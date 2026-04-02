import importlib.util
import os

_module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "peer-retrieval", "peer_retrieval.py")
)
_spec = importlib.util.spec_from_file_location("peer_retrieval_impl", _module_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

retrieve_similar_projects = _module.retrieve_similar_projects

__all__ = ["retrieve_similar_projects"]
