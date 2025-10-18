import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables from the .env file in the config folder
# The path is relative to where this script is run from.
# We assume the main script runs from the 'backend' directory.
#config_file = load_dotenv(dotenv_path='backend/config/.env')

#DATABASE_URL = os.getenv("DATABASE_URL")
tms_engine = None
audit_engine = None


def execute_query(sql_query: str):
    """
    Executes a SQL query, intelligently choosing the correct database engine
    based on the schema name in the query.
    
    """
    print(f"Executing query: {sql_query}")
    engine_to_use = None

    if "PSGAuditStats" in sql_query:
        engine_to_use = audit_engine
        print("Using AUDIT database engine.")
    else:
        engine_to_use = tms_engine
        print("Using TMS database engine.")

    if engine_to_use is None:
        return None, "Error: Database engine not configured."

    try:
        # Use a 'with' statement to ensure the connection is properly closed
        with engine_to_use.connect() as connection:
            # Use pandas to directly read the SQL query into a DataFrame
            # This is efficient and handles the data types well.
            result_df = pd.read_sql_query(text(sql_query), connection)
            return result_df, None
    except SQLAlchemyError as e:
        error_message = f"Database Error: {e}"
        print(error_message)
        return None, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        return None, error_message

# --- Example of how to run this file directly for testing ---
'''if __name__ == '__main__':
    # IMPORTANT: Replace 'YourTableName' with a real table name from your database
    # For example: 'RemittanceTransactions'
    test_query =  "select top 10 * from [PSGAuditStats].[tblItemStatistics]"

    print("--- Testing Query Executor ---")
    df, error = execute_query(test_query)

    if error:
        print(f"Test failed with error: {error}")
    elif df is not None:
        if df.empty:
            print("Query executed successfully, but returned no data.")
        else:
            print("Query executed successfully! First 5 rows:")
            print(df.head())
'''
#"SELECT TOP 5 * FROM RemittanceTransactions;"