from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from modules.peer_retrieval.peer_retrieval import retrieve_similar_projects  # pyright: ignore[reportImplicitRelativeImport]
from modules.repo_ingestion.repo_ingestion import GitHubAPIError, fetch_repo_basic_info  # pyright: ignore[reportImplicitRelativeImport]
from modules.scoring_engine.scoring_engine import compute_fake_risk_score  # pyright: ignore[reportImplicitRelativeImport]
from modules.structure_analyzer.structure_analyzer import analyze_repo_structure  # pyright: ignore[reportImplicitRelativeImport]
from services.persistence import PersistenceStore  # pyright: ignore[reportImplicitRelativeImport]


CANONICAL_V1_SURFACE = "flask_app.py"
CANONICAL_V1_DESCRIPTION = "Flask web app + JSON API"
DEFAULT_ANALYSIS_DB_PATH = Path(__file__).resolve().parent / "data" / "analysis.sqlite3"
DEFAULT_PEER_TOP_K = 5
DEFAULT_RETRIEVAL_STRATEGY = "rule"


def analyze_repository(
    repo_url: str,
    *,
    store: PersistenceStore | None = None,
    candidate_projects: Sequence[Mapping[str, object]] | None = None,
    analyzed_at: str | None = None,
) -> dict[str, object]:
    normalized_repo_url = _normalize_repo_url(repo_url)
    persistence_store = store or get_persistence_store()

    repo_data = fetch_repo_basic_info(normalized_repo_url, timeout=10)
    structure_result = analyze_repo_structure(repo_data)
    project_features = build_project_features(repo_data, structure_result)

    peer_candidates = _resolve_peer_candidates(
        persistence_store,
        normalized_repo_url,
        candidate_projects=candidate_projects,
    )
    selected_peers = retrieve_similar_projects(
        target_features=project_features,
        candidate_projects=peer_candidates,
        top_k=DEFAULT_PEER_TOP_K,
        strategy=DEFAULT_RETRIEVAL_STRATEGY,
    )
    peer_baseline = build_peer_baseline(selected_peers)

    scoring_result = compute_fake_risk_score(
        project_features=project_features,
        peer_baseline=peer_baseline,
    )

    snapshot_at = analyzed_at or _utc_now_isoformat()
    repo_identity = build_repo_identity(normalized_repo_url, repo_data)
    peer_retrieval = build_peer_retrieval_payload(selected_peers, peer_baseline)
    report_snapshot = {
        **scoring_result,
        "snapshot_at": snapshot_at,
        "repo_url": normalized_repo_url,
        "repo_info": build_repo_info(normalized_repo_url, repo_data),
        "structure_analysis": dict(structure_result),
        "project_features": project_features,
        "peer_retrieval": peer_retrieval,
    }
    ranking_inputs = build_ranking_inputs(repo_data, scoring_result)
    persisted = persistence_store.record_analysis(
        repo_identity=repo_identity,
        report_snapshot=report_snapshot,
        ranking_inputs=ranking_inputs,
    )

    return {
        "repo_identity": {
            **repo_identity,
            "repo_id": persisted["repo_id"],
        },
        "repo_info": report_snapshot["repo_info"],
        "structure_analysis": structure_result,
        "peer_retrieval": peer_retrieval,
        "scoring_result": scoring_result,
        "snapshot": {
            "snapshot_id": persisted["snapshot_id"],
            "snapshot_version": persisted["snapshot_version"],
            "snapshot_at": snapshot_at,
            "scoring_version": scoring_result["version"],
        },
        "runtime_surface": {
            "primary": CANONICAL_V1_DESCRIPTION,
            "entrypoint": CANONICAL_V1_SURFACE,
        },
    }


def get_persistence_store(db_path: str | Path | None = None) -> PersistenceStore:
    resolved_path = Path(db_path or os.environ.get("AI_FAKE_PROJECT_DB_PATH") or DEFAULT_ANALYSIS_DB_PATH)
    return PersistenceStore(resolved_path)


def build_repo_identity(repo_url: str, repo_data: Mapping[str, object]) -> dict[str, str]:
    return {
        "repo_url": repo_url,
        "owner": str(repo_data["owner"]),
        "name": str(repo_data["name"]),
        "source": "github",
    }


def build_repo_info(repo_url: str, repo_data: Mapping[str, object]) -> dict[str, object]:
    return {
        "owner": repo_data["owner"],
        "name": repo_data["name"],
        "url": repo_url,
        "description": repo_data.get("description", ""),
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "language": repo_data.get("language", ""),
        "size_kb": repo_data.get("size", 0),
        "created_at": repo_data.get("created_at", ""),
        "updated_at": repo_data.get("updated_at", ""),
    }


def build_project_features(
    repo_data: Mapping[str, object],
    structure_result: Mapping[str, object],
) -> dict[str, object]:
    return {
        "code_to_doc_ratio": structure_result.get("code_to_doc_ratio", 0.0),
        "bytes_ratio": structure_result.get("bytes_ratio", 0.0),
        "max_depth": structure_result.get("max_depth", 0),
        "has_entry_point": structure_result.get("has_entry_point", False),
        "has_tests": structure_result.get("has_tests", False),
        "has_config_files": structure_result.get("has_config_files", False),
        "has_ci_cd": structure_result.get("has_ci_cd", False),
        "license_file_present": structure_result.get("license_file_present", False),
        "file_type_distribution": structure_result.get("file_type_distribution", {}),
        "language": repo_data.get("language", ""),
        "stargazers_count": repo_data.get("stargazers_count", 0),
        "description": repo_data.get("description", ""),
        "size": repo_data.get("size", 0),
    }


def build_peer_baseline(peers: Sequence[Mapping[str, object]]) -> dict[str, object] | None:
    comparable_peers = [peer for peer in peers if _peer_is_comparable(peer)]
    if not comparable_peers:
        return None

    first_meta = _peer_metadata(comparable_peers[0])
    sample_size = len(comparable_peers)
    return {
        "sample_size": sample_size,
        "confidence": first_meta.get("confidence", "low"),
        "sparse_peer": bool(first_meta.get("sparse_peer", sample_size < 3)),
        "low_confidence_peer": bool(first_meta.get("low_confidence_peer", False)),
        "disclosure": str(first_meta.get("disclosure", "Peer baseline is derived from retrieved comparable repositories.")),
        "retrieval_metadata": {
            "sample_size": sample_size,
            "confidence": first_meta.get("confidence", "low"),
            "sparse_peer": bool(first_meta.get("sparse_peer", sample_size < 3)),
            "low_confidence_peer": bool(first_meta.get("low_confidence_peer", False)),
            "disclosure": str(first_meta.get("disclosure", "Peer baseline is derived from retrieved comparable repositories.")),
        },
        "code_to_doc_ratio_mean": _mean_numeric(comparable_peers, "code_to_doc_ratio"),
        "bytes_ratio_mean": _mean_numeric(comparable_peers, "bytes_ratio"),
        "max_depth_mean": _mean_numeric(comparable_peers, "max_depth"),
        "has_entry_point_rate": _mean_boolean(comparable_peers, "has_entry_point"),
        "has_tests_rate": _mean_boolean(comparable_peers, "has_tests"),
        "has_config_files_rate": _mean_boolean(comparable_peers, "has_config_files"),
        "has_ci_cd_rate": _mean_boolean(comparable_peers, "has_ci_cd"),
        "license_file_present_rate": _mean_boolean(comparable_peers, "license_file_present"),
        "stargazers_count_mean": _mean_numeric(comparable_peers, "stargazers_count"),
    }


def build_peer_retrieval_payload(
    selected_peers: Sequence[Mapping[str, object]],
    peer_baseline: Mapping[str, object] | None,
) -> dict[str, object]:
    comparable_count = sum(1 for peer in selected_peers if _peer_is_comparable(peer))
    first_meta = _peer_metadata(selected_peers[0]) if selected_peers else {}
    return {
        "selected_peers": [dict(peer) for peer in selected_peers],
        "peer_baseline": dict(peer_baseline) if peer_baseline is not None else None,
        "retrieval_metadata": {
            "selected_count": len(selected_peers),
            "comparable_count": comparable_count,
            "sample_size": _as_int(first_meta.get("sample_size"), comparable_count),
            "confidence": str(first_meta.get("confidence", "low" if comparable_count == 0 else "medium")),
            "sparse_peer": bool(first_meta.get("sparse_peer", comparable_count < 3)),
            "low_confidence_peer": bool(first_meta.get("low_confidence_peer", comparable_count == 0)),
            "disclosure": str(
                first_meta.get(
                    "disclosure",
                    "No directly comparable peers were found; scoring falls back to conservative peer handling.",
                )
            ),
        },
    }


def build_ranking_inputs(
    repo_data: Mapping[str, object],
    scoring_result: Mapping[str, object],
) -> dict[str, object]:
    repo_name = str(repo_data.get("name", "repository"))
    risk_band = str(scoring_result.get("risk_band", "unknown"))
    return {
        "language": str(repo_data.get("language") or "Unknown"),
        "stargazers_count": _as_int(repo_data.get("stargazers_count"), 0),
        "summary": f"{repo_name} latest analysis is {risk_band.replace('_', ' ')}.",
    }


def _resolve_peer_candidates(
    store: PersistenceStore,
    repo_url: str,
    *,
    candidate_projects: Sequence[Mapping[str, object]] | None,
) -> list[dict[str, object]]:
    if candidate_projects is not None:
        return [dict(project) for project in candidate_projects]
    return store.list_peer_candidates(exclude_repo_url=repo_url)


def _peer_metadata(peer: Mapping[str, object]) -> Mapping[str, object]:
    metadata = peer.get("retrieval_metadata")
    if isinstance(metadata, Mapping):
        return metadata
    return {}


def _peer_is_comparable(peer: Mapping[str, object]) -> bool:
    return bool(_peer_metadata(peer).get("comparable", False))


def _mean_numeric(peers: Sequence[Mapping[str, object]], field: str) -> float:
    if not peers:
        return 0.0
    total = 0.0
    for peer in peers:
        total += _as_float(peer.get(field), 0.0)
    return total / len(peers)


def _mean_boolean(peers: Sequence[Mapping[str, object]], field: str) -> float:
    if not peers:
        return 0.0
    total = 0.0
    for peer in peers:
        total += 1.0 if bool(peer.get(field, False)) else 0.0
    return total / len(peers)


def _normalize_repo_url(repo_url: str) -> str:
    if not isinstance(repo_url, str) or not repo_url.strip():
        raise ValueError("repo_url is required")
    return repo_url.strip().rstrip("/")


def _as_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return int(cast(bool, value))
    if isinstance(value, int):
        return cast(int, value)
    if isinstance(value, float):
        return int(cast(float, value))
    if isinstance(value, str) and value.strip():
        return int(cast(str, value))
    return default


def _as_float(value: object, default: float) -> float:
    if isinstance(value, bool):
        return float(int(cast(bool, value)))
    if isinstance(value, (int, float)):
        return float(cast(int | float, value))
    if isinstance(value, str) and value.strip():
        return float(cast(str, value))
    return default


def _utc_now_isoformat() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "CANONICAL_V1_DESCRIPTION",
    "CANONICAL_V1_SURFACE",
    "DEFAULT_ANALYSIS_DB_PATH",
    "GitHubAPIError",
    "analyze_repository",
    "build_peer_baseline",
    "build_project_features",
    "get_persistence_store",
]
