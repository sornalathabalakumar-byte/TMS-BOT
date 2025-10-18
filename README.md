# TMS Bot: Natural Language to SQL 🤖

This project is a web application that allows you to ask questions about a database in plain English. An AI assistant translates your question into a SQL query, fetches the data, and gives you a summarized answer.

This version is configured to run with a local sample database (`employee_data.db`) to demonstrate the core functionality for time being.

## Features
* **Natural Language to SQL**: Converts English questions into SQL queries using Azure OpenAI.
* **RAG (Retrieval-Augmented Generation)**: Intelligently finds the most relevant tables for your question, making it scalable.
* **Secure & Safe**: Includes a validation layer to ensure only safe, read-only queries are run.
* **AI-Powered Summaries**: Provides clear, human-readable answers based on the query results.
* **User-Friendly Interface**: Built with Streamlit for a simple and clean user experience.

## Technology Stack
* **Backend**: Python, FastAPI
* **Frontend**: Streamlit
* **AI**: Azure OpenAI Service (GPT models for generation, Ada for embeddings)
* **Database**: SQLite (for this example) for time being.
* **Testing**: pytest

---

## 🚀 Getting Started: A Step-by-Step Guide

### What You'll Need (Prerequisites)
Before you begin, make sure you have the following software installed on your computer:
* **Python** (version 3.10 or newer). You can download it from [python.org](https://www.python.org/downloads/).
* A code editor like **Visual Studio Code**. You can download it from [code.visualstudio.com](https://code.visualstudio.com/).

## Step1 : Set Up the Python Environment
We'll create a "virtual environment," which is like a private workspace for this project's Python libraries.
Open a new terminal inside VS Code (Terminal > New Terminal).
Create the environment by running:
    **python -m venv tbotenv**

## Step2 :Activate the environment. You'll need to do this every time you open a new terminal for this project.
On Windows:
**tbotenv\Scripts\activate**
On macOS/Linux:
**source tbotenv/bin/activate**


## Step 3: Install All Required Libraries
Install all the project's dependencies from the requirements.txt file with this single command:
**pip install -r requirements.txt**

## Step 4: Create the Sample Database
This project uses a simple file-based database. Run the setup script to create and populate it. This is a one-time step.
**python setup_database.py**
This will create a new file named employee_data.db in your project folder.


## Step 5: Configure Your API Keys
You need to provide your Azure OpenAI credentials so the bot can use the AI.
    Navigate to the backend/config/ folder.
    Create a new file named .env.
    Copy the text below and paste it into your .env file.
    Replace the placeholder values with your actual Azure credentials. The DATABASE_URL is already set up for the sample database.
# --- Azure OpenAI Credentials ---
# Get these from your Azure AI Studio resource
AZURE_OPENAI_ENDPOINT="your_endpoint_url_here"
AZURE_OPENAI_API_KEY="your_api_key_here"
AZURE_OPENAI_MODEL_NAME="your_chat_model_deployment_name_here"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="your_embedding_model_deployment_name_here"
AZURE_API_VERSION="2024-02-01" # Or your specific API version

# --- SQL Database Connection String ---
# This is already configured for the local employee_data.db file. No changes are needed here.
DATABASE_URL="sqlite:///employee_data.db"


## ▶️ How to Run the Application
The application has two parts (backend and frontend) that need to be running at the same time in two separate terminals.

Terminal 1: Start the Backend (The "Brain")
Make sure your virtual environment is active ((tbotenv)).
Navigate into the backend folder: **cd backend**
Start the server:**uvicorn main:app --reload**
Leave this terminal running. It will show log messages as you use the app.

Terminal 2: Start the Frontend (The "Face")
Open a new, second terminal in VS Code.
Activate the virtual environment again in this new terminal:
On Windows: **tbotenv\Scripts\activate**
On macOS/Linux: **source tbotenv/bin/activate**
Make sure you are in the main TMS_BOT folder (you should be by default).
Start the Streamlit app:**streamlit run frontend/app.py**
A new tab will automatically open in your web browser at **http://localhost:8501.** You can now use the bot!

## 🛑 How to Stop the Application
To stop the bot, go to each of your two terminals and press Ctrl + C.

## How to Run Tests (Automated testing)
To verify that all backend components are working correctly, you can run the automated tests.
Make sure you are in the main TMS_BOT folder.
Run the command:**pytest**













