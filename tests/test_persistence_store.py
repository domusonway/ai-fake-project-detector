import sys
from pathlib import Path
from typing import TypedDict, cast

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.persistence import PersistenceStore, RankingQuery


class AnalysisRecord(TypedDict):
    snapshot_id: str
    repo_id: int
    snapshot_version: int
    repo_url: str


class HistoryRecord(TypedDict):
    snapshot_at: str
    fake_risk_score: float
    risk_level: str
    risk_band: str
    dimension_scores: dict[str, float]
    peer_baseline_meta: dict[str, str | int]
    version: str
    snapshot_id: str
    snapshot_version: int
    language: str
    stargazers_count: int
    summary: str


class RankingItem(TypedDict):
    repo_url: str
    owner: str
    name: str
    snapshot_id: str
    snapshot_version: int
    snapshot_at: str
    latest_fake_risk_score: float
    risk_level: str
    risk_band: str
    language: str
    stargazers_count: int
    summary: str


class RankingResult(TypedDict):
    total: int
    items: list[RankingItem]


class FeedbackRecord(TypedDict):
    feedback_id: str
    actor_identity: str
    feedback_kind: str
    payload: dict[str, str]
    submitted_at: str
    dedupe_window_minutes: int
    dedupe_bucket_start: str


class FeedbackWriteResult(TypedDict):
    feedback_id: str
    created: bool
    dedupe_bucket_start: str


def _repo_identity(repo_url: str, owner: str, name: str) -> dict[str, str]:
    return {
        "repo_url": repo_url,
        "owner": owner,
        "name": name,
        "source": "github",
    }


def _report_snapshot(snapshot_at: str, score: float, version: str = "score-v1") -> dict[str, object]:
    return {
        "snapshot_at": snapshot_at,
        "fake_risk_score": score,
        "risk_level": "medium",
        "risk_band": "moderate_suspicious" if score >= 41 else "mild_suspicious",
        "dimension_scores": {
            "delivery": 10.0,
            "substance": 8.0,
            "evidence": 6.0,
            "peer_gap": 5.0,
            "community": 4.0,
            "hype_gap": 3.0,
        },
        "peer_baseline_meta": {"sample_size": 3, "confidence": "medium"},
        "version": version,
    }


def _ranking_inputs(language: str, stars: int, summary: str) -> dict[str, object]:
    return {
        "language": language,
        "stargazers_count": stars,
        "summary": summary,
    }


def test_record_analysis_appends_history_for_same_repo(tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "history.sqlite3")
    repo = _repo_identity("https://github.com/acme/repo-one", "acme", "repo-one")

    first = cast(
        AnalysisRecord,
        cast(
            object,
            store.record_analysis(
                repo_identity=repo,
                report_snapshot=_report_snapshot("2026-04-01T10:00:00Z", 44.0, version="score-v1"),
                ranking_inputs=_ranking_inputs("Python", 120, "First snapshot"),
            ),
        ),
    )
    second = cast(
        AnalysisRecord,
        cast(
            object,
            store.record_analysis(
                repo_identity=repo,
                report_snapshot=_report_snapshot("2026-04-01T12:00:00Z", 58.0, version="score-v2"),
                ranking_inputs=_ranking_inputs("Python", 180, "Second snapshot"),
            ),
        ),
    )

    history = cast(list[HistoryRecord], cast(object, store.get_repo_history(repo["repo_url"])))

    assert first["repo_id"] == second["repo_id"]
    assert first["snapshot_version"] == 1
    assert second["snapshot_version"] == 2
    assert [item["snapshot_version"] for item in history] == [2, 1]
    assert history[0]["fake_risk_score"] == 58.0
    assert history[1]["fake_risk_score"] == 44.0
    assert history[1]["version"] == "score-v1"


def test_query_rankings_uses_latest_materialized_snapshot(tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "ranking.sqlite3")

    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/openweights", "acme", "openweights"),
        report_snapshot=_report_snapshot("2026-04-01T09:00:00Z", 35.0),
        ranking_inputs=_ranking_inputs("Python", 600, "Structured training toolkit"),
    )
    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/openweights", "acme", "openweights"),
        report_snapshot=_report_snapshot("2026-04-01T11:00:00Z", 52.0),
        ranking_inputs=_ranking_inputs("Python", 640, "Structured training toolkit updated"),
    )
    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/zen/flash-demo", "zen", "flash-demo"),
        report_snapshot=_report_snapshot("2026-04-01T10:30:00Z", 74.0),
        ranking_inputs=_ranking_inputs("TypeScript", 2200, "Flashy launch page and waitlist"),
    )

    result = cast(
        RankingResult,
        cast(
            object,
            store.query_rankings(
                RankingQuery(search="open", languages=("Python",), sort_by="latest_fake_risk_score")
            ),
        ),
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["repo_url"] == "https://github.com/acme/openweights"
    assert item["latest_fake_risk_score"] == 52.0
    assert item["snapshot_version"] == 2
    assert item["language"] == "Python"
    assert item["summary"] == "Structured training toolkit updated"


def test_record_feedback_dedupes_within_window_and_allows_next_window(tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "feedback.sqlite3")
    repo = _repo_identity("https://github.com/acme/repo-one", "acme", "repo-one")
    _ = store.record_analysis(
        repo_identity=repo,
        report_snapshot=_report_snapshot("2026-04-01T10:00:00Z", 44.0),
        ranking_inputs=_ranking_inputs("Python", 120, "First snapshot"),
    )

    first = cast(
        FeedbackWriteResult,
        cast(
            object,
            store.record_feedback(
                repo_url=repo["repo_url"],
                actor_identity="github:user-123",
                feedback_kind="credibility_vote",
                payload={"vote": "support", "note": "Has working demo"},
                submitted_at="2026-04-01T10:05:00Z",
                dedupe_window_minutes=60,
            ),
        ),
    )
    duplicate = cast(
        FeedbackWriteResult,
        cast(
            object,
            store.record_feedback(
                repo_url=repo["repo_url"],
                actor_identity="github:user-123",
                feedback_kind="credibility_vote",
                payload={"vote": "support", "note": "Same actor same hour"},
                submitted_at="2026-04-01T10:40:00Z",
                dedupe_window_minutes=60,
            ),
        ),
    )
    next_window = cast(
        FeedbackWriteResult,
        cast(
            object,
            store.record_feedback(
                repo_url=repo["repo_url"],
                actor_identity="github:user-123",
                feedback_kind="credibility_vote",
                payload={"vote": "support", "note": "Next hour should persist"},
                submitted_at="2026-04-01T11:10:00Z",
                dedupe_window_minutes=60,
            ),
        ),
    )

    feedback = cast(list[FeedbackRecord], cast(object, store.list_feedback(repo["repo_url"])))

    assert first["created"] is True
    assert duplicate["created"] is False
    assert duplicate["feedback_id"] == first["feedback_id"]
    assert next_window["created"] is True
    assert next_window["feedback_id"] != first["feedback_id"]
    assert len(feedback) == 2
    assert feedback[0]["dedupe_bucket_start"] == "2026-04-01T11:00:00Z"
    assert feedback[1]["dedupe_bucket_start"] == "2026-04-01T10:00:00Z"


def test_query_rankings_supports_risk_band_sort_direction_and_pagination(tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "ranking-filters.sqlite3")

    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/alpha", "acme", "alpha"),
        report_snapshot=_report_snapshot("2026-04-01T09:00:00Z", 61.0),
        ranking_inputs=_ranking_inputs("Python", 120, "Alpha summary"),
    )
    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/beta", "acme", "beta"),
        report_snapshot=_report_snapshot("2026-04-01T10:00:00Z", 47.0),
        ranking_inputs=_ranking_inputs("Python", 140, "Beta summary"),
    )
    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/gamma", "acme", "gamma"),
        report_snapshot=_report_snapshot("2026-04-01T11:00:00Z", 52.0),
        ranking_inputs=_ranking_inputs("TypeScript", 90, "Gamma summary"),
    )

    result = cast(
        RankingResult,
        cast(
            object,
            store.query_rankings(
                RankingQuery(
                    languages=("Python",),
                    risk_bands=("moderate_suspicious",),
                    sort_by="snapshot_at",
                    descending=False,
                    limit=1,
                    offset=1,
                )
            ),
        ),
    )

    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert result["items"][0]["repo_url"] == "https://github.com/acme/beta"


def test_list_peer_candidates_uses_latest_analyzed_snapshots_and_excludes_subject_repo(tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "peer-candidates.sqlite3")

    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/subject", "acme", "subject"),
        report_snapshot=_report_snapshot("2026-04-01T09:00:00Z", 44.0),
        ranking_inputs=_ranking_inputs("Python", 120, "Subject snapshot"),
    )
    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/subject", "acme", "subject"),
        report_snapshot=_report_snapshot("2026-04-01T10:00:00Z", 49.0, version="score-v2"),
        ranking_inputs=_ranking_inputs("Python", 150, "Subject snapshot updated"),
    )
    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/peer-one", "acme", "peer-one"),
        report_snapshot={
            **_report_snapshot("2026-04-01T11:00:00Z", 31.0),
            "project_features": {"language": "Python", "has_tests": True, "stargazers_count": 220},
        },
        ranking_inputs=_ranking_inputs("Python", 220, "Peer one snapshot"),
    )
    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/peer-one", "acme", "peer-one"),
        report_snapshot={
            **_report_snapshot("2026-04-01T12:00:00Z", 29.0, version="score-v2"),
            "project_features": {"language": "Python", "has_tests": False, "stargazers_count": 260},
        },
        ranking_inputs=_ranking_inputs("Python", 260, "Peer one latest snapshot"),
    )
    _ = store.record_analysis(
        repo_identity=_repo_identity("https://github.com/acme/peer-two", "acme", "peer-two"),
        report_snapshot={
            **_report_snapshot("2026-04-01T08:00:00Z", 57.0),
            "project_features": {"language": "TypeScript", "has_tests": True, "stargazers_count": 90},
        },
        ranking_inputs=_ranking_inputs("TypeScript", 90, "Peer two snapshot"),
    )

    candidates = store.list_peer_candidates(exclude_repo_url="https://github.com/acme/subject")

    assert [candidate["repo_url"] for candidate in candidates] == [
        "https://github.com/acme/peer-one",
        "https://github.com/acme/peer-two",
    ]
    assert all(candidate["cohort"] == "analyzed_repo" for candidate in candidates)
    assert candidates[0]["has_tests"] is False
    assert candidates[0]["stargazers_count"] == 260
    assert candidates[1]["language"] == "TypeScript"


def test_ranking_query_validates_pagination_contracts(tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "query.sqlite3")

    with pytest.raises(ValueError, match="limit must be positive"):
        _ = store.query_rankings(RankingQuery(limit=0))

    with pytest.raises(ValueError, match="offset cannot be negative"):
        _ = store.query_rankings(RankingQuery(offset=-1))
