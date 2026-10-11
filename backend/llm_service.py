
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a helpful PDF question-answering assistant.

Answer the user's question using only the provided context.

If the answer is not present in the context,
say: "I couldn't find this information in the document."

Context:
{context}"""
    ),
    ("human", "{question}")
])

def generate_answer(question: str, documents):
    context = "\n\n".join(
        doc.page_content for doc in documents
    )

    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "question": question
    })

    return response.content
