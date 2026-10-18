
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from langchain_core.documents import Document


embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def store_chunks(chunks, doc_id):
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

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embedding_model
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
            collection_name="pdf_documents",
            embedding=embedding_model
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
            k=3,
            filter=search_filter
        )

        if not results:
            return []

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
                collection_name="pdf_documents",
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



