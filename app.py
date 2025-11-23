"""
EasyExcel Backend API

FastAPI server for processing Excel/CSV files with AI-powered prompts.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request, Header, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import traceback
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from services.file_manager import FileManager
from services.excel_processor import ExcelProcessor
from services.chart_builder import ChartBuilder
from services.llm_agent import LLMAgent
from services.paypal_service import PayPalService
from services.user_service import UserService
from utils.validator import DataValidator

# Initialize FastAPI app
app = FastAPI(
    title="EasyExcel API",
    description="AI-powered Excel/CSV processing service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_manager = FileManager()
validator = DataValidator()
chart_builder = ChartBuilder(output_dir=str(file_manager.charts_dir))
paypal_service = PayPalService()
user_service = UserService()

# Security
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Get current user from API key."""
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required. Please provide your API key in the Authorization header.")
    
    api_key = credentials.credentials
    user = user_service.get_user_by_api_key(api_key)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return user
user_service = UserService()

# Initialize LLM agent with Google Gemini (will raise error if API key not set)
try:
    llm_agent = LLMAgent()
except ValueError as e:
    print(f"Warning: {e}")
    llm_agent = None


# Request/Response models
class HealthResponse(BaseModel):
    status: str
    message: str


class ProcessFileResponse(BaseModel):
    status: str
    processed_file_url: Optional[str] = None
    chart_url: Optional[str] = None
    summary: list
    action_plan: Optional[dict] = None
    message: Optional[str] = None
    processed_data: Optional[List[Dict[str, Any]]] = None  # JSON representation of processed dataframe (list of row dicts)
    columns: Optional[List[str]] = None  # Column names
    row_count: Optional[int] = None  # Number of rows
    # Formula engine response format
    type: Optional[str] = None  # "summary" | "table" | "value" | "chart" | "transformation"
    operation: Optional[str] = None  # Operation name (e.g., "sum", "average", "filter", etc.)
    result: Optional[Any] = None  # Result value, dataset, or chart instruction


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return HealthResponse(status="OK", message="EasyExcel API is running")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(status="OK", message="Service is healthy")


@app.post("/process-file", response_model=ProcessFileResponse)
async def process_file(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    """
    Process uploaded Excel/CSV file based on user prompt
    
    Args:
        file: Uploaded file (Excel or CSV)
        prompt: Natural language prompt describing desired operations
        
    Returns:
        Processed file URL, chart URL (if generated), and summary
    """
    processed_file_path = None
    chart_path = None
    
    try:
        # 1. Validate file
        is_valid, error = validator.validate_file_format(file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        # 2. Save uploaded file
        file_content = await file.read()
        temp_file_path = file_manager.save_uploaded_file(file_content, file.filename)
        
        # 3. Validate file content
        is_valid, error, df = validator.validate_complete_file(temp_file_path, file.filename)
        if not is_valid:
            file_manager.delete_file(temp_file_path)
            raise HTTPException(status_code=400, detail=error)
        
        # 4. Get available columns
        available_columns = list(df.columns)
        
        # 5. Interpret prompt with LLM
        if llm_agent is None:
            raise HTTPException(
                status_code=500, 
                detail="LLM service not available. Please set GEMINI_API_KEY environment variable."
            )
        
        action_plan = llm_agent.interpret_prompt(prompt, available_columns)
        
        # 6. Validate required columns exist
        columns_needed = action_plan.get("columns_needed", [])
        if columns_needed:
            is_valid, error, missing = validator.validate_columns_exist(df, columns_needed)
            if not is_valid:
                file_manager.delete_file(temp_file_path)
                raise HTTPException(status_code=400, detail=error)
        
        # 7. Check subscription and token limits
        # Estimate tokens needed (rough estimate: 100 tokens per row + prompt tokens)
        estimated_tokens = len(df) * 100 + len(prompt) * 2
        token_check = user_service.check_token_limit(user["user_id"], estimated_tokens)
        
        if not token_check.get("can_proceed"):
            file_manager.delete_file(temp_file_path)
            raise HTTPException(
                status_code=403,
                detail=token_check.get("error", "Insufficient tokens. Please upgrade your plan.")
            )
        
        # 7. Process file
        processor = ExcelProcessor(temp_file_path)
        processor.load_data()
        
        # Check if user mentioned cleaning operations in prompt
        cleaning_keywords = ['remove duplicates', 'clean', 'fix formatting', 'handle missing', 'duplicate', 'remove empty', 'normalize']
        prompt_lower = prompt.lower()
        user_wants_cleaning = any(keyword in prompt_lower for keyword in cleaning_keywords)
        
        # Check if user wants visualization
        visualization_keywords = ['visualize', 'dashboard', 'chart', 'graph', 'plot', 'show me']
        user_wants_chart = any(keyword in prompt_lower for keyword in visualization_keywords)
        
        # CRITICAL: If user wants cleaning operations, ALWAYS use "clean" task
        # This ensures the processed sheet shows actual cleaned data, not summary statistics
        original_task = action_plan.get("task", "summarize")
        if user_wants_cleaning:
            # Force task to "clean" to show actual data, not summary statistics
            action_plan["task"] = "clean"
            # If user also wants dashboard/chart, preserve that request
            if user_wants_chart and action_plan.get("chart_type") == "none":
                action_plan["chart_type"] = "bar"
            # Ensure we're working with original data, not summarized data
            # (load_data() already loaded the original, so we're good)
        
        # If user wants visualization but task is summarize (and no cleaning), that's fine
        # But if cleaning is involved, we already set it to "clean" above
        
        result = processor.execute_action_plan(action_plan)
        
        # Double-check: If task ended up as "summarize" but user wanted cleaning, 
        # we need to reload and re-execute with clean task
        final_task = result.get("task", original_task)
        if final_task == "summarize" and user_wants_cleaning:
            # This shouldn't happen if override worked, but just in case:
            processor.load_data()  # Reload original data
            action_plan["task"] = "clean"
            if user_wants_chart and action_plan.get("chart_type") == "none":
                action_plan["chart_type"] = "bar"
            result = processor.execute_action_plan(action_plan)
        
        processed_df = result["df"]
        summary = result["summary"]
        chart_needed = result["chart_needed"]
        chart_type = result["chart_type"]
        formula_result = result.get("formula_result")
        task = result.get("task", "summarize")
        
        # 8. Save processed file
        output_filename = f"processed_{Path(file.filename).stem}.xlsx"
        output_path = file_manager.output_dir / output_filename
        processed_file_path = processor.save_processed_file(str(output_path))
        
        # 9. Generate chart if needed
        # Check if user requested visualization even if LLM didn't set it
        visualization_keywords = ['visualize', 'dashboard', 'chart', 'graph', 'plot', 'show me']
        prompt_lower = prompt.lower()
        user_wants_chart = any(keyword in prompt_lower for keyword in visualization_keywords)
        
        # Initialize chart variables
        chart_path = None
        x_col = None
        y_col = None
        
        # Generate chart if: LLM requested it OR user mentioned visualization
        if (chart_needed and chart_type != "none") or (user_wants_chart and chart_type == "none"):
            # If user wants chart but LLM didn't set type, default to bar chart
            if chart_type == "none" and user_wants_chart:
                chart_type = "bar"
                summary.append("Detected visualization request - generating chart")
            
            try:
                # Auto-detect columns for chart
                x_col, y_col = chart_builder._auto_detect_columns(processed_df, chart_type)
                chart_path = chart_builder.create_chart(
                    processed_df, 
                    chart_type,
                    x_column=x_col,
                    y_column=y_col,
                    title=f"{prompt[:50]}..."
                )
                summary.append(f"Generated {chart_type} chart: {Path(chart_path).name}")
            except Exception as e:
                summary.append(f"Chart generation failed: {str(e)}")
                chart_path = None
        
        # 10. Clean up temp file
        file_manager.delete_file(temp_file_path)
        
        # 11. Prepare response URLs
        processed_file_url = f"/download/{Path(processed_file_path).name}" if processed_file_path else None
        chart_url = f"/download/charts/{Path(chart_path).name}" if chart_path else None
        
        # 12. Convert processed dataframe to JSON for preview
        # Limit to first 1000 rows for preview to avoid large responses
        import pandas as pd
        import numpy as np
        preview_df = processed_df.head(1000) if len(processed_df) > 1000 else processed_df
        # Replace NaN/None values with null for proper JSON serialization
        processed_data = preview_df.replace({np.nan: None, pd.NA: None}).to_dict(orient='records')
        columns = list(processed_df.columns)
        row_count = len(processed_df)
        
        # 13. Determine response type and format for formula engine
        response_type = "table"  # Default
        operation = task
        result_value = None
        
        # Extract formula type if it's a formula operation
        if task == "formula" and action_plan.get("formula"):
            formula_type = action_plan["formula"].get("type", "")
            operation = formula_type if formula_type else task
        
        # If formula was executed and returned a single value
        if formula_result is not None:
            response_type = "value"
            operation = operation if operation != "formula" else action_plan.get("formula", {}).get("type", "formula")
            result_value = formula_result
        # If chart was generated
        elif chart_path:
            response_type = "chart"
            operation = "visualize" if operation == "formula" else operation
            result_value = {
                "chart_type": chart_type,
                "chart_url": chart_url,
                "title": f"{prompt[:50]}...",
                "x_column": x_col,
                "y_column": y_col
            }
        # If task is summarize (only when explicitly requested, not for dashboards)
        # Check if user actually wanted summary or just a dashboard
        if task == "summarize":
            # If user requested dashboard/chart or cleaning, they want the actual data, not summary stats
            if user_wants_chart or chart_path or user_wants_cleaning:
                response_type = "transformation"
                result_value = processed_data
            else:
                response_type = "summary"
                result_value = processed_data
        # If task transforms the data (including clean operations)
        elif task in ["clean", "transform", "filter", "sort", "group_by", "formula"]:
            response_type = "transformation"
            # For formula transformations, use the formula type as operation
            if task == "formula" and action_plan.get("formula"):
                operation = action_plan["formula"].get("type", "formula")
            result_value = processed_data
        # Default: return table
        else:
            result_value = processed_data
        
        # Record token usage
        actual_tokens_used = estimated_tokens  # In production, calculate actual tokens used
        user_service.record_token_usage(user["user_id"], actual_tokens_used, "file_processing")
        
        return ProcessFileResponse(
            status="success",
            processed_file_url=processed_file_url,
            chart_url=chart_url,
            summary=summary,
            action_plan=action_plan,
            message="File processed successfully",
            processed_data=processed_data,
            columns=columns,
            row_count=row_count,
            type=response_type,
            operation=operation,
            result=result_value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if processed_file_path and Path(processed_file_path).exists():
            file_manager.delete_file(processed_file_path)
        if chart_path and Path(chart_path).exists():
            file_manager.delete_file(chart_path)
        
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(f"Error processing file: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download processed file
    
    Args:
        filename: Name of file to download
        
    Returns:
        File download response
    """
    file_path = file_manager.output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/download/charts/{filename}")
async def download_chart(filename: str):
    """
    Download chart image
    
    Args:
        filename: Name of chart file to download
        
    Returns:
        Chart image download response
    """
    file_path = file_manager.charts_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Chart not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="image/png"
    )


# User and Payment Models
class CreateUserRequest(BaseModel):
    email: str
    plan: str = "Free"

class CreateSubscriptionRequest(BaseModel):
    plan_name: str
    user_email: str
    user_id: Optional[str] = None


class WebhookEvent(BaseModel):
    event_type: str
    resource: Dict[str, Any]


# User Management Endpoints
@app.post("/api/users/register")
async def register_user(request: CreateUserRequest):
    """
    Register a new user and get API key.
    
    Args:
        request: User registration with email and plan
        
    Returns:
        User data with API key
    """
    try:
        user = user_service.create_user(request.email, request.plan)
        return JSONResponse(content={
            "status": "success",
            "user": user
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@app.get("/api/users/me")
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user information.
    
    Returns:
        User data with subscription info
    """
    return JSONResponse(content={
        "status": "success",
        "user": user
    })


# PayPal Payment Endpoints
@app.post("/api/payments/create-subscription")
async def create_subscription(request: CreateSubscriptionRequest):
    """
    Create a PayPal subscription for a user.
    
    Args:
        request: Subscription request with plan_name, user_email, and optional user_id
        
    Returns:
        Subscription details with approval URL
    """
    try:
        if request.plan_name == "Free":
            return JSONResponse(
                status_code=400,
                content={"error": "Free plan does not require payment"}
            )
        
        # Create or get user
        user = user_service.create_user(request.user_email, "Free")  # Start with Free, upgrade after payment
        user_id = request.user_id or user["user_id"]
        
        result = paypal_service.create_subscription(
            plan_name=request.plan_name,
            user_email=request.user_email,
            user_id=user_id
        )
        
        return JSONResponse(content={
            "status": "success",
            "subscription_id": result["subscription_id"],
            "approval_url": result["approval_url"],
            "plan_name": result["plan_name"]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")


@app.get("/api/payments/subscription/{subscription_id}")
async def get_subscription(subscription_id: str):
    """
    Get subscription details.
    
    Args:
        subscription_id: PayPal subscription ID
        
    Returns:
        Subscription details
    """
    try:
        details = paypal_service.get_subscription_details(subscription_id)
        return JSONResponse(content={
            "status": "success",
            "subscription": details
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscription: {str(e)}")


@app.post("/api/payments/cancel-subscription/{subscription_id}")
async def cancel_subscription(subscription_id: str, reason: str = "User requested cancellation"):
    """
    Cancel a PayPal subscription.
    
    Args:
        subscription_id: PayPal subscription ID
        reason: Reason for cancellation
        
    Returns:
        Cancellation status
    """
    try:
        success = paypal_service.cancel_subscription(subscription_id, reason)
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": "Subscription cancelled successfully"
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel subscription")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel subscription: {str(e)}")


@app.post("/api/payments/webhook")
async def paypal_webhook(request: Request):
    """
    Handle PayPal webhook events.
    
    This endpoint receives webhook notifications from PayPal about subscription events.
    """
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Verify webhook
        if not paypal_service.verify_webhook(headers, body.decode()):
            raise HTTPException(status_code=401, detail="Webhook verification failed")
        
        # Parse webhook event
        import json
        event_data = json.loads(body)
        event_type = event_data.get("event_type")
        resource = event_data.get("resource", {})
        
        # Handle different event types
        subscription_id = resource.get("id")
        subscriber = resource.get("subscriber", {})
        email = subscriber.get("email_address")
        plan_id = resource.get("plan_id", "")
        
        # Map PayPal plan ID to our plan names
        plan_name = "Starter"  # Default
        if "pro" in plan_id.lower() or "12" in plan_id:
            plan_name = "Pro"
        elif "starter" in plan_id.lower() or "4.99" in plan_id:
            plan_name = "Starter"
        
        if event_type == "BILLING.SUBSCRIPTION.CREATED":
            # Subscription created - find user by email and update
            if email:
                # Get or create user
                user = user_service.create_user(email, plan_name)
                user_service.update_subscription(user["user_id"], subscription_id, plan_name, "created")
        elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
            # Subscription activated
            if email:
                user = user_service.create_user(email, plan_name)
                user_service.update_subscription(user["user_id"], subscription_id, plan_name, "active")
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            # Subscription cancelled
            if email:
                user = user_service.create_user(email, "Free")  # Downgrade to Free
                user_service.update_subscription(user["user_id"], subscription_id, "Free", "cancelled")
        elif event_type == "PAYMENT.SALE.COMPLETED":
            # Payment completed - subscription is active
            if email:
                user = user_service.create_user(email, plan_name)
                user_service.update_subscription(user["user_id"], subscription_id, plan_name, "active")
        
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.post("/cleanup")
async def cleanup_old_files():
    """Clean up old files"""
    deleted_count = file_manager.clean_old_files(days=7)
    return {"status": "success", "files_deleted": deleted_count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

