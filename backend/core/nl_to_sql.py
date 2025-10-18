import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from datetime import date

# --- Azure OpenAI Client Setup ---
# Load environment variables from the .env file
#load_dotenv(dotenv_path='backend/config/.env')

'''# Initialize the Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_API_VERSION")
)
# Get the model deployment name from the environment variables
AZURE_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME")
'''

client: AzureOpenAI = None
AZURE_MODEL_NAME: str = None

'''def get_schema_description():
    """Reads the database schema description from the file."""
    try:
        with open('models/schema_description.txt', 'r') as f:
            schema = f.read()
        return schema
    except FileNotFoundError:
        return "Error: Schema description file not found."
'''
"""
    Generates a SQL query from a natural language user question.

    Args:
        user_question (str): The user's question in plain English.

    Returns:
        str: The generated T-SQL query string or an error message.
"""
def generate_sql_query(history: list[dict[str, str]], retrieved_schemas: str):
   
    # This is the "System Prompt". It gives the AI its instructions and context.
    # Good prompt engineering is key to getting good results.

    today_date = date.today().strftime("%Y-%m-%d")

    print(today_date)
      
    system_prompt = f"""You are an expert T-SQL assistant. Your another task is to convert a user's question into a valid T-SQL query based on the business rules and schema below.
    ---
     BUSINESS RULES (in order of importance):
        1.  **CRITICAL 3-TABLE JOIN RULE for Rejection Reasons**: To find the correct rejection description (`RejDesc`), you MUST perform a three-table join as shown in the examples below. This requires joining `DetailFile1`, `WorkSrcDesc`, and `REJREASON` and includes a fallback to a generic reason.

        2.  **CRITICAL EFFICIENCY RULE for Counting**:
            - To count **accepted** items (transactions, checks, or stubs), you **MUST ONLY** use the summary columns (`TotalTrans`, `CheckCount`, `StubCount`) in the `BATCHFILE` table.
            - To count **rejected** transactions or items, you **MUST** use the `DetailFile1` table where the `Reject` column is 1. To count unique rejected transactions, use `COUNT(DISTINCT TranNo)`.

        3.  **CRITICAL RULE for Conversational Context**: You MUST analyze the entire conversation history. If a previous message contains a filter (like a date range or a specific batch number), you MUST apply that same filter to the current query unless the user explicitly provides a new one. This is your most important instruction.
        4.  **CRITICAL RULE for Yes/No Questions**: You MUST NOT answer yes/no questions directly. ALWAYS convert them into a SQL query that can find the answer.

        5.  **CRITICAL RULE for Audit History**: To answer questions about 'audit history' or 'what changed', you MUST JOIN `tblAuditLogMaster` and `tblAuditLogDetail` on the `LogId` column. The Master table tells you WHO performed an action and WHEN, and the Detail table tells you WHAT field was changed.
        
        6.The current date is {today_date}

    ---

    EXAMPLES:
        - User Question: "Why were the transactions in batch 0000578130 rejected?"
        - SQL Query: SELECT T3.RejDesc FROM PSGTMS.DetailFile1 AS T1 JOIN PSGTMS.WorkSrcDesc AS T2 ON T1.WorkSrc = T2.WorkSource JOIN PSGTMS.REJREASON AS T3 ON T1.RejectPgm = T3.PgmID AND T1.RejectReason = T3.RejID WHERE T1.BatchNo = '0000578130' AND T1.Reject = 1 AND (T3.WSIdx = T2.WSIdx OR T3.WSIdx = 0) ORDER BY T3.WSIdx DESC;
        
        - User Question: "how many transactions were processed yesterday?"
        - SQL Query: SELECT SUM(TotalTrans) FROM PSGTMS.BATCHFILE WHERE ProcessDate = CONVERT(int, CONVERT(varchar, GETDATE()-1, 112));
        ---
    Here is the database schema you must use:
        ---
        {retrieved_schemas}
        ---

        YOUR TASK:
        - Using the full conversation history for context, generate the correct T-SQL query for the user's latest question.
        - Strictly output only a single T-SQL `SELECT` statement. Do not answer the question directly or add any explanations.
    """

    

   
    messages_for_api = [{"role": "system", "content": system_prompt}]
    
    # 2. Add the entire user/assistant conversation history.
    messages_for_api.extend(history)

    # This is the new, updated system_prompt

    print("--- Sending request to Azure OpenAI ---")
    try:
        response = client.chat.completions.create(
            model=AZURE_MODEL_NAME, # Your model deployment name
            messages=messages_for_api,
            temperature=0, # Lower temperature for more deterministic, factual results
            max_tokens=500
        )

        sql_query = response.choices[0].message.content.strip() 
        #print(f"Generated SQL Query: {sql_query}")


        # A final check to ensure it's not returning an error message
        if "ERROR" in sql_query.upper():
             return "ERROR: The question cannot be answered with the available data."

        return sql_query

    except Exception as e:
        print(f"An error occurred with the OpenAI API: {e}")
        return f"Error: Failed to generate SQL query. {e}"


# --- Example of how to run this file directly for testing ---
if __name__ == '__main__':
    # Make sure your schema_description.txt is filled out before testing!
    test_question = "How many records are in the tblItemStatistics table?"

    print(f"User Question: \"{test_question}\"")
    generated_query = generate_sql_query(test_question)
    print("\n--- Generated SQL Query ---")
    print(generated_query)