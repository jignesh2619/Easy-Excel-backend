"""
LazyExcel Backend API

FastAPI server for processing Excel/CSV files with AI-powered prompts.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request, Header, Depends
from fastapi.responses import JSONResponse, FileResponse
# CORS is handled by nginx - no FastAPI CORS middleware needed
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import traceback
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This ensures logs go to stdout/stderr
    ]
)

logger = logging.getLogger(__name__)

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
from services.sample_selector import SampleSelector
from services.file_knowledge_base import FileKnowledgeBase

# Initialize FastAPI app
app = FastAPI(
    title="LazyExcel API",
    description="AI-powered Excel/CSV processing service",
    version="1.0.0"
)

# CORS is handled by nginx - no need for FastAPI CORS middleware
# This prevents duplicate CORS headers which browsers reject

# Initialize services
file_manager = FileManager()
validator = DataValidator()
chart_builder = ChartBuilder(output_dir=str(file_manager.charts_dir))
paypal_service = PayPalService()
user_service = UserService()
sample_selector = SampleSelector()
file_kb = FileKnowledgeBase(metadata_file="file_metadata.json")  # Persistent file knowledge base

# Automatic metadata cleanup on startup (delete all metadata older than 1 day)
try:
    cleanup_stats = file_kb.cleanup_all(days=1, check_missing_files=True, base_path=str(file_manager.temp_dir))
    if cleanup_stats["total_deleted"] > 0:
        logger.info(f"Startup cleanup: Removed {cleanup_stats['total_deleted']} expired/missing metadata entries")
except Exception as e:
    logger.warning(f"Startup metadata cleanup failed (non-critical): {e}")

# Security
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Get current user from Supabase Auth token or API key.
    Supports both Supabase Auth tokens and legacy API keys.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required. Please provide your access token in the Authorization header.")
    
    token = credentials.credentials
    
    # Try Supabase Auth token first (format: Bearer <token>)
    try:
        from services.supabase_client import SupabaseClient
        supabase = SupabaseClient.get_client()
        
        # Verify token and get user
        user_info = supabase.auth.get_user(token)
        
        if user_info and user_info.user:
            # Get user from our database
            user = user_service.get_user_by_supabase_id(user_info.user.id)
            if user:
                return user
    except Exception:
        # If Supabase auth fails, try API key (legacy support)
        pass
    
    # Fallback to API key authentication (legacy)
    user = user_service.get_user_by_api_key(token)
    if user:
        return user
    
    raise HTTPException(status_code=401, detail="Invalid authentication token")

# Initialize LLM agent with OpenAI GPT-4.1 (will raise error if API key not set)
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
    formatting_metadata: Optional[Dict[str, Any]] = None  # Formatting metadata for preview display
    # Formula engine response format
    type: Optional[str] = None  # "summary" | "table" | "value" | "chart" | "transformation"
    operation: Optional[str] = None  # Operation name (e.g., "sum", "average", "filter", etc.)
    result: Optional[Any] = None  # Result value, dataset, or chart instruction
    trace_report: Optional[Dict[str, Any]] = None  # Data traceability report


class ProcessDataRequest(BaseModel):
    data: List[Dict[str, Any]]  # JSON data (list of row objects)
    columns: List[str]  # Column names
    prompt: str  # User prompt for processing
    row_count: Optional[int] = None  # Total number of rows (if data is a preview/sample)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return HealthResponse(status="OK", message="EasyExcel API is running")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(status="OK", message="Service is healthy")


# OPTIONS requests are handled by nginx - no need for FastAPI handler
# This prevents duplicate CORS headers


@app.post("/process-file", response_model=ProcessFileResponse)
async def process_file(
    file: UploadFile = File(...),
    prompt: str = Form(default=""),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Process uploaded Excel/CSV file based on user prompt
    
    Args:
        file: Uploaded file (Excel or CSV)
        prompt: Natural language prompt describing desired operations (optional - if empty, just load file)
        
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
        
        # 2. Save uploaded file (streaming for better performance)
        try:
            # Use streaming to avoid loading entire file into memory
            temp_file_path = await file_manager.save_uploaded_file_streaming(file, file.filename)
        except Exception as e:
            logger.error(f"Error saving uploaded file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to save uploaded file: {str(e)}")
        
        # 3. Validate file content
        try:
            is_valid, error, df = validator.validate_complete_file(temp_file_path, file.filename)
            if not is_valid:
                file_manager.delete_file(temp_file_path)
                logger.error(f"File validation failed: {error}")
                raise HTTPException(status_code=400, detail=error)
        except HTTPException:
            raise
        except Exception as e:
            file_manager.delete_file(temp_file_path)
            logger.error(f"Error validating file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}. Please ensure the file is not corrupted.")
        
        # 4. Get available columns
        available_columns = list(df.columns)
        
        # 4a. Index file in knowledge base (for faster future access)
        try:
            file_metadata = file_kb.index_file(temp_file_path, df)
            logger.info(f"File indexed in knowledge base: {file_metadata.get('file_name')}")
        except Exception as e:
            logger.warning(f"Failed to index file in knowledge base: {e}")
            # Continue without indexing - not critical
        
        # 5. Get user authentication before processing
        user = None
        if credentials and credentials.credentials:
            token = credentials.credentials
            # Try Supabase Auth token first (same logic as get_current_user)
            try:
                from services.supabase_client import SupabaseClient
                supabase = SupabaseClient.get_client()
                user_info = supabase.auth.get_user(token)
                if user_info and user_info.user:
                    user = user_service.get_user_by_supabase_id(user_info.user.id)
            except Exception:
                # If Supabase auth fails, try API key (legacy support)
                user = user_service.get_user_by_api_key(token)
        
        # 6. Prepare representative sample data for LLM context
        sample_data = None
        sample_explanation = ""
        data_size_estimate = 0
        if len(df) > 0:
            sample_result = sample_selector.build_sample(df)
            sample_df = sample_result.dataframe
            sample_explanation = sample_result.explanation
            sample_data = sample_df.to_dict("records")
            
            import json
            data_json = json.dumps(sample_data)
            data_size_estimate = len(data_json) // 4
            logger.info(
                "✅ Sample prepared for LLM: %s rows selected from %s total, explanation: %s",
                len(sample_df),
                len(df),
                sample_explanation
            )
        
        # 7. Check token limits before LLM call (account for full Excel data)
        # Estimate includes: user prompt + system prompt + Excel data + response
        prompt_tokens_estimate = len(prompt) // 4
        system_prompt_estimate = 2000  # System prompt is large with all instructions
        excel_data_tokens = data_size_estimate
        response_tokens_estimate = 500  # Conservative estimate for JSON response
        estimated_tokens = prompt_tokens_estimate + system_prompt_estimate + excel_data_tokens + response_tokens_estimate
        
        logger.info(f"Token estimate breakdown: prompt={prompt_tokens_estimate}, system={system_prompt_estimate}, data={excel_data_tokens}, response={response_tokens_estimate}, total={estimated_tokens}")
        
        if user:
            token_check = user_service.check_token_limit(user["user_id"], estimated_tokens)
            if not token_check.get("can_proceed"):
                file_manager.delete_file(temp_file_path)
                raise HTTPException(
                    status_code=403,
                    detail=token_check.get("error", "Insufficient tokens. Please upgrade your plan.")
                )
        
        # 8. Interpret prompt with LLM (only if prompt is provided)
        # If prompt is empty or just whitespace, skip processing and return file as-is
        prompt = prompt.strip() if prompt else ""
        
        if not prompt:
            # No prompt provided - just load and return file without any processing
            logger.info("No prompt provided - returning file as-is without processing")
            processor = ExcelProcessor(temp_file_path)
            processor.load_data()
            
            # Save unprocessed file using processor's save method
            output_filename = f"processed_{Path(file.filename).stem}.xlsx"
            output_path = file_manager.output_dir / output_filename
            processed_file_path = processor.save_processed_file(str(output_path))
            
            return ProcessFileResponse(
                file_url=f"/download/{Path(processed_file_path).name}",
                chart_url=None,
                summary=["File loaded successfully. No processing performed."],
                rows=len(processor.df),
                columns=len(processor.df.columns),
                formatting_metadata={}
            )
        
        if llm_agent is None:
            raise HTTPException(
                status_code=500, 
                detail="LLM service not available. Please set OPENAI_API_KEY environment variable."
            )
        
        # Get user_id for feedback tracking
        user_id = user["user_id"] if user else None
        
        llm_result = llm_agent.interpret_prompt(
            prompt,
            available_columns,
            user_id=user_id,
            sample_data=sample_data,
            sample_explanation=sample_explanation,
            df=df  # Pass DataFrame for chart analysis
        )
        action_plan = llm_result.get("action_plan", {})
        # Add user prompt to action plan so processors can check what user explicitly requested
        action_plan["user_prompt"] = prompt
        
        # Get actual token usage from OpenAI API (includes prompt + data + response)
        actual_tokens_used = llm_result.get("tokens_used", estimated_tokens)
        
        # Log actual vs estimated for monitoring
        if actual_tokens_used != estimated_tokens:
            logger.info(f"Token usage: estimated={estimated_tokens}, actual={actual_tokens_used}, difference={actual_tokens_used - estimated_tokens}")
        else:
            logger.info(f"Token usage: {actual_tokens_used} tokens (used estimate as fallback)")
        
        # 8. Validate required columns exist
        columns_needed = action_plan.get("columns_needed", [])
        if columns_needed:
            is_valid, error, missing = validator.validate_columns_exist(df, columns_needed)
            if not is_valid:
                file_manager.delete_file(temp_file_path)
                raise HTTPException(status_code=400, detail=error)
        
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
        chart_path = result.get("chart_path")  # Chart path from ChartExecutor
        chart_needed = result.get("chart_needed", False)
        chart_type = result.get("chart_type", "none")
        formula_result = result.get("formula_result")
        task = result.get("task", "summarize")
        trace_report = result.get("trace_report", {})  # Get trace report from processor result
        
        # 8. Save processed file
        output_filename = f"processed_{Path(file.filename).stem}.xlsx"
        output_path = file_manager.output_dir / output_filename
        processed_file_path = processor.save_processed_file(str(output_path))
        
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
        
        # 12a. Get formatting metadata for preview display
        formatting_metadata = processor.get_formatting_metadata(preview_df)
        logger.info(f"📊 Formatting metadata generated: {len(formatting_metadata.get('cell_formats', {}))} cells with formatting")
        
        # 12b. Add formatting info directly to each cell in processed_data for easier frontend rendering
        if formatting_metadata.get("cell_formats"):
            for row_idx, row_data in enumerate(processed_data):
                for col_name in columns:
                    cell_key = f"{row_idx}_{col_name}"
                    if cell_key in formatting_metadata["cell_formats"]:
                        cell_format = formatting_metadata["cell_formats"][cell_key]
                        # Add _format suffix to avoid conflicts with actual data
                        row_data[f"{col_name}_format"] = cell_format
        
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
            
            # Extract chart columns from action_plan
            x_col = None
            y_col = None
            chart_config = action_plan.get("chart_config")
            if chart_config:
                x_col = chart_config.get("x_column")
                y_col = chart_config.get("y_column")
            elif "chart_configs" in action_plan and action_plan["chart_configs"]:
                # Multiple charts - use first one
                first_chart = action_plan["chart_configs"][0]
                x_col = first_chart.get("x_column")
                y_col = first_chart.get("y_column")
            
            # Get chart type - handle dashboard case
            display_chart_type = chart_type if chart_type != "none" else "dashboard"
            
            result_value = {
                "chart_type": display_chart_type,
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
        
        # Record token usage if we have an authenticated user (use actual tokens from LLM API)
        if user:
            user_service.record_token_usage(user["user_id"], actual_tokens_used, "file_processing")
        
        # Record successful execution for feedback learning
        if llm_agent.feedback_learner:
            try:
                execution_result = {
                    "status": "success",
                    "task": task,
                    "rows_processed": row_count,
                    "chart_generated": chart_path is not None
                }
                llm_agent.feedback_learner.record_success(
                    user_prompt=prompt,
                    action_plan=action_plan,
                    execution_result=execution_result,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to record feedback: {e}")
        
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
            formatting_metadata=formatting_metadata,
            type=response_type,
            operation=operation,
            result=result_value,
            trace_report=trace_report
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
        
        # Record failed execution for feedback learning
        if llm_agent and llm_agent.feedback_learner:
            try:
                user_id = user["user_id"] if user else None
                # Try to get action_plan if it was created before error
                action_plan = locals().get("action_plan", {})
                llm_agent.feedback_learner.record_failure(
                    user_prompt=prompt,
                    action_plan=action_plan,
                    error=str(e),
                    user_id=user_id
                )
            except Exception as feedback_error:
                logger.warning(f"Failed to record failure feedback: {feedback_error}")
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/process-data", response_model=ProcessFileResponse)
async def process_data(
    request: ProcessDataRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Process JSON data directly (for chatbot/iterative processing)
    
    Args:
        request: ProcessDataRequest with data, columns, and prompt
        credentials: Optional authentication token
        
    Returns:
        Processed data response with updated data
    """
    processed_file_path = None
    chart_path = None
    
    try:
        # 1. Convert JSON data to DataFrame
        import pandas as pd
        import numpy as np
        import tempfile
        from pathlib import Path
        
        df = pd.DataFrame(request.data)
        
        # Check if frontend is sending limited data (preview only)
        # If row_count is provided and larger than data length, log a warning
        if hasattr(request, 'row_count') and request.row_count and request.row_count > len(df):
            logger.warning(
                f"⚠️ Frontend sent only {len(df)} rows but row_count={request.row_count}. "
                f"Processing will only affect the {len(df)} rows sent. "
                f"Frontend should send all {request.row_count} rows for full processing."
            )
        
        # Ensure columns match
        if set(df.columns) != set(request.columns):
            # Reorder columns to match request
            df = df[request.columns]
        
        # 2. Get user authentication (optional for chatbot)
        user = None
        user_id = None
        if credentials and credentials.credentials:
            token = credentials.credentials
            try:
                from services.supabase_client import SupabaseClient
                supabase = SupabaseClient.get_client()
                user_info = supabase.auth.get_user(token)
                if user_info and user_info.user:
                    user = user_service.get_user_by_supabase_id(user_info.user.id)
            except Exception:
                user = user_service.get_user_by_api_key(token)
        
        # Authentication is optional for chatbot - proceed without user if not authenticated
        
        # 3. Save DataFrame to temporary file for processing
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                temp_file_path = f.name
        except Exception as e:
            logger.error(f"Error creating temp file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create temporary file: {str(e)}")
        
        # 4. Prepare sample data for LLM
        available_columns = list(df.columns)
        sample_data = None
        sample_explanation = ""
        data_size_estimate = 0
        if len(df) > 0:
            sample_result = sample_selector.build_sample(df)
            sample_df = sample_result.dataframe
            sample_explanation = sample_result.explanation
            sample_data = sample_df.to_dict("records")
            
            import json
            data_json = json.dumps(sample_data)
            data_size_estimate = len(data_json) // 4
            logger.info(
                "✅ Sample prepared for LLM: %s rows selected from %s total, explanation: %s",
                len(sample_df),
                len(df),
                sample_explanation
            )
        
        # 5. Check token limits (only if user is authenticated)
        prompt_tokens_estimate = len(request.prompt) // 4
        system_prompt_estimate = 2000
        excel_data_tokens = data_size_estimate
        response_tokens_estimate = 500
        estimated_tokens = prompt_tokens_estimate + system_prompt_estimate + excel_data_tokens + response_tokens_estimate
        
        if user:
            token_check = user_service.check_token_limit(user["user_id"], estimated_tokens)
            if not token_check.get("can_proceed"):
                if temp_file_path and Path(temp_file_path).exists():
                    file_manager.delete_file(temp_file_path)
                raise HTTPException(
                    status_code=403,
                    detail=token_check.get("error", "Insufficient tokens. Please upgrade your plan.")
                )
        
        # 6. Interpret prompt with LLM
        if llm_agent is None:
            if temp_file_path and Path(temp_file_path).exists():
                file_manager.delete_file(temp_file_path)
            raise HTTPException(
                status_code=500, 
                detail="LLM service not available. Please set OPENAI_API_KEY environment variable."
            )
        
        if user:
            user_id = user["user_id"]
        
        llm_result = llm_agent.interpret_prompt(
            request.prompt,
            available_columns,
            user_id=user_id,
            sample_data=sample_data,
            sample_explanation=sample_explanation,
            df=df
        )
        action_plan = llm_result.get("action_plan", {})
        action_plan["user_prompt"] = request.prompt
        
        actual_tokens_used = llm_result.get("tokens_used", estimated_tokens)
        
        # 7. Validate required columns
        columns_needed = action_plan.get("columns_needed", [])
        if columns_needed:
            is_valid, error, missing = validator.validate_columns_exist(df, columns_needed)
            if not is_valid:
                if temp_file_path and Path(temp_file_path).exists():
                    file_manager.delete_file(temp_file_path)
                raise HTTPException(status_code=400, detail=error)
        
        # 8. Process data
        processor = ExcelProcessor(temp_file_path)
        processor.load_data()
        
        # Check for cleaning operations
        cleaning_keywords = ['remove duplicates', 'clean', 'fix formatting', 'handle missing', 'duplicate', 'remove empty', 'normalize']
        prompt_lower = request.prompt.lower()
        user_wants_cleaning = any(keyword in prompt_lower for keyword in cleaning_keywords)
        
        visualization_keywords = ['visualize', 'dashboard', 'chart', 'graph', 'plot', 'show me']
        user_wants_chart = any(keyword in prompt_lower for keyword in visualization_keywords)
        
        original_task = action_plan.get("task", "summarize")
        if user_wants_cleaning:
            action_plan["task"] = "clean"
            if user_wants_chart and action_plan.get("chart_type") == "none":
                action_plan["chart_type"] = "bar"
        
        result = processor.execute_action_plan(action_plan)
        
        final_task = result.get("task", original_task)
        if final_task == "summarize" and user_wants_cleaning:
            processor.load_data()
            action_plan["task"] = "clean"
            if user_wants_chart and action_plan.get("chart_type") == "none":
                action_plan["chart_type"] = "bar"
            result = processor.execute_action_plan(action_plan)
        
        processed_df = result["df"]
        summary = result["summary"]
        chart_path = result.get("chart_path")
        chart_needed = result.get("chart_needed", False)
        chart_type = result.get("chart_type", "none")
        formula_result = result.get("formula_result")
        task = result.get("task", "summarize")
        trace_report = result.get("trace_report", {})  # Get trace report from processor result
        
        # 9. Save processed file
        output_filename = f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = file_manager.output_dir / output_filename
        processed_file_path = processor.save_processed_file(str(output_path))
        
        # 10. Clean up temp file
        if temp_file_path and Path(temp_file_path).exists():
            file_manager.delete_file(temp_file_path)
        
        # 11. Prepare response URLs
        processed_file_url = f"/download/{Path(processed_file_path).name}" if processed_file_path else None
        chart_url = f"/download/charts/{Path(chart_path).name}" if chart_path else None
        
        # 12. Convert processed dataframe to JSON for preview
        preview_df = processed_df.head(1000) if len(processed_df) > 1000 else processed_df
        processed_data = preview_df.replace({np.nan: None, pd.NA: None}).to_dict(orient='records')
        columns = list(processed_df.columns)
        row_count = len(processed_df)
        
        # Debug: Log sample data from processed_data
        if processed_data and len(processed_data) > 0:
            sample_row = processed_data[0]
            logger.info(f"🔍 Sample row from processed_data: {sample_row}")
            if 'Student Name' in columns:
                student_names = [row.get('Student Name') for row in processed_data[:5]]
                logger.info(f"🔍 First 5 Student Name values: {student_names}")
            if 'Contact No.' in columns:
                contacts = [row.get('Contact No.') for row in processed_data[:5]]
                logger.info(f"🔍 First 5 Contact No. values: {contacts}")
        
        # 13. Get formatting metadata
        formatting_metadata = processor.get_formatting_metadata(preview_df)
        logger.info(f"📊 Formatting metadata generated: {len(formatting_metadata.get('cell_formats', {}))} cells with formatting")
        
        # 14. Add formatting info to each cell
        if formatting_metadata.get("cell_formats"):
            for row_idx, row_data in enumerate(processed_data):
                for col_name in columns:
                    cell_key = f"{row_idx}_{col_name}"
                    if cell_key in formatting_metadata["cell_formats"]:
                        cell_format = formatting_metadata["cell_formats"][cell_key]
                        row_data[f"{col_name}_format"] = cell_format
        
        # 15. Determine response type
        response_type = "table"
        operation = task
        result_value = None
        
        if task == "formula" and action_plan.get("formula"):
            formula_type = action_plan["formula"].get("type", "")
            operation = formula_type if formula_type else task
        
        if formula_result is not None:
            response_type = "value"
            operation = operation if operation != "formula" else action_plan.get("formula", {}).get("type", "formula")
            result_value = formula_result
        elif chart_path:
            response_type = "chart"
            operation = "visualize" if operation == "formula" else operation
            
            x_col = None
            y_col = None
            chart_config = action_plan.get("chart_config")
            if chart_config:
                x_col = chart_config.get("x_column")
                y_col = chart_config.get("y_column")
            elif "chart_configs" in action_plan and action_plan["chart_configs"]:
                first_chart = action_plan["chart_configs"][0]
                x_col = first_chart.get("x_column")
                y_col = first_chart.get("y_column")
            
            display_chart_type = chart_type if chart_type != "none" else "dashboard"
            
            result_value = {
                "chart_type": display_chart_type,
                "chart_url": chart_url,
                "title": f"{request.prompt[:50]}...",
                "x_column": x_col,
                "y_column": y_col
            }
        
        if task == "summarize":
            if user_wants_chart or chart_path or user_wants_cleaning:
                response_type = "transformation"
                result_value = processed_data
            else:
                response_type = "summary"
                result_value = processed_data
        elif task in ["clean", "transform", "filter", "sort", "group_by", "formula"]:
            response_type = "transformation"
            if task == "formula" and action_plan.get("formula"):
                operation = action_plan["formula"].get("type", "formula")
            result_value = processed_data
        else:
            result_value = processed_data
        
        # 16. Record token usage (only if user is authenticated)
        if user:
            user_service.record_token_usage(user["user_id"], actual_tokens_used, "data_processing")
        
        # 17. Record feedback (only if user is authenticated)
        if user and llm_agent.feedback_learner:
            try:
                execution_result = {
                    "status": "success",
                    "task": task,
                    "rows_processed": row_count,
                    "chart_generated": chart_path is not None
                }
                llm_agent.feedback_learner.record_success(
                    user_prompt=request.prompt,
                    action_plan=action_plan,
                    execution_result=execution_result,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to record feedback: {e}")
        
        # Log response details for debugging
        logger.info(f"📤 Sending response: {len(processed_data)} rows, {len(columns)} columns, row_count={row_count}")
        logger.info(f"📤 Response includes processed_data: {processed_data is not None}, length: {len(processed_data) if processed_data else 0}")
        
        return ProcessFileResponse(
            status="success",
            processed_file_url=processed_file_url,
            chart_url=chart_url,
            summary=summary,
            action_plan=action_plan,
            message="Data processed successfully",
            processed_data=processed_data,
            columns=columns,
            row_count=row_count,
            formatting_metadata=formatting_metadata,
            type=response_type,
            operation=operation,
            trace_report=trace_report,
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
        logger.error(f"Error processing data: {error_detail}")
        
        # Record failed execution (only if user is authenticated)
        if user and llm_agent and llm_agent.feedback_learner:
            try:
                user_id = user["user_id"] if user else None
                action_plan = locals().get("action_plan", {})
                llm_agent.feedback_learner.record_failure(
                    user_prompt=request.prompt,
                    action_plan=action_plan,
                    error=str(e),
                    user_id=user_id
                )
            except Exception as feedback_error:
                logger.warning(f"Failed to record failure feedback: {feedback_error}")
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/download/{filename}")
async def download_file(
    filename: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download processed file (requires authentication)
    
    Args:
        filename: Name of file to download
        user: Authenticated user (from token)
        
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
async def download_chart(
    filename: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download chart image (requires authentication)
    
    Args:
        filename: Name of chart file to download
        user: Authenticated user (from token)
        
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

class LoginRequest(BaseModel):
    email: str

class SupabaseAuthRequest(BaseModel):
    access_token: str  # Supabase Auth access token
    user_id: str  # Supabase Auth user ID
    email: str  # User email from Supabase Auth

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


@app.post("/api/users/login")
async def login_user(request: LoginRequest):
    """
    Login with email (for email/password auth via Supabase).
    If user doesn't exist, creates a new user with Free plan.
    
    Args:
        request: Login request with email
        
    Returns:
        User data
    """
    try:
        # Check if user exists
        user = user_service.get_user_by_email(request.email)
        
        if not user:
            # Create new user with Free plan
            user = user_service.create_user(request.email, "Free")
        
        return JSONResponse(content={
            "status": "success",
            "user": user
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to login: {str(e)}")


@app.post("/api/users/supabase-auth")
async def supabase_auth(request: SupabaseAuthRequest):
    """
    Authenticate with Supabase Auth token.
    Verifies the token and creates/returns user.
    
    Args:
        request: Supabase auth request with access_token, user_id, and email
        
    Returns:
        User data
    """
    try:
        from services.supabase_client import SupabaseClient
        import traceback
        
        # Verify Supabase token by getting user info
        supabase = SupabaseClient.get_client()
        
        # Verify token and get user - use the access token directly
        try:
            user_info = supabase.auth.get_user(request.access_token)
        except Exception as e:
            logger.error(f"Supabase get_user error: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=401, detail=f"Invalid Supabase token: {str(e)}")
        
        if not user_info or not user_info.user:
            raise HTTPException(status_code=401, detail="Invalid Supabase token - no user found")
        
        # Verify the user ID matches
        if user_info.user.id != request.user_id:
            logger.warning(f"User ID mismatch: token user_id={user_info.user.id}, request user_id={request.user_id}")
            # Still proceed, but use the ID from the token (more trustworthy)
            actual_user_id = user_info.user.id
        else:
            actual_user_id = request.user_id
        
        # Get or create user in our database
        user = user_service.get_user_by_supabase_id(actual_user_id)
        
        if not user:
            # Use email from token if available, otherwise use request email
            user_email = user_info.user.email or request.email
            # Create new user with Free plan
            user = user_service.create_user_from_supabase_auth(
                actual_user_id,
                user_email,
                "Free"
            )
        
        return JSONResponse(content={
            "status": "success",
            "user": user
        })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supabase auth endpoint error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Supabase authentication failed: {str(e)}")


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
async def create_subscription(
    request: CreateSubscriptionRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Create a PayPal subscription for a user.
    
    Args:
        request: Subscription request with plan_name, user_email, and optional user_id
        credentials: Optional authentication token (Bearer token)
        
    Returns:
        Subscription details with approval URL
    """
    try:
        if request.plan_name == "Free":
            return JSONResponse(
                status_code=400,
                content={"error": "Free plan does not require payment"}
            )
        
        # Try to get authenticated user if token is provided
        user_id = request.user_id
        user_email = request.user_email
        
        if credentials and credentials.credentials:
            try:
                # Get authenticated user
                authenticated_user = get_current_user(credentials)
                if authenticated_user:
                    user_id = authenticated_user.get("user_id")
                    user_email = authenticated_user.get("email") or user_email
                    logger.info(f"Using authenticated user: {user_id}")
            except HTTPException:
                # If auth fails, continue with provided user_id/email
                pass
        
        # If no user_id provided and not authenticated, create new user
        if not user_id:
            # Check if user exists by email first
            existing_user = user_service.get_user_by_email(user_email)
            if existing_user:
                user_id = existing_user["user_id"]
            else:
                user = user_service.create_user(user_email, "Free")  # Start with Free, upgrade after payment
                user_id = user["user_id"]
        else:
            # User ID provided - verify user exists by checking email
            existing_user = user_service.get_user_by_email(user_email)
            if existing_user and existing_user.get("user_id") == user_id:
                # User exists and IDs match
                pass
            elif existing_user:
                # Email exists but different user_id - use existing user
                user_id = existing_user["user_id"]
            else:
                # User doesn't exist, but we have user_id from auth - user should exist
                # Just proceed with the provided user_id
                pass
        
        # Check if PayPal is configured
        if not paypal_service.api:
            raise HTTPException(
                status_code=503,
                detail="Payment service is not configured. Please contact support or try again later."
            )
        
        result = paypal_service.create_subscription(
            plan_name=request.plan_name,
            user_email=user_email,
            user_id=user_id
        )
        
        return JSONResponse(content={
            "status": "success",
            "subscription_id": result["subscription_id"],
            "approval_url": result["approval_url"],
            "plan_name": result["plan_name"]
        })
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        logger.error(traceback.format_exc())
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
            # Subscription cancelled - downgrade to Free
            if email:
                user = user_service.create_user(email, "Free")  # Downgrade to Free
                user_service.update_subscription(user["user_id"], subscription_id, "Free", "cancelled")
        elif event_type == "BILLING.SUBSCRIPTION.SUSPENDED":
            # Subscription suspended (payment failure) - downgrade to Free
            if email:
                user = user_service.create_user(email, "Free")
                user_service.handle_payment_failure(user["user_id"], subscription_id)
        elif event_type == "PAYMENT.SALE.COMPLETED":
            # Payment completed - subscription is active
            if email:
                user = user_service.create_user(email, plan_name)
                user_service.update_subscription(user["user_id"], subscription_id, plan_name, "active")
        elif event_type == "PAYMENT.SALE.DENIED" or event_type == "PAYMENT.CAPTURE.DENIED":
            # Payment denied/failed - downgrade to Free
            if email:
                user = user_service.create_user(email, "Free")
                user_service.handle_payment_failure(user["user_id"], subscription_id)
        
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.post("/cleanup")
async def cleanup_old_files():
    """Clean up old files"""
    deleted_count = file_manager.clean_old_files(days=7)
    return {"status": "success", "files_deleted": deleted_count}


@app.post("/api/subscriptions/maintenance")
async def run_subscription_maintenance():
    """
    Run subscription maintenance tasks.
    
    This endpoint should be called periodically (e.g., daily via cron job) to:
    - Refresh tokens for free users after 30 days
    - Downgrade expired paid subscriptions to Free
    
    Returns:
        Dictionary with counts of actions taken
    """
    try:
        results = user_service.run_subscription_maintenance()
        return JSONResponse(content={
            "status": "success",
            "tokens_refreshed": results["tokens_refreshed"],
            "users_downgraded": results["users_downgraded"]
        })
    except Exception as e:
        logger.error(f"Error running subscription maintenance: {e}")
        raise HTTPException(status_code=500, detail=f"Maintenance failed: {str(e)}")


@app.post("/api/metadata/cleanup")
async def cleanup_metadata(
    days: int = 1,
    check_missing_files: bool = True,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cleanup metadata: remove expired and missing file metadata
    
    Args:
        days: Days of inactivity before deletion (default: 1 for daily cleanup)
        check_missing_files: Whether to check for missing files (default: True)
    
    Returns:
        Cleanup statistics
    """
    try:
        # Get temp directory for file existence check
        base_path = str(file_manager.temp_dir) if hasattr(file_manager, 'temp_dir') else None
        
        stats = file_kb.cleanup_all(
            days=days,
            check_missing_files=check_missing_files,
            base_path=base_path
        )
        
        return JSONResponse(content={
            "status": "success",
            "expired_deleted": stats["expired_deleted"],
            "missing_deleted": stats["missing_deleted"],
            "total_deleted": stats["total_deleted"]
        })
    except Exception as e:
        logger.error(f"Error cleaning up metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@app.post("/api/metadata/cleanup/daily")
async def daily_cleanup_metadata():
    """
    Daily metadata cleanup endpoint (can be called by cron job)
    Deletes all metadata older than 1 day and missing files
    
    No authentication required (for cron job access)
    
    Returns:
        Cleanup statistics
    """
    try:
        # Get temp directory for file existence check
        base_path = str(file_manager.temp_dir) if hasattr(file_manager, 'temp_dir') else None
        
        stats = file_kb.cleanup_all(
            days=1,  # Delete everything older than 1 day
            check_missing_files=True,
            base_path=base_path
        )
        
        logger.info(f"Daily cleanup completed: {stats['total_deleted']} entries deleted")
        
        return JSONResponse(content={
            "status": "success",
            "expired_deleted": stats["expired_deleted"],
            "missing_deleted": stats["missing_deleted"],
            "total_deleted": stats["total_deleted"],
            "message": "Daily cleanup completed"
        })
    except Exception as e:
        logger.error(f"Error in daily cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Daily cleanup failed: {str(e)}")


@app.delete("/api/metadata/{file_name}")
async def delete_file_metadata(
    file_name: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete metadata for a specific file
    
    Args:
        file_name: Name of the file to delete metadata for
    
    Returns:
        Success status
    """
    try:
        deleted = file_kb.delete_file_metadata(file_name)
        if deleted:
            return JSONResponse(content={
                "status": "success",
                "message": f"Metadata deleted for {file_name}"
            })
        else:
            raise HTTPException(status_code=404, detail=f"Metadata not found for {file_name}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@app.get("/api/metadata/stats")
async def get_metadata_stats(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get statistics about stored metadata
    
    Returns:
        Metadata statistics
    """
    try:
        stats = file_kb.get_metadata_stats()
        return JSONResponse(content={
            "status": "success",
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error getting metadata stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

