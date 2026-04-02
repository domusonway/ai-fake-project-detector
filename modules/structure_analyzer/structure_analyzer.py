import importlib.util
import os

_module_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "structure-analyzer", "structure_analyzer.py")
)
_spec = importlib.util.spec_from_file_location("structure_analyzer_impl", _module_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

analyze_repo_structure = _module.analyze_repo_structure

__all__ = ["analyze_repo_structure"]
