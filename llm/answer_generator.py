from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from config import CHAT_MODEL
from llm.prompts import ANSWER_PROMPT
from models.analysis import AnswerAnalysis


class AnswerGenerator:
    """Generates a grounded answer and full analysis in a single LLM call."""

    def __init__(self):
        llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0)
        self.llm = llm.with_structured_output(AnswerAnalysis, method="json_schema")
        self.prompt = ChatPromptTemplate.from_template(ANSWER_PROMPT)
        self.chain = self.prompt | self.llm

    def generate(self, question: str, history: str, context: str) -> AnswerAnalysis:
        """Generate answer, citations, conflict detection and analysis together."""
        return self.chain.invoke({
            "question": question,
            "history": history,
            "context": context,
        })
