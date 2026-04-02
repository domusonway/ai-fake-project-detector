"""
repo-ingestion模块实现
负责接收GitHub仓库URL输入，进行基础抓取和初步处理
"""
import re
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse


class GitHubAPIError(Exception):
    """GitHub API错误"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


def fetch_repo_basic_info(repo_url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    从GitHub获取仓库的基本信息，包括README内容、文件结构等基础数据。
    
    Args:
        repo_url: GitHub仓库URL，格式为https://github.com/owner/repo
        timeout: 请求超时时间（秒）
    
    Returns:
        包含仓库基本信息的字典
    
    Raises:
        ValueError: 当repo_url格式无效时
        ConnectionError: 当网络请求失败时
        GitHubAPIError: 当GitHub API返回错误时
    """
    # 验证URL格式
    if not _is_valid_github_url(repo_url):
        raise ValueError("Invalid GitHub URL")
    
    # 解析URL获取owner和repo
    owner, repo = _parse_github_url(repo_url)
    
    # 构建API URL
    api_base = f"https://api.github.com/repos/{owner}/{repo}"
    
    try:
        # 获取仓库基本信息
        repo_response = requests.get(api_base, timeout=timeout)
        repo_response.raise_for_status()
        repo_data = repo_response.json()
        
        # 获取README内容
        readme_content = _get_readme_content(api_base, timeout)
        
        # 获取文件树结构
        file_tree = _get_file_tree(api_base, timeout)
        
        # 获取语言信息
        languages = _get_languages(api_base, timeout)
        
        # 构建返回结果
        result = {
            "repo_url": repo_url,
            "owner": owner,
            "name": repo,
            "readme_content": readme_content or "",
            "file_tree": file_tree,
            "default_branch": repo_data.get("default_branch", ""),
            "is_fork": repo_data.get("fork", False),
            "created_at": repo_data.get("created_at", ""),
            "updated_at": repo_data.get("updated_at", ""),
            "size": repo_data.get("size", 0),
            "language": repo_data.get("language", ""),
            "languages": languages,
            "stargazers_count": repo_data.get("stargazers_count", 0),
            "forks_count": repo_data.get("forks_count", 0),
            "open_issues_count": repo_data.get("open_issues_count", 0),
            "topics": repo_data.get("topics", []),
            "license": _parse_license(repo_data.get("license")),
            "description": repo_data.get("description", ""),
            "homepage": repo_data.get("homepage")
        }
        
        return result
    except requests.exceptions.RequestException as e:
        if hasattr(e.response, 'status_code'):
            raise GitHubAPIError(str(e), e.response.status_code)
        else:
            raise ConnectionError(f"Network request failed: {str(e)}")
    except Exception as e:
        # 重新抛出已知的异常类型
        if isinstance(e, (ValueError, ConnectionError, GitHubAPIError)):
            raise
        else:
            # 检查是否是带有status_code的GitHubAPIError
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                raise GitHubAPIError(str(e), e.response.status_code)
            else:
                # 将其他异常视为网络错误
                raise ConnectionError(f"Network request failed: {str(e)}")


def _is_valid_github_url(url: str) -> bool:
    """验证GitHub URL格式"""
    pattern = r'^https://github\.com/[\w.-]+/[\w.-]+/?$'
    return bool(re.match(pattern, url.rstrip('/')))


def _parse_github_url(url: str) -> tuple:
    """解析GitHub URL获取owner和repo"""
    parsed = urlparse(url.rstrip('/'))
    if parsed.hostname != 'github.com':
        raise ValueError("Invalid GitHub URL")
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) >= 2:
        return path_parts[0], path_parts[1]
    else:
        raise ValueError("Invalid GitHub URL format")


def _get_readme_content(api_base: str, timeout: int) -> Optional[str]:
    """获取README内容"""
    try:
        # 尝试常见的README文件名
        readme_names = ['README.md', 'README.rst', 'README.txt', 'README']
        for readme_name in readme_names:
            readme_url = f"{api_base}/readme"
            headers = {'Accept': 'application/vnd.github.v3.raw'}
            response = requests.get(readme_url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.text
        return None
    except Exception:
        return None


def _get_file_tree(api_base: str, timeout: int) -> List[Dict[str, Any]]:
    """获取文件树结构"""
    try:
        # 获取默认分支
        branch_response = requests.get(f"{api_base}", timeout=timeout)
        branch_response.raise_for_status()
        default_branch = branch_response.json().get('default_branch', 'main')
        
        # 获取文件树
        tree_url = f"{api_base}/git/trees/{default_branch}?recursive=1"
        tree_response = requests.get(tree_url, timeout=timeout)
        tree_response.raise_for_status()
        tree_data = tree_response.json()
        
        file_tree = []
        for item in tree_data.get('tree', []):
            # 只包括文件和目录
            if item['type'] in ['blob', 'tree']:
                file_info = {
                    'path': item['path'],
                    'type': 'file' if item['type'] == 'blob' else 'dir',
                    'size': item.get('size', 0)
                }
                file_tree.append(file_info)
        
        return file_tree
    except Exception:
        # 如果无法获取详细文件树，返回基本信息
        return []


def _get_languages(api_base: str, timeout: int) -> Dict[str, int]:
    """获取语言统计"""
    try:
        lang_url = f"{api_base}/languages"
        lang_response = requests.get(lang_url, timeout=timeout)
        lang_response.raise_for_status()
        return lang_response.json()
    except Exception:
        return {}


def _parse_license(license_data: Optional[Dict]) -> Optional[Dict]:
    """解析许可证信息"""
    if not license_data:
        return None
    
    return {
        'key': license_data.get('key'),
        'name': license_data.get('name'),
        'spdx_id': license_data.get('spdx_id')
    }


# 为了便于直接运行测试，提供一个简单的测试函数
if __name__ == "__main__":
    # 简单测试
    test_url = "https://github.com/octocat/Hello-World"
    try:
        result = fetch_repo_basic_info(test_url, timeout=5)
        print(f"Successfully fetched info for {test_url}")
        print(f"Repository: {result['owner']}/{result['name']}")
        print(f"Description: {result['description']}")
        print(f"Stars: {result['stargazers_count']}")
    except Exception as e:
        print(f"Error fetching repo info: {e}")
