"""
演示脚本：展示repo-ingestion和structure-analyzer模块的基本用法
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

import importlib.util
import sys
import os

# Dynamically import modules with hyphenated directory names
def import_from_path(module_path, class_name):
    spec = importlib.util.spec_from_file_location(class_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[class_name] = module
    spec.loader.exec_module(module)
    return module

# Import repo_ingestion module
repo_ingestion_path = os.path.join(os.path.dirname(__file__), 'modules', 'repo-ingestion', 'repo_ingestion.py')
repo_ingestion_module = import_from_path(repo_ingestion_path, 'repo_ingestion')
fetch_repo_basic_info = repo_ingestion_module.fetch_repo_basic_info
GitHubAPIError = repo_ingestion_module.GitHubAPIError

# Import structure_analyzer module
structure_analyzer_path = os.path.join(os.path.dirname(__file__), 'modules', 'structure-analyzer', 'structure_analyzer.py')
structure_analyzer_module = import_from_path(structure_analyzer_path, 'structure_analyzer')
analyze_repo_structure = structure_analyzer_module.analyze_repo_structure

def demo_with_mock_data():
    """使用模拟数据演示模块功能"""
    print("=== 使用模拟数据演示 ===")
    
    # 模拟仓库数据（模拟从GitHub API获取的数据）
    mock_repo_data = {
        "repo_url": "https://github.com/example/awesome-ai-project",
        "owner": "example",
        "name": "awesome-ai-project",
        "readme_content": "# Awesome AI Project\\n\\nThis is a cutting-edge AI framework that will revolutionize the industry.\\n\\n## Features\\n- State-of-the-art models\\n- Easy to use API\\n- Comprehensive documentation\\n\\n## Installation\\n```bash\\npip install awesome-ai\\n```",
        "file_tree": [
            {"path": "README.md", "type": "blob", "size": 3072},
            {"path": "src/", "type": "tree", "size": 0},
            {"path": "src/__init__.py", "type": "blob", "size": 128},
            {"path": "src/core.py", "type": "blob", "size": 5120},
            {"path": "src/utils.py", "type": "blob", "size": 2560},
            {"path": "src/models/", "type": "tree", "size": 0},
            {"path": "src/models/__init__.py", "type": "blob", "size": 128},
            {"path": "src/models/transformer.py", "type": "blob", "size": 7168},
            {"path": "src/models/cnn.py", "type": "blob", "size": 4096},
            {"path": "tests/", "type": "tree", "size": 0},
            {"path": "tests/test_core.py", "type": "blob", "size": 1024},
            {"path": "tests/test_utils.py", "type": "blob", "size": 1024},
            {"path": "requirements.txt", "type": "blob", "size": 256},
            {"path": "setup.py", "type": "blob", "size": 1024},
            {"path": "LICENSE", "type": "blob", "size": 1024},
            {"path": ".github/", "type": "tree", "size": 0},
            {"path": ".github/workflows/", "type": "tree", "size": 0},
            {"path": ".github/workflows/ci.yml", "type": "blob", "size": 2048}
        ],
        "default_branch": "main",
        "is_fork": False,
        "created_at": "2023-01-15T10:30:00Z",
        "updated_at": "2023-06-20T14:45:00Z",
        "size": 15360,
        "language": "Python",
        "languages": {"Python": 12288, "YAML": 2048},
        "stargazers_count": 1240,
        "forks_count": 89,
        "open_issues_count": 15,
        "topics": ["machine-learning", "deep-learning", "pytorch", "artificial-intelligence"],
        "license": {"key": "mit", "name": "MIT License", "spdx_id": "MIT"},
        "description": "A state-of-the-art AI framework for machine learning and deep learning",
        "homepage": "https://awesome-ai.example.com"
    }
    
    print("1. 输入数据（模拟从GitHub获取的仓库信息）：")
    print(f"   仓库: {mock_repo_data['owner']}/{mock_repo_data['name']}")
    print(f"   描述: {mock_repo_data['description']}")
    print(f"   Stars: {mock_repo_data['stargazers_count']}")
    print(f"   语言: {mock_repo_data['language']}")
    print(f"   文件数: {len(mock_repo_data['file_tree'])}")
    
    print("\n2. 使用structure-analyzer分析仓库结构：")
    structure_result = analyze_repo_structure(mock_repo_data)
    
    print("   分析结果：")
    print(f"   - 总文件数: {structure_result['file_count']}")
    print(f"   - 总目录数: {structure_result['dir_count']}")
    print(f"   - 代码文件数: {structure_result['code_files']}")
    print(f"   - 文档文件数: {structure_result['doc_files']}")
    print(f"   - 代码/文档比例: {structure_result['code_to_doc_ratio']:.2f}")
    print(f"   - 代码字节数: {structure_result['code_bytes']}")
    print(f"   - 文档字节数: {structure_result['doc_bytes']}")
    print(f"   - 字节比例: {structure_result['bytes_ratio']:.2f}")
    print(f"   - 最大目录深度: {structure_result['max_depth']}")
    print(f"   - 平均目录深度: {structure_result['avg_depth']:.2f}")
    print(f"   - 是否有入口点: {structure_result['has_entry_point']}")
    print(f"   - 是否有测试: {structure_result['has_tests']}")
    print(f"   - 是否有配置文件: {structure_result['has_config_files']}")
    print(f"   - 是否有CI/CD: {structure_result['has_ci_cd']}")
    print(f"   - 是否有许可证: {structure_result['license_file_present']}")
    print(f"   - README质量评分: {structure_result['readme_quality_score']:.2f}")
    print(f"   - 综合结构评分: {structure_result['structure_score']:.2f}")
    
    print("\n3. 文件类型分布：")
    for ext, count in sorted(structure_result['file_type_distribution'].items()):
        ext_display = ext if ext else "(无扩展名)"
        print(f"   {ext_display}: {count} 个文件")
    
    print("\n=== 演示完成 ===")

def demo_error_handling():
    """演示错误处理"""
    print("\n=== 错误处理演示 ===")
    
    # 测试无效URL
    try:
        fetch_repo_basic_info("https://example.com/not-a-github-repo")
    except ValueError as e:
        print(f"✓ 正确捕获无效URL错误: {e}")
    
    # 测试另一种无效URL
    try:
        fetch_repo_basic_info("not-a-url-at-all")
    except ValueError as e:
        print(f"✓ 正确捕获无效URL错误: {e}")
    
    print("=== 错误处理演示完成 ===")

if __name__ == "__main__":
    print("AI假项目检测器 - 模块演示")
    print("=" * 50)
    
    demo_with_mock_data()
    demo_error_handling()
    
    print("\n" + "=" * 50)
    print("演示结束！")