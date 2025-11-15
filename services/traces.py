"""
Sample traces to send to LangSmith to trigger evaluators.

These traces use ChatOpenAI with simple questions and will trigger the webhook
evaluators that have been set up.
"""

from langsmith import traceable
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY


@traceable
def ask_question(question: str) -> str:
    """Ask a question using ChatOpenAI."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=OPENAI_API_KEY
    )
    response = llm.invoke(question)
    return response.content


def send_sample_traces() -> None:
    """Send 3 sample traces to LangSmith to trigger evaluators."""
    questions = [
        "What color is the sky? Keep your answer concise",
        "What is 2+2? Keep your answer concise",
        "What is the capital of France? Keep your answer concise",
    ]
    
    print(f"\nSending {len(questions)} sample traces...")
    
    for i, question in enumerate(questions, 1):
        try:
            print(f"  [{i}/{len(questions)}] Sending trace: {question[:50]}...")
            answer = ask_question(question)
            print(f"    ✓ Trace sent successfully")
        except Exception as e:
            print(f"    ⚠ Failed to send trace: {e}")
    

if __name__ == "__main__":
    send_sample_traces()
