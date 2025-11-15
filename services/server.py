import json
import traceback
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Body
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import client, OPENAI_API_KEY, parse_judge_model


def configure_llm(model_string: str = "openai:gpt-4o-mini", output_schema: BaseModel | None = None):
    """Configure the LLM for the judge."""
    judge_provider, judge_model_name = parse_judge_model(model_string)
    if judge_provider != "openai":
        raise ValueError(f"Unsupported provider '{judge_provider}'. Only 'openai' is supported.")
       
    llm = ChatOpenAI(
        model=judge_model_name,
        temperature=0,
        api_key=OPENAI_API_KEY
    )
    if output_schema:
        llm = llm.with_structured_output(output_schema)
    return llm


# --- Pydantic Models ---
class Run(BaseModel):
    """Represents a single run in the webhook payload."""
    id: str
    trace_id: str
    name: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    run_type: str
    status: str
    error: Optional[str] = None

class WebhookPayload(BaseModel):
    """LangSmith webhook payload structure."""
    rule_id: str
    start_time: str
    end_time: str
    runs: List[Run]

# --- Judge Evaluation ---
correctness_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert evaluator judging the correctness of LLM application runs.
    
Evaluate the run based on the following criteria:
- Correctness: Does the output correctly address the input?
- Completeness: Is the output complete and comprehensive?
- Quality: Is the output well-formed and appropriate?

Make sure to explain your reasoning
"""),
    ("human", """Evaluate this run:

Inputs:
{inputs}

Outputs:
{outputs}
""")
])

class Correctness(BaseModel):
    """Represents the correctness of a run."""
    score: bool = Field(description="Whether the output is correct according to the criteria.")
    comment: str = Field(description="A brief explanation of your score.")

# --- Evaluate Run ---
async def evaluate_run(run: Run) -> Dict[str, Any]:
    """Run LLM judge evaluation on a single run using structured output."""
    try:
        # Format inputs and outputs for the judge
        inputs_str = json.dumps(run.inputs, indent=2) if run.inputs else "No inputs"
        outputs_str = json.dumps(run.outputs, indent=2) if run.outputs else "No outputs"
        
        # Get judge evaluation with structured output
        prompt = correctness_prompt.format_messages(
            inputs=inputs_str,
            outputs=outputs_str
        )
        
        llm = configure_llm(output_schema=Correctness)
        evaluation: Correctness = await llm.ainvoke(prompt)
        
        # Convert boolean score to float (0.0 or 1.0) for LangSmith feedback API
        score = 1.0 if evaluation.score else 0.0
        
        return {
            "score": score,
            "comment": evaluation.comment
        }
    except Exception as e:
        print(f"Error evaluating run {run.id}: {e}")
        traceback.print_exc()
        return {
            "score": 0.5,
            "comment": f"Evaluation error: {str(e)}"
        }

async def process_webhook(payload: WebhookPayload) -> Dict[str, Any]:
    """Process webhook payload: evaluate runs and post feedback."""
    results = []
    
    for run in payload.runs:
        # Skip failed runs
        if run.status != "success" or run.error:
            print(f"Skipping run {run.id} - status: {run.status}, error: {run.error}")
            continue
        
        # Evaluate the run
        evaluation = await evaluate_run(run)
        
        # Post feedback to LangSmith
        try:
            client.create_feedback(
                key="judge_evaluation",
                score=evaluation["score"],
                trace_id=run.trace_id,
                run_id=run.id,
                comment=evaluation["comment"]
            )
            results.append({
                "run_id": run.id,
                "trace_id": run.trace_id,
                "score": evaluation["score"],
                "status": "success"
            })
            print(f"Posted feedback for run {run.id}: score={evaluation['score']}")
        except Exception as e:
            print(f"Error posting feedback for run {run.id}: {e}")
            results.append({
                "run_id": run.id,
                "trace_id": run.trace_id,
                "error": str(e),
                "status": "error"
            })
    
    return {
        "processed": len(results),
        "results": results
    }

# --- FastAPI Application ---
app = FastAPI(
    title="LangSmith Webhook Judge Service",
    description="Receives LangSmith webhooks, evaluates runs with an LLM judge, and posts feedback.",
    version="0.1.0",
)

@app.post("/webhook", status_code=200, tags=["Webhooks"])
async def handle_webhook(payload: WebhookPayload = Body(...)):
    """
    Webhook endpoint to receive LangSmith run notifications.
    Evaluates each run with an LLM judge and posts feedback.
    """
    try:
        result = await process_webhook(payload)
        return {
            "message": "Webhook processed successfully",
            "rule_id": payload.rule_id,
            **result
        }
    except Exception as e:
        error_message = f"Error processing webhook: {str(e)}"
        print(f"[ERROR] {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

@app.get("/health", status_code=200, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Service is running",
    }

# To run this server:
# 2. Run with: uvicorn server:app --host 0.0.0.0 --port 8000
# 3. Deploy to Render.com and use the URL in your webhook configuration
