import json
import os

class Knowledge:

    def __init__(self, file_path = "./knowledge.json"):
        self.file_path = file_path
        self.data = self._load_json()
        self.last_modified = os.path.getmtime(file_path)

    def _load_json(self):
        if not os.path.exists(self.file_path):
            print(f"{self.file_path} not found. Creating an empty knowledge base.")
            return None
        with open(self.file_path, "r") as f:
            return json.load(f)
    
    def _save_json(self):
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=2)
        print(f"Knowledge file updated: {self.file_path}")

    def get(self):
        return {
            "thresholds": self.data.get("thresholds", {}),
            "weights": self.data.get("weights", {})
        }
    
    def get_threshold(self, metric):
        return self.data.get("thresholds", {}).get(metric, {})

    def get_weight(self, metric):
        return self.data.get("weights", {}).get(metric, None)
    
    def set(self, section, key, value):
        if section not in self.data:
            raise ValueError(f"Invalid section: {section}")
        self.data[section][key] = value
        self._save_json()

    def reload_if_updated(self):
        modified = os.path.getmtime(self.file_path)
        if modified != self.last_modified:
            self.data = self._load_json()
            self.last_modified = modified