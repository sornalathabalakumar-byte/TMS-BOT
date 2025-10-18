import os
import pandas as pd
from openai import AzureOpenAI
import textwrap

# --- Placeholders ---
# These will be configured by main.py when the server starts.
client: AzureOpenAI = None
AZURE_MODEL_NAME: str = None

def summarize_result(history: list[dict[str, str]], query_result_df: pd.DataFrame):
    """
    Analyzes a query's result to generate a natural language summary.
    This version pre-processes the data in Python for accuracy before sending it to the AI.

    """
    user_question = history[-1]["content"]
    pre_processed_summary = ""

    # --- START OF DATA PRE-PROCESSING LOGIC ---

    if query_result_df.empty:
        # If the dataframe is empty, create a simple message for the AI.
        pre_processed_summary = "The query returned no results."

    # CASE 1: Handle the complex breakdown for rejected transactions per batch.
    elif 'BatchNo' in query_result_df.columns and 'TranNo' in query_result_df.columns:
        # Use pandas to group by BatchNo and get the unique transaction numbers
        grouped = query_result_df.groupby('BatchNo')['TranNo'].unique()

        # Calculate overall totals
        total_items = len(query_result_df)
        total_unique_transactions = query_result_df['TranNo'].nunique()
        total_batches = len(grouped)

        # Build a simple, factual text breakdown
        summary_lines = [
            f"A total of {total_items} items were found, belonging to {total_unique_transactions} unique transactions across {total_batches} batches.",
            "Here is the breakdown:"
        ]

        for batch_no, tran_nos in grouped.items():
            num_trans_in_batch = len(tran_nos)
            tran_list = ", ".join(map(str, sorted(tran_nos))) # Sort for consistency
            summary_lines.append(
                f"- For batch number {batch_no}, there were {num_trans_in_batch} transactions with the numbers: {tran_list}."
            )

        pre_processed_summary = "\n".join(summary_lines)

    # CASE 2: Handle all other simple queries.
    else:
        pre_processed_summary = query_result_df.to_string()

    # --- END OF DATA PRE-PROCESSING LOGIC ---


    # The new prompt is much simpler: its only job is to format our pre-processed summary.
    system_prompt = textwrap.dedent(f"""
        You are a helpful assistant. A user asked a question, and a program has already processed the data and created a factual summary.
        Your only task is to rephrase the pre-processed summary below into a single, clear, and friendly paragraph or list.

        ---
        CONTEXT:
        - User's Question: "{user_question}"
        - The full conversation so far: {history}
        - Pre-processed Data Summary to use for your answer:
        ---
        {pre_processed_summary}
        ---

        BUSINESS RULES for Summarization:
        1.  **CRITICAL RULE for No Results**: If the summary says "no results," provide a direct, negative answer to the user's question (e.g., "No rejected transactions were found for that batch.").
        2.  **CRITICAL RULE for Single-Value Answers**: If the data is just a single number, directly state what that number represents (e.g., "There were 73 rejected transactions.").
        3.  **NEW RULE for Rejection Reasons**: If the data contains a 'RejDesc' column, your summary should clearly list all the rejection reasons found.
        4.  **CRITICAL RULE for Accuracy**: You MUST use the exact numerical values and text from the pre-processed data. Do not invent information.
        ---

        YOUR TASK:
        - Present the information from the pre-processed summary in a natural, conversational way, following all the rules.
        - Do not add any extra notes like "(Note: the above is illustrative)". """)

    print("--- Sending pre-processed data to Azure OpenAI for formatting ---")
    try:
        response = client.chat.completions.create(
            model=AZURE_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Please provide the final, user-friendly summary."}
            ],
            temperature=0,
            max_tokens=1500
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print(f"An error occurred with the OpenAI API: {e}")
        return f"Error: Failed to summarize the result. {e}"

# --- Example of how to run this file directly for testing ---
if __name__ == '__main__':
    test_question = "How many records are in the tblItemStatistics table?"
    
    # Create a sample DataFrame to simulate a real query result for COUNT(*)
    # The empty column name '' is what pandas often produces for an aggregate without an alias.
    test_data = pd.DataFrame({'': [54]})

    print(f"Original Question: \"{test_question}\"")
    print("\n--- Sample Data from Database ---")
    print(test_data.to_string())
    
    summary = summarize_result(user_question=test_question, query_result_df=test_data)

    print("\n--- Generated Summary ---")
    print(summary)