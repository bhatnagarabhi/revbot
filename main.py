from curses import meta
import os
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
    
    def chunk_files(self, file_list: list) -> list:
        """
        Summary:
            Read and chunk files

        Args:
            file_list (list): List of files to recurse through
        """
        if file_list == []:
            raise RuntimeError(f"[ERROR] Could not find valid list of files in {self.CODEBASE_PATH}.")
        try:
            for file in file_list:
                with open(file, 'r') as f:
                    meta_file_path = f.name
                    uuid = self.generate_md5(meta_file_path)
                    file_content = f.read()
                    print(f"[INFO] Consuming: {meta_file_path}")
                    print(f"[INFO] Generated md5: {uuid}")
                    
        except Exception as e:
            print(f"[ERROR] Error occured while reading files - {e}")

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