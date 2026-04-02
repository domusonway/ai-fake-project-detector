import pytest
from unittest.mock import Mock, patch
import sys
import os
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.repo_ingestion.repo_ingestion import fetch_repo_basic_info, GitHubAPIError
from .fixtures import build_repo_ingestion_payloads

@patch('modules.repo_ingestion.requests.get')
def test_fetch_repo_basic_info_valid_url(mock_get):
    """测试有效的GitHub URL"""
    payloads = build_repo_ingestion_payloads("substantive")

    # 配置mock响应
    mock_repo_response = Mock()
    mock_repo_response.status_code = 200
    mock_repo_response.json.return_value = payloads["repo"]
    
    mock_readme_response = Mock()
    mock_readme_response.status_code = 200
    mock_readme_response.text = payloads["readme"]
    
    mock_tree_response = Mock()
    mock_tree_response.status_code = 200
    mock_tree_response.json.return_value = {"tree": payloads["tree"]}
    
    mock_languages_response = Mock()
    mock_languages_response.status_code = 200
    mock_languages_response.json.return_value = payloads["languages"]
    
    # 设置mock.get的side_effect来返回不同的响应
    mock_get.side_effect = [
        mock_repo_response,      # 首先是获取仓库信息 (api_base)
        mock_readme_response,    # 然后是获取README (api_base/readme)
        mock_repo_response,      # 再次获取默认分支 (api_base) - 复用仓库信息响应
        mock_tree_response,      # 然后是获取文件树 (api_base/git/trees/{default_branch}?recursive=1)
        mock_languages_response  # 最后是获取语言 (api_base/languages)
    ]
    
    # 调用函数
    result = fetch_repo_basic_info("https://github.com/octocat/Hello-World")
    
    # 验证结果
    assert result["repo_url"] == "https://github.com/octocat/Hello-World"
    assert result["owner"] == "octocat"
    assert result["name"] == "Hello-World"
    assert result["readme_content"] == payloads["readme"]
    assert len(result["file_tree"]) == len(payloads["tree"])
    assert all(item["type"] in {"file", "dir"} for item in result["file_tree"])
    assert result["default_branch"] == payloads["repo"]["default_branch"]
    assert result["is_fork"] is False
    assert result["size"] == payloads["repo"]["size"]
    assert result["language"] == payloads["repo"]["language"]
    assert result["stargazers_count"] == payloads["repo"]["stargazers_count"]
    assert result["forks_count"] == payloads["repo"]["forks_count"]
    assert result["open_issues_count"] == payloads["repo"]["open_issues_count"]
    assert result["topics"] == payloads["repo"]["topics"]
    license_info = payloads["repo"]["license"]
    assert license_info is not None
    assert result["license"]["key"] == license_info["key"]
    assert result["description"] == payloads["repo"]["description"]
    assert result["homepage"] == payloads["repo"]["homepage"]

@patch('modules.repo_ingestion.requests.get')
def test_fetch_repo_basic_info_invalid_url(mock_get):
    """测试无效的GitHub URL"""
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        fetch_repo_basic_info("https://example.com/octocat/Hello-World")
    
    # 确保没有发出网络请求
    mock_get.assert_not_called()

@patch('modules.repo_ingestion.requests.get')
def test_fetch_repo_basic_info_network_error(mock_get):
    """测试网络错误"""
    mock_get.side_effect = Exception("Network error")
    
    with pytest.raises(ConnectionError, match="Network request failed"):
        fetch_repo_basic_info("https://github.com/octocat/Hello-World")

@patch('modules.repo_ingestion.requests.get')
def test_fetch_repo_basic_info_github_api_error(mock_get):
    """测试GitHub API错误"""
    from requests.exceptions import HTTPError
    
    mock_response = Mock()
    mock_response.status_code = 404
    # Create a proper HTTPError with response attribute
    http_error = HTTPError("404 Client Error")
    http_error.response = mock_response
    mock_response.raise_for_status.side_effect = http_error
    mock_get.return_value = mock_response
    
    with pytest.raises(GitHubAPIError) as exc_info:
        fetch_repo_basic_info("https://github.com/octocat/Non-Existent-Repo")
    
    assert exc_info.value.status_code == 404
