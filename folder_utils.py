import uuid
from slugify import slugify
from pathlib import Path

class OutputFolder:
    def __init__(self, parent_folder: str, title: str):
        """
        Initialize an OutputFolder instance.

        Args:
            parent_folder (str): The parent folder where the output folder will be created.
            title (str): The title used to generate the output folder name.
        """
        self.parent = parent_folder
        self.title = title
        self.title_slug = slugify(title)
        self.path = self._create_folder()

    def _create_folder(self) -> Path:
        """
        Create a unique output folder based on the title and a random UUID.

        Returns:
            Path: The path to the created output folder.
        """
        folder_name = f"{self.title_slug}-{uuid.uuid4()}"
        path = Path(self.parent) / folder_name
        path.mkdir(parents=True, exist_ok=True)
        return path