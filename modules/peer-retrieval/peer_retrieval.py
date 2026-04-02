import math
from typing import Literal, NotRequired, TypedDict, cast


class ProjectFeatures(TypedDict):
    code_to_doc_ratio: float
    bytes_ratio: float
    max_depth: int
    has_entry_point: bool
    has_tests: bool
    has_config_files: bool
    has_ci_cd: bool
    license_file_present: bool
    file_type_distribution: dict[str, int]
    language: str
    stargazers_count: int
    embedding_vector: NotRequired[list[float]]


class CandidateProject(ProjectFeatures):
    repo_url: str
    cohort: str


class RetrievalMetadata(TypedDict):
    requested_strategy: str
    effective_strategy: str
    strategy_fallback_reason: str | None
    comparable: bool
    comparability_bucket: Literal["primary", "fallback"]
    comparability_score: float
    comparable_peer_count: int
    sample_size: int
    sparse_peer: bool
    low_confidence_peer: bool
    confidence: Literal["low", "medium", "high"]
    fallback_reason: str | None
    disclosure: str
    rank: int


class RetrievalResult(CandidateProject):
    similarity_score: float
    match_explanation: dict[str, float]
    retrieval_metadata: RetrievalMetadata


class ScoredCandidate(TypedDict):
    project: CandidateProject
    similarity_score: float
    match_explanation: dict[str, float]
    comparability_score: float
    comparable: bool


FEATURE_WEIGHTS: dict[str, float] = {
    "code_to_doc_ratio": 0.15,
    "bytes_ratio": 0.15,
    "max_depth": 0.1,
    "has_entry_point": 0.05,
    "has_tests": 0.1,
    "has_config_files": 0.05,
    "has_ci_cd": 0.05,
    "license_file_present": 0.05,
    "file_type_distribution": 0.2,
    "language": 0.1,
    "stargazers_count": 0.1,
}

COMPARABILITY_WEIGHTS: dict[str, float] = {
    "language": 0.45,
    "has_entry_point": 0.1,
    "has_tests": 0.1,
    "has_config_files": 0.05,
    "has_ci_cd": 0.05,
    "license_file_present": 0.05,
    "file_type_distribution": 0.2,
}

SUPPORTED_STRATEGIES = {"rule", "embedding", "hybrid"}


def retrieve_similar_projects(
    target_features: object,
    candidate_projects: object,
    top_k: int = 10,
    strategy: str = "rule",
) -> list[RetrievalResult]:
    if not isinstance(target_features, dict):
        raise ValueError("target_features must be a dictionary")

    if not isinstance(candidate_projects, list):
        raise ValueError("candidate_projects must be a list")

    for index, project in enumerate(candidate_projects):
        if not isinstance(project, dict):
            raise ValueError(f"Each candidate project must be a dictionary, but item {index} is {type(project)}")

    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy}. Supported strategies are: rule, embedding, hybrid")

    if not candidate_projects or top_k <= 0:
        return []

    typed_target_features = cast(ProjectFeatures, cast(object, target_features))
    typed_candidate_projects = cast(list[CandidateProject], cast(object, candidate_projects))
    required_features = list(FEATURE_WEIGHTS.keys())
    _validate_required_features(typed_target_features, typed_candidate_projects, required_features)

    requested_strategy = strategy
    effective_strategy = strategy
    strategy_fallback_reason: str | None = None

    has_embeddings = _has_embedding_vectors(typed_target_features, typed_candidate_projects)
    if strategy in {"embedding", "hybrid"} and not has_embeddings:
        effective_strategy = "rule"
        strategy_fallback_reason = "missing_embedding_vectors"

    scored_candidates: list[ScoredCandidate] = []
    for project in typed_candidate_projects:
        rule_similarity = _calculate_rule_similarity(typed_target_features, project, FEATURE_WEIGHTS)
        embedding_similarity = _calculate_embedding_similarity(typed_target_features, project) if has_embeddings else 0.0
        similarity_score = _select_similarity(rule_similarity, embedding_similarity, effective_strategy)
        match_explanation = _calculate_rule_explanation(typed_target_features, project, FEATURE_WEIGHTS)
        comparability_score = _calculate_rule_similarity(typed_target_features, project, COMPARABILITY_WEIGHTS)
        comparable = _is_comparable(typed_target_features, project, comparability_score)

        scored_candidates.append(
            {
                "project": project,
                "similarity_score": similarity_score,
                "match_explanation": match_explanation,
                "comparability_score": comparability_score,
                "comparable": comparable,
            }
        )

    comparable_candidates = [item for item in scored_candidates if item["comparable"]]
    fallback_candidates = [item for item in scored_candidates if not item["comparable"]]

    comparable_candidates.sort(key=lambda item: (-item["similarity_score"], item["project"]["repo_url"]))
    fallback_candidates.sort(key=lambda item: (-item["similarity_score"], item["project"]["repo_url"]))

    selected = (comparable_candidates + fallback_candidates)[: min(top_k, len(scored_candidates))]
    comparable_peer_count = min(len(comparable_candidates), len(selected))
    sparse_peer = comparable_peer_count < 3
    top_comparable_similarity = comparable_candidates[0]["similarity_score"] if comparable_candidates else 0.0
    confidence = _determine_confidence(comparable_peer_count, top_comparable_similarity)
    low_confidence_peer = confidence == "low" or top_comparable_similarity < 0.35
    disclosure = _build_disclosure(comparable_peer_count, sparse_peer, low_confidence_peer)

    result: list[RetrievalResult] = []
    for rank, item in enumerate(selected, start=1):
        source_project = item["project"]
        retrieval_metadata: RetrievalMetadata = {
            "requested_strategy": requested_strategy,
            "effective_strategy": effective_strategy,
            "strategy_fallback_reason": strategy_fallback_reason,
            "comparable": item["comparable"],
            "comparability_bucket": "primary" if item["comparable"] else "fallback",
            "comparability_score": round(item["comparability_score"], 6),
            "comparable_peer_count": comparable_peer_count,
            "sample_size": comparable_peer_count,
            "sparse_peer": sparse_peer,
            "low_confidence_peer": low_confidence_peer,
            "confidence": confidence,
            "fallback_reason": None if item["comparable"] else "insufficient_comparable_peers",
            "disclosure": disclosure,
            "rank": rank,
        }
        result_item: RetrievalResult = {
            "repo_url": source_project["repo_url"],
            "cohort": source_project["cohort"],
            "code_to_doc_ratio": source_project["code_to_doc_ratio"],
            "bytes_ratio": source_project["bytes_ratio"],
            "max_depth": source_project["max_depth"],
            "has_entry_point": source_project["has_entry_point"],
            "has_tests": source_project["has_tests"],
            "has_config_files": source_project["has_config_files"],
            "has_ci_cd": source_project["has_ci_cd"],
            "license_file_present": source_project["license_file_present"],
            "file_type_distribution": source_project["file_type_distribution"],
            "language": source_project["language"],
            "stargazers_count": source_project["stargazers_count"],
            "similarity_score": round(item["similarity_score"], 6),
            "match_explanation": item["match_explanation"],
            "retrieval_metadata": retrieval_metadata,
        }
        if "embedding_vector" in source_project:
            result_item["embedding_vector"] = source_project["embedding_vector"]
        result.append(result_item)

    return result


def _validate_required_features(target_features: ProjectFeatures, candidate_projects: list[CandidateProject], required_features: list[str]) -> None:
    for feature in required_features:
        if feature not in target_features:
            raise KeyError(f"Missing required feature in target_features: {feature}")
        for index, project in enumerate(candidate_projects):
            if feature not in project:
                raise KeyError(f"Missing required feature '{feature}' in candidate project {index}")


def _has_embedding_vectors(target_features: ProjectFeatures, candidate_projects: list[CandidateProject]) -> bool:
    target_vector = target_features.get("embedding_vector")
    if target_vector is None or not target_vector:
        return False

    for project in candidate_projects:
        project_vector = project.get("embedding_vector")
        if project_vector is None or not project_vector:
            return False
    return True


def _select_similarity(rule_similarity: float, embedding_similarity: float, effective_strategy: str) -> float:
    if effective_strategy == "embedding":
        return embedding_similarity
    if effective_strategy == "hybrid":
        return (rule_similarity * 0.7) + (embedding_similarity * 0.3)
    return rule_similarity


def _is_comparable(target_features: ProjectFeatures, project_features: CandidateProject, comparability_score: float) -> bool:
    language_match = target_features["language"] == project_features["language"]
    tests_match = target_features["has_tests"] == project_features["has_tests"]
    entry_match = target_features["has_entry_point"] == project_features["has_entry_point"]
    return language_match and comparability_score >= 0.6 and (tests_match or entry_match)


def _determine_confidence(comparable_peer_count: int, top_similarity: float) -> Literal["low", "medium", "high"]:
    if comparable_peer_count <= 1 or top_similarity < 0.35:
        return "low"
    if comparable_peer_count < 3:
        return "medium"
    return "high"


def _build_disclosure(comparable_peer_count: int, sparse_peer: bool, low_confidence_peer: bool) -> str:
    if comparable_peer_count == 0:
        return "No directly comparable peers were found; fallback peers are disclosed for context only."
    if sparse_peer and low_confidence_peer:
        return "Peer baseline is sparse and low confidence; downstream scoring should stay conservative."
    if sparse_peer:
        return "Peer baseline is sparse; fallback peers may appear after primary comparable peers."
    if low_confidence_peer:
        return "Peer baseline confidence is low; compare outcomes conservatively."
    return "Peer baseline is stable enough for downstream comparison."


def _calculate_rule_similarity(
    target_features: ProjectFeatures,
    project_features: CandidateProject,
    feature_weights: dict[str, float],
) -> float:
    similarity = 0.0
    total_weight = 0.0

    for feature, weight in feature_weights.items():
        feature_similarity = _feature_similarity(feature, target_features[feature], project_features[feature])
        similarity += weight * feature_similarity
        total_weight += weight

    if total_weight == 0:
        return 0.0
    return similarity / total_weight


def _calculate_embedding_similarity(target_features: ProjectFeatures, project_features: CandidateProject) -> float:
    target_vector = target_features.get("embedding_vector")
    project_vector = project_features.get("embedding_vector")
    if target_vector is not None and project_vector is not None:
        return _calculate_cosine_similarity(target_vector, project_vector)
    return _calculate_cosine_similarity(_features_to_vector(target_features), _features_to_vector(project_features))


def _features_to_vector(features: ProjectFeatures) -> list[float]:
    vector: list[float] = []

    numeric_values = [
        float(features["code_to_doc_ratio"]),
        float(features["bytes_ratio"]),
        float(features["max_depth"]),
        float(features["stargazers_count"]),
    ]
    for value in numeric_values:
        normalized = min(value / 1000.0, 1.0) if value >= 0 else 0.0
        vector.append(normalized)

    boolean_values = [
        features["has_entry_point"],
        features["has_tests"],
        features["has_config_files"],
        features["has_ci_cd"],
        features["license_file_present"],
    ]
    for value in boolean_values:
        vector.append(1.0 if value else 0.0)

    file_distribution = features["file_type_distribution"]
    sorted_items = sorted(file_distribution.items(), key=lambda item: item[1], reverse=True)
    total_files = sum(file_distribution.values()) or 1
    for index in range(5):
        count = sorted_items[index][1] if index < len(sorted_items) else 0
        vector.append(count / total_files)

    language = features["language"]
    vector.append(sum(ord(char) for char in language) % 1000 / 1000.0)
    return vector


def _calculate_cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if len(vec1) != len(vec2):
        if len(vec1) < len(vec2):
            vec1 = vec1 + [0.0] * (len(vec2) - len(vec1))
        else:
            vec2 = vec2 + [0.0] * (len(vec1) - len(vec2))

    dot_product = sum(left * right for left, right in zip(vec1, vec2))
    norm_left = math.sqrt(sum(value * value for value in vec1))
    norm_right = math.sqrt(sum(value * value for value in vec2))

    if norm_left == 0 or norm_right == 0:
        return 0.0
    return dot_product / (norm_left * norm_right)


def _calculate_cosine_similarity_dict(dict1: dict[str, int], dict2: dict[str, int]) -> float:
    all_keys = set(dict1.keys()) | set(dict2.keys())
    if not all_keys:
        return 1.0

    vec1 = [float(dict1.get(key, 0)) for key in all_keys]
    vec2 = [float(dict2.get(key, 0)) for key in all_keys]
    return _calculate_cosine_similarity(vec1, vec2)


def _calculate_rule_explanation(
    target_features: ProjectFeatures,
    project_features: CandidateProject,
    feature_weights: dict[str, float],
) -> dict[str, float]:
    explanation: dict[str, float] = {}
    for feature in feature_weights:
        explanation[feature] = _feature_similarity(feature, target_features[feature], project_features[feature])
    return explanation


def _feature_similarity(
    feature: str,
    target_value: float | int | bool | str | dict[str, int],
    project_value: float | int | bool | str | dict[str, int],
) -> float:
    if feature in {"code_to_doc_ratio", "bytes_ratio", "stargazers_count"}:
        numeric_target = float(cast(float | int, target_value))
        numeric_project = float(cast(float | int, project_value))
        if numeric_target == 0 and numeric_project == 0:
            return 1.0
        if numeric_target == 0 or numeric_project == 0:
            return 0.0
        return min(numeric_target, numeric_project) / max(numeric_target, numeric_project)

    if feature == "max_depth":
        depth_target = int(cast(float | int, target_value))
        depth_project = int(cast(float | int, project_value))
        max_depth = max(depth_target, depth_project)
        if max_depth == 0:
            return 1.0
        return 1.0 - abs(depth_target - depth_project) / max_depth

    if feature in {"has_entry_point", "has_tests", "has_config_files", "has_ci_cd", "license_file_present", "language"}:
        return 1.0 if target_value == project_value else 0.0

    if feature == "file_type_distribution":
        return _calculate_cosine_similarity_dict(
            cast(dict[str, int], target_value),
            cast(dict[str, int], project_value),
        )

    return 1.0 if target_value == project_value else 0.0
