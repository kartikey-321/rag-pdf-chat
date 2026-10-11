from doc_parser import load_pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

from embedding_service import generate_embeddings

from vector_store import store_chunks

def process_doc(doc_id):

    documents = load_pdf(f"uploads/{doc_id}.pdf")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    # print("Total pages:", len(documents))
    # print("Total chunks:", len(chunks))

    # if chunks:
    #     for i in range(len(chunks)):
    #         print("chunk: ", i+1, chunks[i].page_content)
    #         print("Metadata:", chunks[i].metadata)

        # print("First chunk:", chunks[0].page_content)
        # print("Metadata:", chunks[0].metadata)

    # vectors=generate_embeddings(chunks)

    # print("Total chunks:", len(chunks))
    # print("Total vectors:", len(vectors))
    # print("First vector dimensions:", len(vectors[0]))
    # print("First vector:", vectors[0])

    store_chunks(chunks, doc_id)

    # results = vector_store.similarity_search(
    #     query="Why we need DBMS?",
    #     k=3
    # )

    # for result in results:
    #     print(result.page_content)
        
    # return vectors


    # print("Total documents:", len(documents))
    # print("First page text:", documents[0].page_content[:500])
    # print("Metadata:", documents[0].metadata)