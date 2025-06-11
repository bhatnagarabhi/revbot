import os
import sys
from exceptiongroup import catch
import toml

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
        print(self.config)
        
    def _load_config(self) -> dict:
        """
        Summary:
            Load the toml properties file
        Returns:
            dict: Toml dictionary
        """
        if not os.path.exists(self.config_path):
            print(f"ERROR: {self.config_path} not found.")
        try:
            with open(self.config_path, 'r') as f:
                config_data = toml.load(f)
            return config_data
        except Exception as e:
            raise RuntimeError(f"Unexpected error occured while loading config: {e}")
        except toml.TomlDecodeError as e:
            raise ValueError(f"ERROR: Error decoding TOML configuration: {e}")
        
        
if __name__ == "__main__":
    config_path = 'properties.toml'
    try:
        app = Shredder(config_path=config_path)
    except FileNotFoundError:
        print(f"ERROR: {config_path} not found")

# for root, subdirs, files in os.walk(CODEBASE_DIR):
#     # print(f"Root Directory = {root}")
#     # print(f"Subdirectories = {subdirs}")
#     # print(f"Files = {files}")
#     for file in files:
#         print(os.path.join(root, file))