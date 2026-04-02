import os
import sys
from typing import Any, TypedDict, cast

import pytest
# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.peer_retrieval.peer_retrieval import retrieve_similar_projects
from .fixtures import retrieval_candidate_projects, retrieval_target_features


class RetrievalResult(TypedDict):
    repo_url: str
    cohort: str
    similarity_score: float
    match_explanation: dict[str, float]
    retrieval_metadata: dict[str, Any]

TARGET_FEATURES = retrieval_target_features()
CANDIDATE_PROJECTS = retrieval_candidate_projects()

def test_retrieve_similar_projects_rule_strategy_returns_comparable_peers_first():
    result = retrieve_similar_projects(
        target_features=TARGET_FEATURES,
        candidate_projects=CANDIDATE_PROJECTS,
        top_k=3,
        strategy="rule"
    )
    typed_result = cast(list[RetrievalResult], result)
    
    assert len(typed_result) == 3
    assert typed_result[0]["cohort"] == "early_but_real"
    assert typed_result[1]["cohort"] == "substantive"
    assert typed_result[2]["cohort"] == "hype_heavy"

    assert typed_result[0]["similarity_score"] > typed_result[1]["similarity_score"] > typed_result[2]["similarity_score"]

    assert all(0.0 <= item["similarity_score"] <= 1.0 for item in typed_result)

    assert all("match_explanation" in item for item in typed_result)
    assert typed_result[0]["retrieval_metadata"]["comparable"] is True
    assert typed_result[1]["retrieval_metadata"]["comparable"] is True
    assert typed_result[2]["retrieval_metadata"]["comparable"] is False
    assert typed_result[2]["retrieval_metadata"]["comparability_bucket"] == "fallback"
    assert typed_result[2]["retrieval_metadata"]["fallback_reason"] == "insufficient_comparable_peers"
    assert typed_result[0]["retrieval_metadata"]["confidence"] == "medium"


def test_retrieve_similar_projects_same_category_results_stay_primary_bucket():
    python_candidates = [
        project for project in CANDIDATE_PROJECTS if project["language"] == "Python"
    ]

    result = retrieve_similar_projects(
        target_features=TARGET_FEATURES,
        candidate_projects=python_candidates,
        top_k=2,
        strategy="rule",
    )

    assert [item["cohort"] for item in result] == ["early_but_real", "substantive"]
    assert all(item["retrieval_metadata"]["comparability_bucket"] == "primary" for item in result)
    assert all(item["retrieval_metadata"]["comparable"] is True for item in result)


def test_retrieve_similar_projects_default_strategy_is_rule_first():
    result = retrieve_similar_projects(
        target_features=TARGET_FEATURES,
        candidate_projects=CANDIDATE_PROJECTS,
        top_k=3,
    )

    assert len(result) == 3
    assert all("match_explanation" in item for item in result)
    assert all(item["retrieval_metadata"]["requested_strategy"] == "rule" for item in result)
    assert all(item["retrieval_metadata"]["effective_strategy"] == "rule" for item in result)


def test_retrieve_similar_projects_embedding_fallback_to_rule_when_no_vectors():
    result = retrieve_similar_projects(
        target_features=TARGET_FEATURES,
        candidate_projects=CANDIDATE_PROJECTS,
        top_k=3,
        strategy="embedding",
    )

    assert len(result) == 3
    assert all("match_explanation" in item for item in result)
    assert all(item["retrieval_metadata"]["requested_strategy"] == "embedding" for item in result)
    assert all(item["retrieval_metadata"]["effective_strategy"] == "rule" for item in result)
    assert all(item["retrieval_metadata"]["strategy_fallback_reason"] == "missing_embedding_vectors" for item in result)


def test_retrieve_similar_projects_marks_sparse_low_confidence_when_too_few_peers_exist():
    sparse_candidates = [
        project for project in CANDIDATE_PROJECTS if project["cohort"] in {"early_but_real", "hype_heavy"}
    ]

    result = retrieve_similar_projects(
        target_features=TARGET_FEATURES,
        candidate_projects=sparse_candidates,
        top_k=2,
        strategy="rule",
    )

    assert [item["cohort"] for item in result] == ["early_but_real", "hype_heavy"]
    assert all(item["retrieval_metadata"]["sparse_peer"] is True for item in result)
    assert all(item["retrieval_metadata"]["confidence"] == "low" for item in result)
    assert all(item["retrieval_metadata"]["comparable_peer_count"] == 1 for item in result)
    assert all("disclosure" in item["retrieval_metadata"] for item in result)

def test_retrieve_similar_projects_empty_candidates():
    """测试空候选列表"""
    result = retrieve_similar_projects(
        target_features=TARGET_FEATURES,
        candidate_projects=[],
        top_k=10,
        strategy="rule"
    )
    
    assert result == []

def test_retrieve_similar_projects_top_k_larger_than_candidates():
    """测试top_k大于候选项目数量"""
    result = retrieve_similar_projects(
        target_features=TARGET_FEATURES,
        candidate_projects=CANDIDATE_PROJECTS,
        top_k=5,
        strategy="rule"
    )
    
    assert len(result) == 3  # 应该只返回实际的候选项目数量
    assert result[0]["similarity_score"] > result[1]["similarity_score"] > result[2]["similarity_score"]

def test_retrieve_similar_projects_invalid_strategy():
    """测试无效策略"""
    with pytest.raises(ValueError, match="Unsupported strategy"):
        retrieve_similar_projects(
            target_features=TARGET_FEATURES,
            candidate_projects=CANDIDATE_PROJECTS,
            top_k=2,
            strategy="invalid_strategy"
        )

def test_retrieve_similar_projects_missing_features():
    """测试缺少必要特征"""
    incomplete_target = dict(TARGET_FEATURES)
    incomplete_target.pop("code_to_doc_ratio")
    
    with pytest.raises(KeyError):
        retrieve_similar_projects(
            target_features=incomplete_target,
            candidate_projects=CANDIDATE_PROJECTS,
            top_k=2,
            strategy="rule"
        )

def test_retrieve_similar_projects_invalid_input():
    """测试无效输入"""
    # target_features不是字典
    with pytest.raises(ValueError, match="target_features must be a dictionary"):
        retrieve_similar_projects(
            target_features="invalid",
            candidate_projects=CANDIDATE_PROJECTS,
            top_k=2,
            strategy="rule"
        )
    
    # candidate_projects不是列表
    with pytest.raises(ValueError, match="candidate_projects must be a list"):
        retrieve_similar_projects(
            target_features=TARGET_FEATURES,
            candidate_projects="invalid",
            top_k=2,
            strategy="rule"
        )
    
    # candidate_projects的元素不是字典
    with pytest.raises(ValueError, match="Each candidate project must be a dictionary"):
        retrieve_similar_projects(
            target_features=TARGET_FEATURES,
            candidate_projects=["invalid"],
            top_k=2,
            strategy="rule"
        )

if __name__ == "__main__":
    test_retrieve_similar_projects_rule_strategy_returns_comparable_peers_first()
    test_retrieve_similar_projects_same_category_results_stay_primary_bucket()
    test_retrieve_similar_projects_default_strategy_is_rule_first()
    test_retrieve_similar_projects_embedding_fallback_to_rule_when_no_vectors()
    test_retrieve_similar_projects_marks_sparse_low_confidence_when_too_few_peers_exist()
    test_retrieve_similar_projects_empty_candidates()
    test_retrieve_similar_projects_top_k_larger_than_candidates()
    test_retrieve_similar_projects_invalid_strategy()
    test_retrieve_similar_projects_missing_features()
    test_retrieve_similar_projects_invalid_input()
    print("All tests passed!")
