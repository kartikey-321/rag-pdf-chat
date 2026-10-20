
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse, RetrievalMode
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny, PointStruct, SparseVector
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

sparse_embedding_model = FastEmbedSparse(
    model_name="Qdrant/bm25"
)

reranker_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

def store_chunks(chunks, doc_id):

    create_hybrid_collection()

    client = QdrantClient(path="./qdrant_data")

    try:
        collection_name = "pdf_documents"

        if not client.collection_exists(collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            )

        for index, chunk in enumerate(chunks):
            chunk.metadata["document_id"] = doc_id
            chunk.metadata["chunk_index"] = index

        # 
        
        vector_store = QdrantVectorStore(
            client=client,
            collection_name="pdf_documents_hybrid",
            embedding=embedding_model,
            sparse_embedding=sparse_embedding_model,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse"
        )

        vector_store.add_documents(chunks)

        print(f"Stored {len(chunks)} chunks in Qdrant")

    finally:
        client.close()



def search_chunks(question: str, doc_id: str | None = None):
    client = QdrantClient(path="./qdrant_data")

    try:
        vector_store = QdrantVectorStore(
            client=client,
            collection_name="pdf_documents_hybrid",
            embedding=embedding_model,
            sparse_embedding=sparse_embedding_model,
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name="dense",
            sparse_vector_name="sparse"
        )

        search_filter = None

        if doc_id:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata.document_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )

        # Step 1: Semantic search (unchanged)
        results = vector_store.similarity_search(
            query=question,
            k=10,
            filter=search_filter
        )

        if not results:
            return []

        results=rerank_chunks(question, results, top_k=3)

        # Step 2: Collect neighboring chunk indices
        neighbors_by_doc = {}

        for doc in results:
            document_id = doc.metadata.get("document_id")
            chunk_index = doc.metadata.get("chunk_index")

            if document_id is None or chunk_index is None:
                continue

            indices = neighbors_by_doc.setdefault(
                document_id, set()
            )

            indices.update([
                chunk_index - 1,
                chunk_index,
                chunk_index + 1
            ])

        
        # Step 3: Fetch missing neighbors in batches
        all_documents = list(results)

        for document_id, indices in neighbors_by_doc.items():

            # Already retrieved chunks
            existing_indices = {
                doc.metadata["chunk_index"]
                for doc in results
                if doc.metadata.get("document_id") == document_id
                and "chunk_index" in doc.metadata
            }

            # Fetch only missing neighboring chunks
            missing_indices = sorted(
                index for index in indices
                if index >= 0 and index not in existing_indices
            )

            if not missing_indices:
                continue

            print(f"Batch fetching chunks: {missing_indices}")
            points, _ = client.scroll(
                collection_name="pdf_documents_hybrid",
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.document_id",
                            match=MatchValue(value=document_id)
                        ),
                        FieldCondition(
                            key="metadata.chunk_index",
                            match=MatchAny(any=missing_indices)
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False,
                limit=len(missing_indices)
            )

            for point in points:
                payload = point.payload or {}

                all_documents.append(
                    Document(
                        page_content=payload.get("page_content", ""),
                        metadata=payload.get("metadata", {})
                    )
                )


        # Step 4: Remove duplicates
        unique_documents = {}

        for doc in all_documents:
            key = (
                doc.metadata.get("document_id"),
                doc.metadata.get("chunk_index")
            )

            unique_documents[key] = doc

        # Step 5: Restore document order
        return sorted(
            unique_documents.values(),
            key=lambda doc: (
                str(doc.metadata.get("document_id", "")),
                doc.metadata.get("chunk_index", 0)
            )
        )

    finally:
        client.close()


def create_hybrid_collection():
    client = QdrantClient(path="./qdrant_data")

    try:
        collection_name = "pdf_documents_hybrid"

        if not client.collection_exists(collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=384,
                        distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams()
                }
            )

        print("Hybrid collection ready!")

    finally:
        client.close()



def migrate_to_hybrid():
    client = QdrantClient(path="./qdrant_data")

    try:
        offset = None
        total = 0

        while True:
            points, offset = client.scroll(
                collection_name="pdf_documents",
                limit=50,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )

            if not points:
                break

            texts = [point.payload["page_content"] for point in points]

            dense_vectors = []

            for point in points:
                text = point.payload["page_content"]

                if point.vector is not None:
                    dense_vector = point.vector
                else:
                    dense_vector = embedding_model.embed_query(text)

            dense_vectors.append(dense_vector)

            # Generate BM25 sparse embeddings for the batch
            sparse_vectors = sparse_embedding_model.embed_documents(texts)

            hybrid_points = []

            for point,dense, sparse in zip(points, dense_vectors, sparse_vectors):
                hybrid_points.append(
                    PointStruct(
                        id=point.id,
                        vector={
                            "dense": dense,
                            "sparse": SparseVector(
                                indices=sparse.indices,
                                values=sparse.values
                            )
                        },
                        payload=point.payload
                    )
                )

            client.upsert(
                collection_name="pdf_documents_hybrid",
                points=hybrid_points
            )

            total += len(hybrid_points)
            print(f"Migrated {total} chunks")

            if offset is None:
                break

        print(f"Migration complete! Total: {total} chunks")

    finally:
        client.close()

def compare_search(question, doc_id):
    client = QdrantClient(path="./qdrant_data")

    try:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.document_id",
                    match=MatchValue(value=doc_id)
                )
            ]
        )

        for mode in [RetrievalMode.DENSE, RetrievalMode.HYBRID]:
            store = QdrantVectorStore(
                client=client,
                collection_name="pdf_documents_hybrid",
                embedding=embedding_model,
                sparse_embedding=sparse_embedding_model,
                retrieval_mode=mode,
                vector_name="dense",
                sparse_vector_name="sparse"
            )

            results = store.similarity_search(
                query=question,
                k=3,
                filter=search_filter
            )

            print(f"\n{mode.value} SEARCH RESULTS")

            for rank, doc in enumerate(results, start=1):
                print(
                    f"Rank {rank} | "
                    f"Chunk {doc.metadata.get('chunk_index')}"
                )
                print("Chunk length:", len(doc.page_content))
                print(doc.page_content)
                print("---")

    finally:
        client.close()

def rerank_chunks(question, chunks, top_k=3):
    pairs = [
        (question, chunk.page_content)
        for chunk in chunks
    ]

    scores = reranker_model.predict(pairs)

    ranked_chunks = sorted(
        zip(chunks, scores),
        key=lambda item: item[1],
        reverse=True
    )

    for chunk, score in ranked_chunks[:3]:
        print(f"Chunk {chunk.metadata.get('chunk_index')} | Score: {score:.2f}")

    return [chunk for chunk, score in ranked_chunks[:top_k]]