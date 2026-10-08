import json
import os
from datetime import datetime


class MemoryStore:

    def __init__(self, file_path="memory/orbit_memory.json"):
        self.file_path = file_path
        self._ensure_storage()

    def _ensure_storage(self):
        folder = os.path.dirname(self.file_path)

        if folder:
            os.makedirs(folder, exist_ok=True)

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump([], file)

    def _load(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _save(self, memories):
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(
                memories,
                file,
                ensure_ascii=False,
                indent=2
            )

    def add(self, content, memory_type="general"):
        memories = self._load()

        memory = {
            "content": content,
            "type": memory_type,
            "timestamp": datetime.utcnow().isoformat()
        }

        memories.append(memory)
        self._save(memories)

        return memory

    def get_all(self):
        return self._load()

    def clear(self):
        self._save([])

        return True
