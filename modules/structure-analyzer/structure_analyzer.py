"""
structure-analyzer模块实现
负责分析仓库的结构特征，提取代码/文档比例、目录深度、文件类型分布等指标
"""
import os
from typing import Dict, List, Any


def analyze_repo_structure(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析仓库结构特征，提取代码/文档比例、目录复杂度等指标。
    
    Args:
        repo_data: 来自repo-ingestion模块的仓库数据字典
    
    Returns:
        包含结构分析结果的字典
    
    Raises:
        ValueError: 当输入数据格式不正确时
        KeyError: 当必要的数据字段缺失时
    """
    # 验证输入
    if not isinstance(repo_data, dict):
        raise ValueError("repo_data must be a dictionary")
    
    if 'file_tree' not in repo_data:
        raise KeyError("Missing required field: file_tree")
    
    file_tree = repo_data['file_tree']
    if not isinstance(file_tree, list):
        raise ValueError("file_tree must be a list")

    normalized_items = []
    directory_paths = {""}
    
    # 初始化统计变量
    file_count = 0
    dir_count = 1  # 根目录
    code_files = 0
    doc_files = 0
    code_bytes = 0
    doc_bytes = 0
    depths = [0]  # 根目录深度为0
    file_type_distribution = {}
    
    # 常见代码文件扩展名
    code_extensions = {
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp', 
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
        '.html', '.htm', '.css', '.scss', '.sass', '.less',
        '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
        '.sql', '.r', '.m', '.pl', '.lua', '.dart', '.ex', '.exs'
    }
    
    # 常见文档文件扩展名
    doc_extensions = {
        '.md', '.markdown', '.rst', '.txt', '.doc', '.docx',
        '.pdf', '.odt', '.pages', '.tex', '.wiki', '.org'
    }
    
    # 分析每个文件和目录
    for item in file_tree:
        if not isinstance(item, dict):
            raise ValueError("Invalid file_tree item")

        if 'path' not in item or 'type' not in item:
            raise ValueError("Invalid file_tree item")

        path = item['path']
        item_type = _normalize_item_type(item['type'])
        size = item.get('size', 0)

        if not isinstance(path, str) or not path:
            raise ValueError("Invalid file_tree item")

        if item_type is None:
            raise ValueError("Invalid file_tree item")

        normalized_item = {
            "path": path,
            "type": item_type,
            "size": size,
        }
        normalized_items.append(normalized_item)

        normalized_path = path.rstrip("/")
        _collect_directory_paths(directory_paths, normalized_path, item_type)

        # 计算目录深度
        depth = path.count('/') if path else 0
        depths.append(depth)
        
        if item_type == 'file':
            file_count += 1
            
            # 获取文件扩展名和文件名
            filename = os.path.basename(path)
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            # 更新文件类型分布
            if ext in file_type_distribution:
                file_type_distribution[ext] += 1
            else:
                file_type_distribution[ext] = 1
            
            # 特殊文档文件名（无扩展名）
            special_doc_files = {'license', 'copying', 'notice', 'authors', 'contributors', 'readme'}
            
            # 判断是代码文件还是文档文件
            if ext in code_extensions:
                code_files += 1
                code_bytes += size
            elif ext in doc_extensions or (not ext and filename.lower() in special_doc_files):
                doc_files += 1
                doc_bytes += size
            # 其他类型文件不计入代码或文档统计
    
    dir_count = len(directory_paths)

    # 计算比例（避免除零错误）
    code_to_doc_ratio = 0.0
    if doc_files > 0:
        code_to_doc_ratio = code_files / doc_files
    
    bytes_ratio = 0.0
    if doc_bytes > 0:
        bytes_ratio = code_bytes / doc_bytes
    
    # 计算深度统计
    max_depth = max(depths) if depths else 0
    avg_depth = sum(depths) / len(depths) if depths else 0.0
    
    # 检测特殊文件
    has_entry_point = _has_entry_point(normalized_items)
    has_tests = _has_tests(normalized_items)
    has_config_files = _has_config_files(normalized_items)
    has_ci_cd = _has_ci_cd(normalized_items)
    license_file_present = _has_license_file(normalized_items)
    
    # 计算README质量评分（简化版）
    readme_quality_score = _calculate_readme_quality(repo_data)
    
    # 计算综合结构评分（简化版）
    structure_score = _calculate_structure_score(
        code_files, doc_files, code_to_doc_ratio, 
        max_depth, has_entry_point, has_tests, 
        has_config_files, license_file_present
    )
    
    return {
        "file_count": file_count,
        "dir_count": dir_count,
        "code_files": code_files,
        "doc_files": doc_files,
        "code_to_doc_ratio": code_to_doc_ratio,
        "code_bytes": code_bytes,
        "doc_bytes": doc_bytes,
        "bytes_ratio": bytes_ratio,
        "max_depth": max_depth,
        "avg_depth": avg_depth,
        "file_type_distribution": file_type_distribution,
        "has_entry_point": has_entry_point,
        "has_tests": has_tests,
        "has_config_files": has_config_files,
        "has_ci_cd": has_ci_cd,
        "license_file_present": license_file_present,
        "readme_quality_score": readme_quality_score,
        "structure_score": structure_score
    }


def _normalize_item_type(item_type: Any) -> str | None:
    """兼容GitHub原始类型和SPEC类型。"""
    if item_type in {"blob", "file"}:
        return "file"
    if item_type in {"tree", "dir"}:
        return "dir"
    return None


def _collect_directory_paths(directory_paths: set[str], path: str, item_type: str) -> None:
    """从文件或目录路径中提取全部目录层级。"""
    if item_type == "dir":
        if path:
            directory_paths.add(path)
        current = os.path.dirname(path)
    else:
        current = os.path.dirname(path)

    while current:
        directory_paths.add(current)
        current = os.path.dirname(current)


def _has_entry_point(file_tree: List[Dict[str, Any]]) -> bool:
    """检查是否存在入口点文件"""
    entry_points = {
        'main.py', 'app.py', 'application.py', 'index.py', 'run.py',
        'main.js', 'app.js', 'index.js', 'server.js',
        'Main.java', 'Application.java',
        'main.go', 'main.rs', 'main.cpp', 'main.c',
        'setup.py', 'manage.py', 'wsgi.py', 'asgi.py',
        'Makefile', 'makefile', 'CMakeLists.txt'
    }
    
    for item in file_tree:
        if item.get('type') == 'file':
            filename = os.path.basename(item.get('path', ''))
            if filename in entry_points:
                return True
    return False


def _has_tests(file_tree: List[Dict[str, Any]]) -> bool:
    """检查是否存在测试文件"""
    test_indicators = [
        'test', 'tests', '__test__', '__tests__',
        'spec', 'specs'
    ]
    
    for item in file_tree:
        if item.get('type') == 'file':
            path = item.get('path', '').lower()
            # 检查路径中是否包含测试相关目录
            if any(indicator in path for indicator in test_indicators):
                return True
            # 检查文件名是否以test开头或结尾
            filename = os.path.basename(path)
            if filename.startswith('test_') or filename.endswith('_test.py'):
                return True
            if filename.endswith('.test.js') or filename.endswith('.spec.js'):
                return True
    return False


def _has_config_files(file_tree: List[Dict[str, Any]]) -> bool:
    """检查是否存在配置文件"""
    config_files = {
        'requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock',
        'package.json', 'package-lock.json', 'yarn.lock',
        'pom.xml', 'build.gradle', 'Cargo.toml', 'go.mod',
        'composer.json', 'Gemfile', 'mix.exs',
        '.gitignore', '.dockerignore', '.env',
        'config.ini', 'config.json', 'config.yaml', 'config.yml',
        'settings.py', 'settings.json', 'settings.yaml'
    }
    
    for item in file_tree:
        if item.get('type') == 'file':
            filename = os.path.basename(item.get('path', ''))
            if filename in config_files:
                return True
    return False


def _has_ci_cd(file_tree: List[Dict[str, Any]]) -> bool:
    """检查是否存在CI/CD配置"""
    ci_cd_indicators = [
        '.github/', '.gitlab-ci.yml', '.travis.yml',
        'Jenkinsfile', 'jenkins.yml', 'circleci',
        'azure-pipelines.yml', 'bitbucket-pipelines.yml'
    ]
    
    for item in file_tree:
        if item.get('type') == 'file':
            path = item.get('path', '')
            for indicator in ci_cd_indicators:
                if indicator in path:
                    return True
        elif item.get('type') == 'dir':
            path = item.get('path', '')
            # 检查是否是CI/CD目录
            if path in ['.github', '.circleci'] or path.startswith('.github/workflows'):
                return True
    return False


def _has_license_file(file_tree: List[Dict[str, Any]]) -> bool:
    """检查是否存在许可证文件"""
    license_files = {
        'LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING',
        'COPYING.txt', 'COPYRIGHT', 'NOTICE'
    }
    
    for item in file_tree:
        if item.get('type') == 'file':
            filename = os.path.basename(item.get('path', '')).upper()
            if filename in license_files:
                return True
    return False


def _calculate_readme_quality(repo_data: Dict[str, Any]) -> float:
    """计算README质量评分（简化版）"""
    readme_content = repo_data.get('readme_content', '')
    if not readme_content:
        return 0.0
    
    score = 0.0
    # 基本长度得分
    if len(readme_content) > 100:
        score += 0.3
    if len(readme_content) > 500:
        score += 0.2
    
    # 检查是否包含常见部分
    sections = ['# ', '## ', 'installation', 'usage', 'example', 'contributing', 'license']
    content_lower = readme_content.lower()
    found_sections = sum(1 for section in sections if section in content_lower)
    score += min(0.3, found_sections * 0.05)
    
    # 检查是否有代码示例
    if '```' in readme_content:
        score += 0.2
    
    return min(1.0, score)


def _calculate_structure_score(code_files: int, doc_files: int, 
                              code_to_doc_ratio: float, max_depth: int,
                              has_entry_point: bool, has_tests: bool,
                              has_config_files: bool, license_file_present: bool) -> float:
    """计算综合结构评分（简化版）"""
    score = 0.0
    
    # 文件数量得分（有代码文件才得分）
    if code_files > 0:
        score += 0.2
        # 代码文件数量适中得分
        if 5 <= code_files <= 50:
            score += 0.1
    
    # 代码/文档比例得分（理想比例在1:1到10:1之间）
    if code_files > 0 and doc_files > 0:
        if 0.1 <= code_to_doc_ratio <= 10.0:
            score += 0.2
    elif code_files > 0 and doc_files == 0:
        # 只有代码没有文档，适中得分
        score += 0.1
    
    # 目录深度得分（不过深也不浅）
    if 1 <= max_depth <= 3:
        score += 0.1
    elif max_depth == 0:
        score += 0.05  # 只有一层目录
    
    # 特殊文件存在得分
    if has_entry_point:
        score += 0.1
    if has_tests:
        score += 0.15
    if has_config_files:
        score += 0.1
    if license_file_present:
        score += 0.1
    
    return min(1.0, score)


# 为了便于直接运行测试，提供一个简单的测试函数
if __name__ == "__main__":
    # 简单测试
    test_data = {
        "repo_url": "https://github.com/octocat/Hello-World",
        "readme_content": "# Hello-World\\n\\nThis is a test repository.",
        "file_tree": [
            {"path": "README.md", "type": "blob", "size": 1024},
            {"path": "src/main.py", "type": "blob", "size": 2048},
            {"path": "src/utils.py", "type": "blob", "size": 1024},
            {"path": "tests/test_main.py", "type": "blob", "size": 512},
            {"path": "requirements.txt", "type": "blob", "size": 128},
            {"path": "LICENSE", "type": "blob", "size": 1024}
        ]
    }
    
    try:
        result = analyze_repo_structure(test_data)
        print("Structure analysis completed successfully:")
        print(f"File count: {result['file_count']}")
        print(f"Code files: {result['code_files']}")
        print(f"Doc files: {result['doc_files']}")
        print(f"Code to doc ratio: {result['code_to_doc_ratio']:.2f}")
        print(f"Structure score: {result['structure_score']:.2f}")
    except Exception as e:
        print(f"Error analyzing repo structure: {e}")
