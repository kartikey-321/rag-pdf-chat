from vector_store import search_chunks
from llm_service import generate_answer

question = "Why do we need DBMS?"

documents = search_chunks(question)

answer = generate_answer(question, documents)

print("AI Answer:", answer[0]["text"])