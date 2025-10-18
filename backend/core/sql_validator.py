import re
import sqlparse

# List of SQL keywords that are not allowed.
# These are commands that can modify or delete data.
FORBIDDEN_KEYWORDS = [
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE',
    'RENAME', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK'
]

def is_safe_query(sql_query: str):
    """
    Validates a SQL query to ensure it is safe to execute.

    A query is considered safe if it:
    1. Is a read-only 'SELECT' statement.
    2. Does not contain any forbidden keywords that could modify or delete data.

    Args:
        sql_query (str): The SQL query string to validate.

    Returns:
        tuple: A tuple containing (is_safe, message).
               - `is_safe` is a boolean (True if safe, False otherwise).
               - `message` is a string explaining the result.
    """
    # Normalize the query to uppercase for case-insensitive checks
    query_upper = sql_query.upper()
    # 1. Ensure starts with SELECT

    if not query_upper.strip().startswith('SELECT'):
            return False, "Validation failed: Query must be a SELECT statement."


    # 2. Check for any forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        # We use regex with word boundaries (\b) to avoid false positives.
        # For example, to prevent 'UPDATE' from matching a column named 'LAST_UPDATE'.
    
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, query_upper):
            return False, f"Validation failed: Query contains forbidden keyword '{keyword}'."
        
    parsed = sqlparse.parse(sql_query)
    for stmt in parsed:
        if stmt.get_type() != "SELECT":
            return False, "Validation failed: Non-SELECT SQL detected."
    print("SQL Paresed Successfully")

        
    
    # If all checks pass, the query is considered safe
    return True, "Query is safe."

# --- Example of how to run this file directly for testing ---
if __name__ == '__main__':
    print("--- Testing SQL Validator ---")

    # List of queries to test
    test_queries = [
        "SELECT CustomerName, Amount FROM RemittanceTransactions WHERE Status = 'SUCCESS';", # Safe
        "SELECT * FROM AuditLog;", # Safe
        "UPDATE RemittanceTransactions SET Amount = 500 WHERE TransactionID = 123;", # Unsafe
        "DROP TABLE AuditLog;", # Unsafe
        "   SELECT * FROM users", # Safe (with whitespace)
        "delete from users where id = 1" # Unsafe (lowercase)
    ]

    for i, query in enumerate(test_queries):
        is_valid, message = is_safe_query(query)
        print(f"Query {i+1}: \"{query}\"")
        print(f"Result: {'SAFE' if is_valid else 'UNSAFE'} -> {message}\n")