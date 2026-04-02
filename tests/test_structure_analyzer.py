import pytest
import sys
import os
from .fixtures import get_project_fixture
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.structure_analyzer.structure_analyzer import analyze_repo_structure

NORMAL_REPO_DATA = {"file_tree": get_project_fixture("substantive")["file_tree"]}
EMPTY_REPO_DATA = {"file_tree": []}
NO_CODE_REPO_DATA = {"file_tree": get_project_fixture("hype_heavy")["file_tree"]}
ONLY_CODE_REPO_DATA = {"file_tree": get_project_fixture("early_but_real")["file_tree"]}
SPEC_STYLE_REPO_DATA = {"file_tree": get_project_fixture("substantive")["file_tree"]}

def test_analyze_repo_structure_normal_case():
    """测试正常情况的结构分析"""
    result = analyze_repo_structure(NORMAL_REPO_DATA)
    print(f"Result: {result}")
    # 基本计数检查
    assert result["file_count"] == 10
    assert result["dir_count"] == 7
    assert result["code_files"] == 7
    assert result["doc_files"] == 3
    
    # 比例检查
    assert abs(result["code_to_doc_ratio"] - 2.3333333333333335) < 0.001
    assert result["code_bytes"] == 12944
    assert result["doc_bytes"] == 5500
    assert abs(result["bytes_ratio"] - 2.3534545454545454) < 0.001
    
    # 深度检查
    assert result["max_depth"] == 2
    assert abs(result["avg_depth"] - 0.6875) < 0.001
    
    # 文件类型分布
    assert result["file_type_distribution"][".md"] == 2
    assert result["file_type_distribution"][".py"] == 5
    assert result["file_type_distribution"][".toml"] == 1
    assert result["file_type_distribution"][".yml"] == 1
    assert result["file_type_distribution"][""] == 1
    
    # 特殊文件检测
    assert result["has_entry_point"] is True
    assert result["has_tests"] is True
    assert result["has_config_files"] is True
    assert result["has_ci_cd"] is True
    assert result["license_file_present"] is True
    
    # 评分应该在合理范围内
    assert 0.0 <= result["readme_quality_score"] <= 1.0
    assert 0.0 <= result["structure_score"] <= 1.0

def test_analyze_repo_structure_empty_file_tree():
    """测试空文件树的情况"""
    result = analyze_repo_structure(EMPTY_REPO_DATA)
    
    assert result["file_count"] == 0
    assert result["dir_count"] == 1  # 只有根目录
    assert result["code_files"] == 0
    assert result["doc_files"] == 0
    assert result["code_to_doc_ratio"] == 0.0
    assert result["code_bytes"] == 0
    assert result["doc_bytes"] == 0
    assert result["bytes_ratio"] == 0.0
    assert result["max_depth"] == 0
    assert result["avg_depth"] == 0.0
    assert result["file_type_distribution"] == {}
    assert result["has_entry_point"] == False
    assert result["has_tests"] == False
    assert result["has_config_files"] == False
    assert result["has_ci_cd"] == False
    assert result["license_file_present"] == False

def test_analyze_repo_structure_no_code():
    """测试只有文档没有代码的情况"""
    result = analyze_repo_structure(NO_CODE_REPO_DATA)
    
    assert result["file_count"] == 6
    assert result["code_files"] == 2
    assert result["doc_files"] == 4
    assert result["code_to_doc_ratio"] == 0.5
    assert result["code_bytes"] == 560
    assert result["doc_bytes"] == 5400
    assert result["bytes_ratio"] == 0.1037037037037037
    assert result["has_entry_point"] is False
    assert result["has_tests"] is False
    assert result["has_config_files"] is False

def test_analyze_repo_structure_only_code():
    """测试只有代码没有文档的情况"""
    result = analyze_repo_structure(ONLY_CODE_REPO_DATA)
    
    assert result["file_count"] == 8
    assert result["code_files"] == 5
    assert result["doc_files"] == 3
    assert result["code_to_doc_ratio"] == 1.6666666666666667
    assert result["code_bytes"] == 6950
    assert result["doc_bytes"] == 3400
    assert result["bytes_ratio"] == 2.0441176470588234
    assert result["has_entry_point"] is True

def test_analyze_repo_structure_accepts_spec_style_file_types():
    """测试符合SPEC的file/dir类型和隐式目录计算"""
    result = analyze_repo_structure(SPEC_STYLE_REPO_DATA)

    assert result["file_count"] == 10
    assert result["dir_count"] == 7
    assert result["code_files"] == 7
    assert result["doc_files"] == 3
    assert abs(result["code_to_doc_ratio"] - 2.3333333333333335) < 0.001
    assert result["max_depth"] == 2

def test_analyze_repo_structure_invalid_file_tree_item():
    """测试缺少path/type的file_tree元素"""
    with pytest.raises(ValueError, match="Invalid file_tree item"):
        analyze_repo_structure({"file_tree": [{"path": "README.md"}]})

def test_analyze_repo_structure_missing_file_tree():
    """测试缺少必要的file_tree字段"""
    with pytest.raises(KeyError, match="file_tree"):
        analyze_repo_structure({"some_other_field": "value"})

def test_analyze_repo_structure_invalid_input():
    """测试无效输入的情况"""
    with pytest.raises(ValueError, match="repo_data must be a dictionary"):
        analyze_repo_structure("invalid_input")
    
    with pytest.raises(ValueError, match="file_tree must be a list"):
        analyze_repo_structure({"file_tree": "not_a_list"})

if __name__ == "__main__":
    # 运行测试
    test_analyze_repo_structure_normal_case()
    test_analyze_repo_structure_empty_file_tree()
    test_analyze_repo_structure_no_code()
    test_analyze_repo_structure_only_code()
    test_analyze_repo_structure_missing_file_tree()
    test_analyze_repo_structure_invalid_input()
    print("All tests passed!")
