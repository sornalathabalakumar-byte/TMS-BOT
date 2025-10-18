from dotenv import load_dotenv
load_dotenv(dotenv_path='config/.env')


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from openai import AzureOpenAI
import os
from sqlalchemy import create_engine
from datetime import date, timedelta
import textwrap





import core.nl_to_sql as nl_to_sql
import core.query_executor as query_executor
import core.result_analyzer as result_analyzer


#from core.nl_to_sql import generate_sql_query
from core.sql_validator import is_safe_query
#from core.query_executor import execute_query
#from core.result_analyzer import summarize_result
from core.logger import setup_logger
import core.schema_retriever as schema_retriever
logger = setup_logger(__name__)   

def preprocess_question_for_dates(user_question: str) -> str:
    """
    Looks for relative date terms in the user's question and replaces them
    with specific dates or date ranges that the AI can easily understand.
    """
    today = date.today()
    question_lower = user_question.lower()

    # --- Handle "today" ---
    if "today" in question_lower:
        date_str = today.strftime('%Y%m%d')
        return question_lower.replace("today", f"on the date {date_str}")
        
    # --- Handle "yesterday" ---
    elif "yesterday" in question_lower:
        yesterday = today - timedelta(days=1)
        date_str = yesterday.strftime('%Y%m%d')
        return question_lower.replace("yesterday", f"on the date {date_str}")

    # --- Handle "last month" ---
    elif "last month" in question_lower:
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        start_date_str = first_day_of_last_month.strftime('%Y%m%d')
        end_date_str = last_day_of_last_month.strftime('%Y%m%d')
        return question_lower.replace(
            "last month", f"between the dates {start_date_str} and {end_date_str}"
        )

    # --- Handle "last week" ---
    elif "last week" in question_lower:
        start_of_last_week = today - timedelta(days=today.weekday() + 7)
        end_of_last_week = start_of_last_week + timedelta(days=6)
        start_date_str = start_of_last_week.strftime('%Y%m%d')
        end_date_str = end_of_last_week.strftime('%Y%m%d')
        return question_lower.replace(
            "last week", f"between the dates {start_date_str} and {end_date_str}"
        )

    # --- Dynamically handle "last [day of week]" ---
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    for day_name, day_number in weekdays.items():
        if f"last {day_name}" in question_lower:
            days_ago = 1
            while True:
                day_to_check = today - timedelta(days=days_ago)
                if day_to_check.weekday() == day_number:
                    last_day_date = day_to_check
                    break
                days_ago += 1
            
            date_str = last_day_date.strftime('%Y%m%d')
            return question_lower.replace(f"last {day_name}", f"on the date {date_str}")

    # If no special date terms are found, return the original question
    return user_question

def classify_intent(history: list[dict[str, str]]) -> str:
    """
    Uses the AI to classify the user's latest question into one of a few categories.
    This helps us decide which tools or schemas to use.
    """
    intent_prompt = textwrap.dedent("""
        Classify the user's final question into one of the following categories based on the conversation history:
        1. "audit_history": The user is asking about the history of changes, what was changed, who changed it, or using words like 'audit', 'log', 'history', 'track', 'update', 'change'.
        2. "data_retrieval": The user is asking a general question about the data itself (e.g., counts, sums, lists).
        **You MUST respond with only one of the two category names ("audit_history" or "data_retrieval") and nothing else.**

    """)

    messages_for_intent = [{"role": "system", "content": intent_prompt}]
    messages_for_intent.extend(history)

    try:
        response = nl_to_sql.client.chat.completions.create(
            model=nl_to_sql.AZURE_MODEL_NAME,
            messages=messages_for_intent,
            temperature=0,
            max_tokens=10  # Very small, as we only expect one word back
        )
        intent = response.choices[0].message.content.strip().lower()
        if intent not in ["audit_history", "data_retrieval"]:
            logger.warning(f"Intent classification returned an invalid category: '{intent}'. Defaulting to 'data_retrieval'.")
            return "data_retrieval"
        logger.info(f"Classified intent as: '{intent}'")
        return intent
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        return "data_retrieval" # Default to data retrieval on error


# Initialize the FastAPI app
app = FastAPI(title="TMS Bot API", description="API for converting natural language to SQL and getting summarized results.")

# --- Pydantic Models for Input and Output ---

class QueryRequest(BaseModel):
    """Defines the structure of the incoming request body."""
    history: list[dict[str, str]] # Expects a list of {"role": ..., "content": ...}

class QueryResponse(BaseModel):
    """Defines the structure of the outgoing response."""
    summary: str
    sql_query: str
    query_result: list # This will hold the data from the database

# --- API Endpoints ---

@app.get("/", tags=["Health Check"])
def root():
    """A simple endpoint to check if the API is running."""
    return {"message": "TMS Bot API is running!"}

@app.on_event("startup")
def startup_event():
    """On startup, configure clients and index the schemas."""
    # Configure clients for all modules that need it
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION")
    )
    schema_retriever.client = client
    schema_retriever.AZURE_EMBEDDING_MODEL_NAME = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    nl_to_sql.client = client
    nl_to_sql.AZURE_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME")

    result_analyzer.client = client
    result_analyzer.AZURE_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME")

    print("Configuring database engines...")
    tms_engine = create_engine(os.getenv("DATABASE_URL_TMS"))
    query_executor.tms_engine = tms_engine


    audit_engine = create_engine(os.getenv("DATABASE_URL_AUDIT"))
    query_executor.audit_engine = audit_engine
    print("Database engines configured.")
    # ------------------------------------
    
    # Load and index the schemas into memory
    schema_retriever.load_and_index_schemas()

@app.post("/query", response_model=QueryResponse, tags=["Query Processing"])
async def process_query(request: QueryRequest):
    """
    The main endpoint to process a user's natural language query.
    """
    history = request.history
    if not history:
        raise HTTPException(status_code=400, detail="History cannot be empty.")
    
    user_question = history[-1]["content"]

    logger.info(f"Received question: '{user_question}'")
    logger.info(f"Full history contains {len(history)} messages.")
    # --- START OF CHANGE ---
    # First, preprocess the question to handle relative dates
    try :
        intent = classify_intent(history)
        
        # 2. Based on the intent, retrieve the correct schemas.
        if intent == "audit_history":
            # If the user wants audit history, we FORCE the retriever to only
            # consider the audit schemas, bypassing the normal RAG search.
            relevant_schemas = schema_retriever.retrieve_specific_schemas(
                ["PSGAuditStats.tblAuditLogMaster", "PSGAuditStats.tblAuditLogDetail"]
            )
        else:
            # For all other questions, use the normal RAG process.
            processed_question = preprocess_question_for_dates(user_question)
            history[-1]["content"] = processed_question
            relevant_schemas = schema_retriever.retrieve_relevant_schemas(processed_question)
    
        logger.info(f"Retrieved Schemas:\n{relevant_schemas}")

        # Step 1: Generate SQL from the natural language question
        #sql_query = generate_sql_query(user_question)
        sql_query = nl_to_sql.generate_sql_query(history, relevant_schemas)

        if "ERROR:" in sql_query:
            logger.error(f"Failed to generate SQL for '{user_question}': {sql_query}")
            raise HTTPException(status_code=400, detail=f"Failed to generate SQL: {sql_query}")
        #print(f"Generated SQL: {sql_query}")
        logger.info(f"Generated SQL: {sql_query}")


        # Step 2: Validate the generated SQL to ensure it's safe
        is_safe, message = is_safe_query(sql_query)
        if not is_safe:
            logger.warning(f"Validation Failed for SQL '{sql_query}': {message}")
            raise HTTPException(status_code=403, detail=f"Validation Failed: {message}")
        #print("SQL query passed validation.")
        logger.info("SQL query passed validation.")


        # Step 3: Execute the safe SQL query against the database
        result_df, error = query_executor.execute_query(sql_query)
        if error:
            logger.error(f"Database execution failed for SQL '{sql_query}': {error}")
            raise HTTPException(status_code=500, detail=f"Database execution failed: {error}")
        #print("Query executed successfully.")
        logger.info("Query executed successfully.")

        
        # Handle cases where the query runs but returns no data
        if result_df is None:
            logger.info("Query returned no data (None result). Initializing empty DataFrame.")
            result_df = pd.DataFrame() # Create an empty DataFrame to avoid errors
        

        # Step 4: Analyze the result and generate a natural language summary
        summary = result_analyzer.summarize_result(history, result_df)
        #print(f"Generated Summary: {summary}")
        logger.info(f"Generated Summary: {summary}")


        # Step 5: Format the DataFrame result into a JSON-friendly list of dictionaries
        # This is easy for frontends to work with.
        query_result_json = result_df.to_dict(orient='records')

        # Return the final, structured response
        logger.info("Successfully processed query and returning response.")

        return QueryResponse(
            summary=summary,
            sql_query=sql_query,
            query_result=query_result_json
        )
    except HTTPException:
        raise 
    except Exception as e:
            # Catch any unexpected server errors and log them with traceback
            logger.exception(f"An unhandled internal server error occurred: {e}")
            print(f"An unhandled internal server error occurred: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error: An unexpected issue occurred during processing.")
