
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue


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

        results = vector_store.similarity_search(
            query=question,
            k=3,
            filter=search_filter
        )

        return results

    finally:
        client.close()


