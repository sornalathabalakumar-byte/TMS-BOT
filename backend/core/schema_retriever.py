# backend/core/schema_retriever.py
import numpy as np
from openai import AzureOpenAI
from pathlib import Path


# This client will be configured and passed from main.py
client: AzureOpenAI = None 
AZURE_EMBEDDING_MODEL_NAME: str = None

# This will hold our indexed schemas in memory
schema_embeddings = []
schemas = []

def get_embedding(text):
    """Generates an embedding for a given text."""
    return client.embeddings.create(input=[text], model=AZURE_EMBEDDING_MODEL_NAME).data[0].embedding

def cosine_similarity(vec1, vec2):
    """Calculates the similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def load_and_index_schemas():
    """Reads the schema file, splits it, and creates embeddings."""
    global schemas, schema_embeddings
    print("Loading and indexing schemas...")
    try: 
        script_dir = Path(__file__).parent.parent
        schema_file_path = script_dir / "models" / "schema_description.txt"
        with open(schema_file_path, 'r') as f:
            full_schema_text = f.read()
    except FileNotFoundError:
        print(f"\n--- FATAL ERROR ---")
        print(f"The schema file was not found at the expected path: {schema_file_path}")
        print("Please ensure your folder structure is correct:")
        print("backend/\n  ├── core/\n  └── models/\n      └── schema_description.txt")
        print("-------------------\n")
        raise

    # Split schemas by a delimiter (e.g., ---) and strip whitespace
    schemas = [s.strip() for s in full_schema_text.split('---') if s.strip()]

    # Generate and store embeddings for each schema
    schema_embeddings = [get_embedding(s) for s in schemas]
    print(f"✅ Indexed {len(schemas)} schemas.")

def retrieve_relevant_schemas(question, top_k=2):
    """Finds the most relevant schema(s) for a user's question."""
    question_embedding = get_embedding(question)

    similarity_scores = [cosine_similarity(question_embedding, emb) for emb in schema_embeddings]

    top_indices = np.argsort(similarity_scores)[-top_k:][::-1]

    retrieved = [schemas[i] for i in top_indices]
    return "\n---\n".join(retrieved)

def retrieve_specific_schemas(table_names: list[str]) -> str:
    """
    Retrieves the full descriptions for a specific list of table names.
    """
    global schemas
    retrieved = []
    for schema_text in schemas:
        for table_name in table_names:
            if table_name in schema_text:
                retrieved.append(schema_text)
                break # Move to the next schema_text
    return "\n---\n".join(retrieved)