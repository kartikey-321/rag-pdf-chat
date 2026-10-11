
from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def generate_embeddings(chunks):
    texts = [chunk.page_content for chunk in chunks]

    vectors = embedding_model.embed_documents(texts)

    return vectors
