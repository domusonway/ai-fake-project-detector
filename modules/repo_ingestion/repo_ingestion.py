import importlib.util
import os

_module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "repo-ingestion", "repo_ingestion.py")
)
_spec = importlib.util.spec_from_file_location("repo_ingestion_impl", _module_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

fetch_repo_basic_info = _module.fetch_repo_basic_info
GitHubAPIError = _module.GitHubAPIError
requests = _module.requests

__all__ = ["fetch_repo_basic_info", "GitHubAPIError", "requests"]
