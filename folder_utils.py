import uuid
from slugify import slugify
from pathlib import Path
import json

class OutputFolder:
    def __init__(self, parent_folder, title):
        self.parent = parent_folder
        self.title = title
        self.title_slug = slugify(title)
        self.path = self.create_folder()

    def create_folder(self):
        folder_name = f"{self.title_slug}-{uuid.uuid4()}"
        path = Path(self.parent) / folder_name
        path.mkdir(parents=True, exist_ok=True)
        return path