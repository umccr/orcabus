# Imports
from pathlib import Path


def get_portal_run_id_path_from_relative_path(file_path: Path, portal_run_id: str) -> Path:
    portal_run_id_index = file_path.parts.index(portal_run_id)
    return Path("/".join(file_path.parts[0:portal_run_id_index + 1]))

