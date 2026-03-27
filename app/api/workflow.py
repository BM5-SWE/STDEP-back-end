from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel, Field
from typing import Optional
from app.api.auth import get_current_user
from app.models.user import User
import boto3
import os
import json

router = APIRouter(prefix="/run-workflow", tags=["workflow"])

# Example: You may want to load these from config or env
STEP_FUNCTION_ARN = os.getenv("STEP_FUNCTION_ARN")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

class RunWorkflowRequest(BaseModel):
    platform: str = Field(pattern="^(amazon|aliexpress)$")
    query_text: str = Field(max_length=500)
    query_type: str = Field(pattern="^(category|custom)$")
    # Add any other parameters needed for your workflow

class RunWorkflowResponse(BaseModel):
    execution_arn: str
    status: str

class WorkflowStatusResponse(BaseModel):
    execution_arn: str
    status: str
    output: Optional[dict] = None  # Will contain S3 result key if succeeded

@router.post("", response_model=RunWorkflowResponse)
def run_workflow(
    payload: RunWorkflowRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Trigger the AWS Step Function for a product query.
    Returns the execution ARN and initial status.
    """
    if not STEP_FUNCTION_ARN:
        raise HTTPException(status_code=500, detail="Step Function ARN not configured")

    # Prepare input for Step Function
    input_payload = {
        "user_id": str(current_user.id),
        "platform": payload.platform,
        "query_text": payload.query_text,
        "query_type": payload.query_type,
        # Add more fields as needed
    }

    try:
        client = boto3.client("stepfunctions", region_name=AWS_REGION)
        response = client.start_execution(
            stateMachineArn=STEP_FUNCTION_ARN,
            input=json.dumps(input_payload)
        )
        execution_arn = response["executionArn"]
        status = response.get("status", "RUNNING")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {e}")

    return RunWorkflowResponse(execution_arn=execution_arn, status=status)

@router.get("/status/{execution_arn}", response_model=WorkflowStatusResponse)
def get_workflow_status(
    execution_arn: str = Path(..., description="Step Function execution ARN"),
    current_user: User = Depends(get_current_user),
):
    """
    Poll the status of a Step Function execution.
    Returns status and output (S3 result key) if succeeded.
    """
    try:
        client = boto3.client("stepfunctions", region_name=AWS_REGION)
        response = client.describe_execution(
            executionArn=execution_arn
        )
        status = response["status"]
        output = None
        if status == "SUCCEEDED":
            try:
                output = json.loads(response["output"])
            except Exception:
                output = {"raw": response.get("output")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {e}")

    return WorkflowStatusResponse(
        execution_arn=execution_arn,
        status=status,
        output=output,
    )
