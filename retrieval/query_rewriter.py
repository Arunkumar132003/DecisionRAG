from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from config import CHAT_MODEL

class QueryRewriter:
    """Converts follow-up questions into standalone questions."""
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0)

        self.prompt = ChatPromptTemplate.from_template("""
You are a query rewriting assistant.

Conversation History:
{history}

Current Question:
{question}

Rewrite the current question into a standalone search query.

Return only the rewritten query.
""")
        self.chain = self.prompt | self.llm

    def rewrite(self, question: str, history: str) -> str:
        """Rewrite follow-up questions using conversation history."""

        if not history:
            return question
        response = self.chain.invoke({"question": question, "history": history})
        return response.content.strip()