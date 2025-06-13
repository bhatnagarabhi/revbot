from curses import meta
import os
import random
from time import sleep
import toml
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

class Shredder:
    
    def __init__(self, config_path: str):
        """
        Summary:
            Init the application
        Args:
            config_path (str): Path to toml file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.CODEBASE_PATH = self.config['application']['codebase_path']
        self.IGNORED_PATHS = self.config['application']['ignored_paths']
        self.IGNORED_EXTENSIONS = self.config['application']['ignored_extensions']
        self.NUM_THREADS = self.config['application']['num_threads']
        print(f"[INFO] Using code directory: {self.CODEBASE_PATH}")
        print(f"[INFO] Ignoring paths: {self.IGNORED_PATHS}")
        print(f"[INFO] Ignoring extensions: {self.IGNORED_EXTENSIONS}")
        
        self.compatible_files = self.find_compatible_files(self.CODEBASE_PATH, self.IGNORED_EXTENSIONS, self.IGNORED_PATHS)
        
        # Call the function to start chunking
        self.chunk_files(self.compatible_files)
        

    def _load_config(self) -> dict:
        """
        Summary:
            Load the toml properties file
        Returns:
            dict: Toml dictionary
        """
        if not os.path.exists(self.config_path):
            print(f"[ERROR] {self.config_path} not found.")
        try:
            with open(self.config_path, 'r') as f:
                config_data = toml.load(f)
            return config_data
        except Exception as e:
            raise RuntimeError(f"Unexpected error occured while loading config: {e}")
        except toml.TomlDecodeError as e:
            raise ValueError(f"[ERROR] Error decoding TOML configuration: {e}")
        
    def generate_md5(self, input: str) -> str:
        return hashlib.md5(input.encode()).hexdigest()
        
    def find_compatible_files(self, start_dir: str, ignore_extensions: list, ignore_paths: list) -> list:
        """
        Summary:
            Find compatible splittable files
        Returns:
            list: Py list of compatible files
        """
        found_files=[]
        ignored_extensions_set = {ext.lower() for ext in ignore_extensions}
        ignored_paths_set = {path_name.lower() for path_name in ignore_paths}
        
        for root, _, filenames in os.walk(start_dir):
            _[:] = [d for d in _ if d.lower() not in ignored_paths_set]
            for filename in filenames:
                file_extension = os.path.splitext(filename)[1].lower()
                if file_extension not in ignored_extensions_set:
                    full_file_path = os.path.join(root, filename)
                    found_files.append(full_file_path)
        return found_files
            
    def single_file_task(self, file_path: str) -> dict:
        """
        Summary: Template function for threads to execute

        Args:
            file (str): File to process
        """
        try:
            with open(file_path, 'r') as f:
                meta_file_path = f.name
                file_content = f.readlines()
                if not file_content.strip():
                    print(f"[INFO] Skipping empty or whitespace-only file: {meta_file_path}")
                    return None
                file_uuid = self.generate_md5(meta_file_path)
                print(f"[INFO] Consuming: {meta_file_path}")
                print(f"[INFO] Generated md5: {file_uuid}")
                return {
                    "content": file_content,
                    "metadata": {
                        "file_path": meta_file_path,
                        "file_name": os.path.basename(meta_file_path),
                        "uuid": file_uuid
                    }
                }
        except FileNotFoundError:
            print(f"[ERROR] File not found: {file_path}")
            return None
        except Exception as e:
            print(f"[ERROR] Error occurred while reading {file_path}: {e}")
            return None
    
    def chunk_files(self, file_list: list) -> list:
        """
        Summary:
            Manages the multithreaded reading and chunking of files.
            This is the "runner" that orchestrates the concurrent execution
            of `_process_single_file_task`.

        Args:
            file_list (List[str]): List of file paths to process.

        Returns:
            List[Dict]: A list of dictionaries, where each dictionary represents a chunk.
                        Each dictionary contains 'content' and 'metadata'.
        """
        self.processed_chunks = []
        if not file_list:
            raise RuntimeError(f"[ERROR] No valid files available for {self.CODEBASE_PATH}.")
        print(f"[INFO] Starting multithreaded file processing for {len(file_list)} files...")
        try:
            with ThreadPoolExecutor(max_workers=self.NUM_THREADS) as executor:
                future_to_filepath = {
                    executor.submit(self.single_file_task, file_path): file_path
                    for file_path in file_list
                }
            for future in as_completed(future_to_filepath):
                file_path = future_to_filepath[future]
                try:
                    chunk_data = future.result()
                    if chunk_data is not None:
                        self.processed_chunks.append(chunk_data)
                except Exception as e:
                    print(f"[ERROR] Exception occurred while processing {file_path}: {e}")
            print(f"[INFO] Finished multithreaded file processing. Total {len(self.processed_chunks)} valid chunks generated.")
        except Exception as e:
            print(f"[ERROR] An unhandled error occurred in the multithreaded runner: {e}")
            raise

if __name__ == "__main__":
    config_path = 'properties.toml'
    try:
        app = Shredder(config_path=config_path)
    except FileNotFoundError:
        print(f"[ERROR] {config_path} not found")

# for root, subdirs, files in os.walk(CODEBASE_DIR):
#     # print(f"Root Directory = {root}")
#     # print(f"Subdirectories = {subdirs}")
#     # print(f"Files = {files}")
#     for file in files:
#         print(os.path.join(root, file))