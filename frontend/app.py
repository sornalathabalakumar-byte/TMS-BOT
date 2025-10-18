import streamlit as st
import requests
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="TMS Bot (Conversational)", page_icon="🤖", layout="wide")

# --- UI Components ---
st.title("TMS Bot: Your Conversational Database Assistant 🤖")

API_URL = "http://127.0.0.1:8000/query"

# --- Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Past Messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle New User Input ---
if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Call the Backend with the ENTIRE history ---
    with st.spinner('Thinking...'):
        try:
            # The payload now sends the full list of messages under the "history" key
            payload = {"history": st.session_state.messages}
            response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                data = response.json()
                summary = data['summary']

                with st.chat_message("assistant"):
                    st.markdown(summary)
                    with st.expander("Show Technical Details"):
                        st.code(data['sql_query'], language='sql')
                        if data['query_result']:
                            st.dataframe(pd.DataFrame(data['query_result']))

                st.session_state.messages.append({"role": "assistant", "content": summary})
            else:
                error_details = response.json().get('detail', 'Unknown error')
                st.error(f"Failed to get an answer. Server responded with: {error_details}")

        except requests.exceptions.ConnectionError:
            st.error("Connection Error: Could not connect to the backend. Is the FastAPI server running?")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")