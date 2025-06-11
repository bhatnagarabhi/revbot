import os
import ast
import inspect
import requests
import json
from sklearn.neighbors import NearestNeighbors # For simple in-memory vector store
import numpy as np # For handling numerical arrays

def get_chunk_content(source_lines, node):
    """
    Extracts the source code content for a given AST node,
    handling docstrings and ensuring proper indentation.
    """
    try:
        if hasattr(node, 'end_lineno'):
            start_line = node.lineno - 1
            end_line = node.end_lineno
            return "".join(source_lines[start_line:end_line])
        else:
            # Fallback for older Python versions or nodes without end_lineno
            return "".join(source_lines[node.lineno - 1:node.lineno + 10])
    except Exception as e:
        print(f"Warning: Could not get source segment for node {node} due to {e}. Using approximate lines.")
        if hasattr(node, 'lineno'):
            return "".join(source_lines[node.lineno - 1:node.lineno + 10])
        return ""

def process_python_file(filepath):
    """
    Reads a Python file and extracts functions and classes as distinct chunks.
    Additionally, the entire file content is always added as a 'module' chunk.
    """
    chunks = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()
            source_lines = source_code.splitlines(keepends=True)

        tree = ast.parse(source_code, filename=filepath)

        # Always add the entire file content as a 'module' chunk
        if source_code.strip(): # Ensure it's not an empty file
            chunks.append({
                "file_path": filepath,
                "type": "module",
                "name": os.path.basename(filepath), # Name as the file name
                "lineno": 1,
                "content": source_code.strip()
            })

        # Extract functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                chunk_content = get_chunk_content(source_lines, node)
                if chunk_content:
                    chunks.append({
                        "file_path": filepath,
                        "type": "function",
                        "name": node.name,
                        "lineno": node.lineno,
                        "content": chunk_content.strip()
                    })
            elif isinstance(node, ast.ClassDef):
                chunk_content = get_chunk_content(source_lines, node)
                if chunk_content:
                    chunks.append({
                        "file_path": filepath,
                        "type": "class",
                        "name": node.name,
                        "lineno": node.lineno,
                        "content": chunk_content.strip()
                    })

    except SyntaxError as e:
        print(f"Skipping {filepath} due to SyntaxError: {e}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return chunks

def process_other_file(filepath):
    """
    Reads a non-Python file and treats its entire content as a single chunk.
    """
    chunks = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip():
                chunks.append({
                    "file_path": filepath,
                    "type": "file", # General type for non-Python files
                    "name": os.path.basename(filepath),
                    "lineno": 1,
                    "content": content.strip()
                })
    except Exception as e:
        print(f"Error processing non-Python file {filepath}: {e}")
    return chunks


def recursively_chunk_directory(root_dir):
    """
    Recursively walks through a directory, processes Python files using AST,
    and all other files on a per-file basis.
    Returns a list of all extracted code chunks.
    """
    all_chunks = []
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' not found.")
        return all_chunks

    print(f"Starting chunking in directory: {root_dir}")
    for dirpath, dirnames, filenames in os.walk(root_dir):
        print(f"  Processing directory: {dirpath}")
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if filename.endswith('.py'):
                print(f"    Processing Python file (AST-based): {filepath}")
                file_chunks = process_python_file(filepath)
                all_chunks.extend(file_chunks)
            else:
                # You might want to add an exclusion list for binary files, images, etc.
                # For example: if not filename.endswith(('.jpg', '.png', '.bin')):
                if not filename.endswith(('.jpg', '.png', '.bin', '.class', '.txt')):
                    print(f"    Processing other file (full file): {filepath}")
                    other_chunks = process_other_file(filepath)
                    all_chunks.extend(other_chunks)
    print("Chunking complete.")
    return all_chunks

def get_ollama_embedding(text_chunk, ollama_url="http://localhost:11434", model_name="nomic-embed-text"):
    """
    Generates an embedding for a given text chunk using a local Ollama instance.
    Assumes Ollama server is running and the specified model is downloaded.
    """
    embeddings_api_endpoint = f"{ollama_url}/api/embeddings"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "prompt": text_chunk
    }

    try:
        response = requests.post(embeddings_api_endpoint, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        if "embedding" in result:
            return result["embedding"]
        else:
            print(f"Error: 'embedding' key not found in Ollama response for chunk: {text_chunk[:100]}...")
            return None
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to Ollama at {ollama_url}. Is it running?")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Error from Ollama API ({response.status_code}): {response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while getting Ollama embedding: {e}")
        return None

def get_ollama_llm_response(prompt_text, ollama_url="http://localhost:11434", model_name="qwen2.5-coder:7b"):
    """
    Sends a prompt to a generative LLM running on a local Ollama instance (using /api/chat endpoint).
    Assumes Ollama server is running and the specified chat model is downloaded.

    Args:
        prompt_text (str): The prompt to send to the LLM.
        ollama_url (str): The URL of your local Ollama instance.
        model_name (str): The name of the chat model you want to use (e.g., "llama2", "mistral").

    Returns:
        str: The LLM's generated response.
    """
    chat_api_endpoint = f"{ollama_url}/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "stream": False # Set to False to get a single response
    }

    try:
        response = requests.post(chat_api_endpoint, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if result.get("message") and result["message"].get("content"):
            return result["message"]["content"]
        else:
            print(f"Error: Ollama chat response structure unexpected: {result}")
            return "No valid text response from Ollama LLM."
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to Ollama at {ollama_url}. Is it running and is the model available?")
        return "Error: Could not connect to Ollama LLM."
    except requests.exceptions.HTTPError as e:
        print(f"Error from Ollama Chat API ({response.status_code}): {response.text}")
        return f"Error from Ollama LLM API: {e}"
    except Exception as e:
        print(f"An unexpected error occurred while getting Ollama LLM response: {e}")
        return f"An unexpected error occurred with Ollama LLM: {e}"


if __name__ == "__main__":
    # --- 1. Define the root directory of your codebase ---
    # IMPORTANT: Replace "YOUR_CODEBASE_DIRECTORY_HERE" with the actual path
    # to the directory containing your files (Python and others).
    root_directory_to_chunk = "codebase"
    # Example: root_directory_to_chunk = "./my_project_code"
    # Example: root_directory_to_chunk = "/Users/youruser/Documents/PythonProjects/my_repo"

    # --- 2. Chunk Codebase ---
    code_chunks = recursively_chunk_directory(root_directory_to_chunk)

    # --- 3. Generate Embeddings for all chunks using Ollama ---
    print("\n--- Generating Embeddings with Ollama ---")
    ollama_url = "http://localhost:11434" # Default Ollama URL
    ollama_embedding_model_name = "nomic-embed-text" # Or any other embedding model you've pulled, e.g., "all-minilm"

    # Before running:
    # 1. Ensure Ollama server is running locally (e.g., `ollama serve`).
    # 2. Pull the embedding model you intend to use (e.g., `ollama pull nomic-embed-text`).

    chunks_with_embeddings = []
    if not code_chunks:
        print("No chunks found to embed. Please check 'root_directory_to_chunk'.")
    else:
        for i, chunk in enumerate(code_chunks):
            print(f"  Embedding chunk {i+1} ({chunk['type']}: {chunk['name']})...")
            embedding = get_ollama_embedding(chunk['content'], ollama_url, ollama_embedding_model_name)
            if embedding:
                chunk['embedding'] = np.array(embedding) # Convert to numpy array for sklearn
                chunks_with_embeddings.append(chunk)
                print(f"    Embedding generated (dimension: {len(embedding)}).")
            else:
                print(f"    Failed to generate embedding for chunk {chunk['name']}. Skipping.")

    print(f"\nSuccessfully embedded {len(chunks_with_embeddings)} out of {len(code_chunks)} chunks.")

    # --- 4. Index Embeddings in a Simple In-Memory Vector Store (NearestNeighbors) ---
    if not chunks_with_embeddings:
        print("No chunks with embeddings to index. Exiting RAG setup.")
    else:
        print("\n--- Indexing Embeddings in NearestNeighbors (In-Memory Vector Store) ---")
        # Extract only the embedding vectors for indexing
        embeddings_matrix = np.array([chunk['embedding'] for chunk in chunks_with_embeddings])

        # Determine n_neighbors dynamically
        # It should not be more than the number of samples available
        desired_n_neighbors = 10
        n_neighbors_to_use = min(desired_n_neighbors, len(embeddings_matrix))
        
        # Initialize NearestNeighbors model
        # metric='cosine' is often preferred for text embeddings
        nn_model = NearestNeighbors(n_neighbors=n_neighbors_to_use, metric='cosine')
        nn_model.fit(embeddings_matrix)
        print(f"NearestNeighbors model fitted with {len(embeddings_matrix)} embeddings.")
        print(f"Using n_neighbors = {n_neighbors_to_use} for retrieval.")

        # Store the original chunks in a way that's retrievable by index
        # We use a list, where the index of the embedding in embeddings_matrix
        # corresponds to the index of the chunk in original_chunks
        original_chunks = chunks_with_embeddings

        # --- 5. Demonstrate Retrieval ---
        print("\n--- Demonstrating Retrieval ---")

        # Example query: Simulating a user's question about the codebase
        query_text = "How does the main application process data?"
        # You can change this to another query to test retrieval, e.g.:
        # query_text = "How does the main application process data?"

        print(f"\nUser Query: '{query_text}'")

        # Get embedding for the user's query
        query_embedding = get_ollama_embedding(query_text, ollama_url, ollama_embedding_model_name)

        retrieved_chunks = [] # Initialize retrieved_chunks list here

        if query_embedding is None:
            print("Failed to generate embedding for the query. Cannot perform search.")
        else:
            # Reshape query_embedding for NearestNeighbors (it expects 2D array)
            query_embedding_reshaped = np.array(query_embedding).reshape(1, -1)

            # Perform similarity search
            actual_n_neighbors_for_query = min(nn_model.n_neighbors, len(embeddings_matrix))
            if actual_n_neighbors_for_query == 0:
                print("No neighbors to search for, as no embeddings are available.")
            else:
                distances, indices = nn_model.kneighbors(query_embedding_reshaped, n_neighbors=actual_n_neighbors_for_query)

                print("\n--- Retrieved Relevant Chunks ---")
                for i, idx in enumerate(indices[0]):
                    retrieved_chunk = original_chunks[idx]
                    retrieved_chunks.append(retrieved_chunk) # Add retrieved chunk to the list
                    distance = distances[0][i]
                    print(f"\nRank {i+1} (Cosine Distance: {distance:.4f}):")
                    print(f"  File: {retrieved_chunk['file_path']}")
                    print(f"  Type: {retrieved_chunk['type']}")
                    print(f"  Name: {retrieved_chunk['name']}")
                    print(f"  Line: {retrieved_chunk['lineno']}")
                    print("  Content (excerpt):")
                    print("    " + retrieved_chunk['content'].replace('\n', '\n    ')[:300] + ("..." if len(retrieved_chunk['content']) > 300 else ""))
                    print("-" * 30)

        # --- 6. Integration with an LLM ---
        print("\n--- Integrating with Generative LLM ---")
        if query_embedding is not None and retrieved_chunks:
            # Construct the context from retrieved chunks
            context_text = "\n\n".join([c['content'] for c in retrieved_chunks])
            
            # Craft the prompt for the main LLM
            prompt_for_llm = (
                f"Based on the following code context, answer the user's question. "
                f"Be concise and directly address the question using only the provided context if possible. "
                f"If the context doesn't contain enough information, state that.\n\n"
                f"Code Context:\n```python\n{context_text}\n```\n\n"
                f"User Question: {query_text}\n\n"
                f"Answer:"
            )

            print("\nSending prompt to LLM...")
            # Use the new Ollama-compatible LLM response function
            ollama_llm_model_name = "qwen2.5-coder:7b" # Change this to the chat model you've pulled in Ollama (e.g., "mistral", "codellama")
            llm_answer = get_ollama_llm_response(prompt_for_llm, ollama_url, ollama_llm_model_name)

            print("\n--- LLM's Answer ---")
            print(llm_answer)
        else:
            print("Skipping LLM integration due to missing query embedding or no retrieved chunks.")

    # --- Cleanup (optional) ---
    # import shutil
    # if os.path.exists(root_directory_to_chunk):
    #     # Only remove if it's a dummy directory you created for testing
    #     # Do NOT uncomment this if you set root_directory_to_chunk to your actual codebase!
    #     # shutil.rmtree(root_directory_to_chunk)
    #     # print(f"\nCleaned up directory: {root_directory_to_chunk}")
    pass # Placeholder if cleanup is not needed immediately
