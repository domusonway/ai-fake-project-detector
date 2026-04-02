import sys
from pathlib import Path
from typing import Any, TypedDict, cast


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import app_runtime  # pyright: ignore[reportImplicitRelativeImport]
import flask_app  # pyright: ignore[reportImplicitRelativeImport]
from services.persistence import PersistenceStore  # pyright: ignore[reportImplicitRelativeImport]


class SnapshotPayload(TypedDict):
    snapshot_id: str
    snapshot_version: int
    snapshot_at: str
    scoring_version: str


class RepoIdentityPayload(TypedDict):
    repo_id: int
    repo_url: str
    owner: str
    name: str
    source: str


class AnalysisPayload(TypedDict):
    repo_identity: RepoIdentityPayload
    snapshot: SnapshotPayload
    scoring_result: dict[str, Any]
    detail_url: str
    rankings_url: str
    surface_notice: str


class DetailApiPayload(TypedDict):
    success: bool
    repo_url: str
    latest: dict[str, Any]
    history: list[dict[str, Any]]


class FeedbackApiPayload(TypedDict):
    success: bool
    feedback: dict[str, Any]


def _seed_ranked_repo(
    store: PersistenceStore,
    *,
    repo_url: str,
    owner: str,
    name: str,
    language: str,
    score: float,
    snapshot_at: str,
    summary: str,
) -> None:
    _ = store.record_analysis(
        repo_identity={
            "repo_url": repo_url,
            "owner": owner,
            "name": name,
            "source": "github",
        },
        report_snapshot=_detail_report_snapshot(
            snapshot_at,
            score=score,
            version="score-v-rank",
            summary_suffix=name,
        ),
        ranking_inputs={
            "language": language,
            "stargazers_count": 100,
            "summary": summary,
        },
    )


def _repo_data() -> dict[str, object]:
    return {
        "owner": "acme",
        "name": "signal-lab",
        "description": "Evidence-backed AI project.",
        "stargazers_count": 321,
        "forks_count": 45,
        "language": "Python",
        "size": 16384,
        "created_at": "2026-03-01T00:00:00Z",
        "updated_at": "2026-04-01T00:00:00Z",
    }


def _structure_result() -> dict[str, object]:
    return {
        "code_to_doc_ratio": 1.4,
        "bytes_ratio": 1.2,
        "max_depth": 4,
        "has_entry_point": True,
        "has_tests": True,
        "has_config_files": True,
        "has_ci_cd": True,
        "license_file_present": True,
        "file_type_distribution": {".py": 12, ".md": 3, ".yml": 2},
        "structure_score": 0.82,
    }


def _retrieved_peers() -> list[dict[str, object]]:
    return [
        {
            "repo_url": "https://github.com/peer/one",
            "cohort": "analyzed_repo",
            "code_to_doc_ratio": 1.1,
            "bytes_ratio": 1.0,
            "max_depth": 5,
            "has_entry_point": True,
            "has_tests": True,
            "has_config_files": True,
            "has_ci_cd": True,
            "license_file_present": True,
            "file_type_distribution": {".py": 20, ".md": 4},
            "language": "Python",
            "stargazers_count": 250,
            "similarity_score": 0.81,
            "match_explanation": {"language": 1.0, "has_tests": 1.0},
            "retrieval_metadata": {
                "comparable": True,
                "sample_size": 2,
                "confidence": "medium",
                "sparse_peer": True,
                "low_confidence_peer": False,
                "disclosure": "Peer baseline is sparse; downstream scoring should stay conservative.",
            },
        },
        {
            "repo_url": "https://github.com/peer/two",
            "cohort": "analyzed_repo",
            "code_to_doc_ratio": 1.6,
            "bytes_ratio": 1.3,
            "max_depth": 3,
            "has_entry_point": True,
            "has_tests": True,
            "has_config_files": True,
            "has_ci_cd": False,
            "license_file_present": True,
            "file_type_distribution": {".py": 14, ".md": 6},
            "language": "Python",
            "stargazers_count": 180,
            "similarity_score": 0.77,
            "match_explanation": {"language": 1.0, "has_tests": 1.0},
            "retrieval_metadata": {
                "comparable": True,
                "sample_size": 2,
                "confidence": "medium",
                "sparse_peer": True,
                "low_confidence_peer": False,
                "disclosure": "Peer baseline is sparse; downstream scoring should stay conservative.",
            },
        },
    ]


def _scoring_result() -> dict[str, object]:
    return {
        "fake_risk_score": 37.5,
        "risk_level": "medium",
        "risk_band": "mild_suspicious",
        "dimension_scores": {
            "delivery": 8.0,
            "substance": 7.0,
            "evidence": 6.0,
            "peer_gap": 5.0,
            "community": 4.0,
            "hype_gap": 3.0,
        },
        "evidence_cards": [{"title": "Repository has tests", "type": "positive_signal"}],
        "guardrail_notes": ["Peer baseline is sparse; interpret peer gap conservatively."],
        "peer_baseline_summary": "Compared against 2 similar Python repositories.",
        "peer_baseline_meta": {"sample_size": 2, "confidence": "medium"},
        "version": "score-v-test",
    }


def _detail_report_snapshot(
    snapshot_at: str,
    *,
    score: float,
    version: str,
    summary_suffix: str,
) -> dict[str, object]:
    return {
        "snapshot_at": snapshot_at,
        "repo_url": "https://github.com/acme/signal-lab",
        "fake_risk_score": score,
        "risk_level": "medium" if score < 50 else "high",
        "risk_band": "mild_suspicious" if score < 50 else "moderate_suspicious",
        "dimension_scores": {
            "delivery": 8.0,
            "substance": 7.0,
            "evidence": 6.0,
            "peer_gap": 5.0,
            "community": 4.0,
            "hype_gap": 3.0,
        },
        "peer_baseline_meta": {
            "sample_size": 2,
            "confidence": "low",
            "sparse_peer": True,
            "low_confidence_peer": True,
            "disclosure": "Comparable peer set is sparse and low confidence, so peer-gap penalties stayed conservative.",
        },
        "version": version,
        "repo_info": {
            "owner": "acme",
            "name": "signal-lab",
            "url": "https://github.com/acme/signal-lab",
            "description": "Evidence-backed AI project.",
            "stars": 321,
            "forks": 45,
            "language": "Python",
            "size_kb": 16384,
            "created_at": "2026-03-01T00:00:00Z",
            "updated_at": "2026-04-01T00:00:00Z",
        },
        "peer_retrieval": {
            "retrieval_metadata": {
                "selected_count": 2,
                "comparable_count": 2,
                "sample_size": 2,
                "confidence": "low",
                "sparse_peer": True,
                "low_confidence_peer": True,
                "disclosure": "Comparable peer set is sparse and low confidence, so peer-gap penalties stayed conservative.",
            },
            "selected_peers": [
                {"repo_url": "https://github.com/peer/one", "language": "Python"},
                {"repo_url": "https://github.com/peer/two", "language": "Python"},
            ],
            "peer_baseline": {
                "sample_size": 2,
                "confidence": "low",
                "sparse_peer": True,
                "low_confidence_peer": True,
                "disclosure": "Comparable peer set is sparse and low confidence, so peer-gap penalties stayed conservative.",
                "code_to_doc_ratio_mean": 1.35,
            },
        },
        "project_features": {
            "language": "Python",
            "has_tests": True,
        },
        "scoring_result": {
            "fake_risk_score": score,
            "risk_level": "medium" if score < 50 else "high",
            "risk_band": "mild_suspicious" if score < 50 else "moderate_suspicious",
            "dimension_scores": {
                "delivery": 8.0,
                "substance": 7.0,
                "evidence": 6.0,
                "peer_gap": 5.0,
                "community": 4.0,
                "hype_gap": 3.0,
            },
            "evidence_cards": [
                {
                    "type": "peer_baseline",
                    "description": f"Snapshot {summary_suffix} evidence card.",
                    "value": {"sample_size": 2, "confidence": "low"},
                    "threshold": "Low-confidence peers should not amplify penalties unfairly.",
                    "passed": True,
                    "risk_signal": 5.0,
                }
            ],
            "guardrail_notes": [
                "Scoring is based on public repository evidence and should be treated as a verification aid, not a verdict.",
                "Comparable peer set is sparse and low confidence, so peer-gap penalties stayed conservative.",
            ],
            "peer_baseline_summary": (
                "Code/document balance is near the peer baseline; "
                "sample_size=2, confidence=low. Comparable peer set is sparse and low confidence, "
                "so peer-gap penalties stayed conservative."
            ),
            "peer_baseline_meta": {
                "sample_size": 2,
                "confidence": "low",
                "sparse_peer": True,
                "low_confidence_peer": True,
                "disclosure": "Comparable peer set is sparse and low confidence, so peer-gap penalties stayed conservative.",
            },
            "version": version,
        },
    }


def test_analyze_repository_persists_snapshot_and_reanalysis_history(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "analysis.sqlite3")
    captured: dict[str, object] = {}

    monkeypatch.setattr(app_runtime, "fetch_repo_basic_info", lambda repo_url, timeout=10: _repo_data())
    monkeypatch.setattr(app_runtime, "analyze_repo_structure", lambda repo_data: _structure_result())
    monkeypatch.setattr(app_runtime, "retrieve_similar_projects", lambda **kwargs: _retrieved_peers())

    def fake_compute_fake_risk_score(
        project_features: dict[str, object],
        peer_baseline: dict[str, object] | None = None,
        voting_signals: dict[str, object] | None = None,
    ) -> dict[str, object]:
        captured["project_features"] = project_features
        captured["peer_baseline"] = peer_baseline
        captured["voting_signals"] = voting_signals
        return _scoring_result()

    monkeypatch.setattr(app_runtime, "compute_fake_risk_score", fake_compute_fake_risk_score)

    first = cast(
        AnalysisPayload,
        cast(
            object,
            app_runtime.analyze_repository(
                "https://github.com/acme/signal-lab",
                store=store,
                analyzed_at="2026-04-01T10:00:00Z",
            ),
        ),
    )
    second = cast(
        AnalysisPayload,
        cast(
            object,
            app_runtime.analyze_repository(
                "https://github.com/acme/signal-lab",
                store=store,
                analyzed_at="2026-04-01T11:00:00Z",
            ),
        ),
    )
    history = store.get_repo_history("https://github.com/acme/signal-lab")

    peer_baseline = cast(dict[str, object], captured["peer_baseline"])

    assert first["snapshot"]["snapshot_version"] == 1
    assert second["snapshot"]["snapshot_version"] == 2
    assert second["repo_identity"]["repo_id"] == first["repo_identity"]["repo_id"]
    assert [item["snapshot_version"] for item in history] == [2, 1]
    assert history[0]["repo_url"] == "https://github.com/acme/signal-lab"
    assert history[0]["project_features"]["language"] == "Python"
    assert history[0]["peer_retrieval"]["selected_peers"][0]["repo_url"] == "https://github.com/peer/one"
    assert peer_baseline["sample_size"] == 2
    assert peer_baseline["confidence"] == "medium"
    assert peer_baseline["has_tests_rate"] == 1.0
    assert peer_baseline["stargazers_count_mean"] == 215.0
    assert captured["voting_signals"] is None


def test_api_analyze_returns_snapshot_identity_contract(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "api-analysis.sqlite3"))
    monkeypatch.setattr(app_runtime, "fetch_repo_basic_info", lambda repo_url, timeout=10: _repo_data())
    monkeypatch.setattr(app_runtime, "analyze_repo_structure", lambda repo_data: _structure_result())
    monkeypatch.setattr(app_runtime, "retrieve_similar_projects", lambda **kwargs: _retrieved_peers())
    monkeypatch.setattr(app_runtime, "compute_fake_risk_score", lambda **kwargs: _scoring_result())

    client = flask_app.app.test_client()

    first_response = client.post("/api/analyze", json={"repo_url": "https://github.com/acme/signal-lab"})
    second_response = client.post("/api/reanalyze", json={"repo_url": "https://github.com/acme/signal-lab"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_payload = cast(dict[str, Any], first_response.get_json())
    second_payload = cast(dict[str, Any], second_response.get_json())

    assert first_payload["success"] is True
    assert first_payload["snapshot"]["snapshot_version"] == 1
    assert isinstance(first_payload["snapshot"]["snapshot_id"], str)
    assert first_payload["snapshot"]["scoring_version"] == "score-v-test"
    assert first_payload["repo_identity"]["repo_url"] == "https://github.com/acme/signal-lab"
    assert first_payload["repo_identity"]["owner"] == "acme"
    assert first_payload["repo_identity"]["name"] == "signal-lab"
    assert first_payload["detail_url"] == "/repos/detail?repo_url=https://github.com/acme/signal-lab"
    assert first_payload["rankings_url"] == "/rankings"
    assert "Snapshot v1 persisted" in first_payload["surface_notice"]
    assert second_payload["snapshot"]["snapshot_version"] == 2
    assert second_payload["repo_identity"]["repo_id"] == first_payload["repo_identity"]["repo_id"]


def test_landing_and_report_pages_support_primary_navigation_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "landing-report.sqlite3"))
    monkeypatch.setattr(app_runtime, "fetch_repo_basic_info", lambda repo_url, timeout=10: _repo_data())
    monkeypatch.setattr(app_runtime, "analyze_repo_structure", lambda repo_data: _structure_result())
    monkeypatch.setattr(app_runtime, "retrieve_similar_projects", lambda **kwargs: _retrieved_peers())
    monkeypatch.setattr(app_runtime, "compute_fake_risk_score", lambda **kwargs: _scoring_result())

    client = flask_app.app.test_client()

    landing_response = client.get("/")
    report_response = client.post(
        "/analyze",
        data={"repo_url": "https://github.com/acme/signal-lab"},
        follow_redirects=True,
    )

    assert landing_response.status_code == 200
    landing_html = landing_response.get_data(as_text=True)
    assert 'action="/analyze"' in landing_html
    assert 'href="/rankings"' in landing_html

    assert report_response.status_code == 200
    report_html = report_response.get_data(as_text=True)
    assert "Analysis Results for acme/signal-lab" in report_html
    assert "Open persisted detail &amp; history" in report_html
    assert "Browse analyzed rankings" in report_html
    assert "Peer comparison disclaimer" in report_html
    assert "Repository Information" in report_html
    assert "Evidence Cards" in report_html
    assert "type: 'horizontalBar'" not in report_html
    assert "type: 'bar'" in report_html
    assert "indexAxis: 'y'" in report_html


def test_repo_detail_page_renders_for_real_flattened_snapshot_shape_from_analysis_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "real-detail.sqlite3"))
    monkeypatch.setattr(app_runtime, "fetch_repo_basic_info", lambda repo_url, timeout=10: _repo_data())
    monkeypatch.setattr(app_runtime, "analyze_repo_structure", lambda repo_data: _structure_result())
    monkeypatch.setattr(app_runtime, "retrieve_similar_projects", lambda **kwargs: _retrieved_peers())
    monkeypatch.setattr(app_runtime, "compute_fake_risk_score", lambda **kwargs: _scoring_result())

    client = flask_app.app.test_client()

    analyze_response = client.post("/api/analyze", json={"repo_url": "https://github.com/acme/signal-lab"})
    detail_response = client.get(
        "/repos/detail",
        query_string={"repo_url": "https://github.com/acme/signal-lab"},
    )

    assert analyze_response.status_code == 200
    assert detail_response.status_code == 200
    html = detail_response.get_data(as_text=True)
    assert "Repository Detail &amp; Score History" in html
    assert "Persisted at 2026-" in html
    assert "scoring score-v-test" in html
    assert "Compared against 2 similar Python repositories." in html
    assert "Repository has tests" in html


def test_repo_detail_page_renders_latest_report_and_history(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "detail.sqlite3")
    repo_url = "https://github.com/acme/signal-lab"
    repo_identity = {
        "repo_url": repo_url,
        "owner": "acme",
        "name": "signal-lab",
        "source": "github",
    }
    ranking_inputs = {
        "language": "Python",
        "stargazers_count": 321,
        "summary": "Signal lab credibility report.",
    }

    _ = store.record_analysis(
        repo_identity=repo_identity,
        report_snapshot=_detail_report_snapshot(
            "2026-04-01T10:00:00Z",
            score=41.0,
            version="score-v1",
            summary_suffix="v1",
        ),
        ranking_inputs=ranking_inputs,
    )
    _ = store.record_analysis(
        repo_identity=repo_identity,
        report_snapshot=_detail_report_snapshot(
            "2026-04-01T12:00:00Z",
            score=48.0,
            version="score-v2",
            summary_suffix="v2",
        ),
        ranking_inputs=ranking_inputs,
    )

    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "detail.sqlite3"))
    client = flask_app.app.test_client()

    response = client.get("/repos/detail", query_string={"repo_url": repo_url})

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Repository Detail &amp; Score History" in html
    assert "Latest Snapshot" in html
    assert "Snapshot v2" in html
    assert "Snapshot v1" in html
    assert "Comparable peer set is sparse and low confidence" in html
    assert "Chronological Score History" in html
    assert "Signal lab credibility report." in html


def test_repo_detail_api_returns_latest_snapshot_and_history(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "detail-api.sqlite3")
    repo_url = "https://github.com/acme/signal-lab"
    repo_identity = {
        "repo_url": repo_url,
        "owner": "acme",
        "name": "signal-lab",
        "source": "github",
    }
    ranking_inputs = {
        "language": "Python",
        "stargazers_count": 321,
        "summary": "Signal lab credibility report.",
    }

    _ = store.record_analysis(
        repo_identity=repo_identity,
        report_snapshot=_detail_report_snapshot(
            "2026-04-01T10:00:00Z",
            score=41.0,
            version="score-v1",
            summary_suffix="v1",
        ),
        ranking_inputs=ranking_inputs,
    )
    _ = store.record_analysis(
        repo_identity=repo_identity,
        report_snapshot=_detail_report_snapshot(
            "2026-04-01T12:00:00Z",
            score=48.0,
            version="score-v2",
            summary_suffix="v2",
        ),
        ranking_inputs=ranking_inputs,
    )

    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "detail-api.sqlite3"))
    client = flask_app.app.test_client()

    response = client.get("/api/repos/detail", query_string={"repo_url": repo_url})

    assert response.status_code == 200
    payload = cast(DetailApiPayload, cast(object, response.get_json()))
    assert payload["success"] is True
    assert payload["repo_url"] == repo_url
    assert payload["latest"]["snapshot_version"] == 2
    assert [entry["snapshot_version"] for entry in payload["history"]] == [2, 1]
    assert payload["latest"]["scoring_result"]["peer_baseline_meta"]["low_confidence_peer"] is True


def test_ranking_page_renders_filtered_analyzed_repos_with_transparency_notice(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "rankings.sqlite3")
    _seed_ranked_repo(
        store,
        repo_url="https://github.com/acme/signal-lab",
        owner="acme",
        name="signal-lab",
        language="Python",
        score=48.0,
        snapshot_at="2026-04-01T12:00:00Z",
        summary="Signal lab credibility report.",
    )
    _seed_ranked_repo(
        store,
        repo_url="https://github.com/zen/flash-demo",
        owner="zen",
        name="flash-demo",
        language="TypeScript",
        score=74.0,
        snapshot_at="2026-04-01T11:00:00Z",
        summary="Flashy launch page and waitlist.",
    )
    _ = store.record_feedback(
        repo_url="https://github.com/acme/signal-lab",
        actor_identity="github:user-1",
        feedback_kind="credibility_vote",
        payload={"vote": "support", "note": "Has working docs"},
        submitted_at="2026-04-01T12:05:00Z",
    )

    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "rankings.sqlite3"))
    client = flask_app.app.test_client()

    response = client.get(
        "/rankings",
        query_string={"language": "Python", "risk_band": "mild_suspicious", "search": "signal"},
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Analyzed Repository Rankings" in html
    assert "Only repositories analyzed and persisted by this app are ranked here" in html
    assert "Primary ordering is based on persisted risk snapshots" in html
    assert "feedback is supplemental and never authoritative for rank ordering" in html
    assert "signal-lab" in html
    assert "Flashy launch page and waitlist." not in html
    assert "/repos/detail?repo_url=https://github.com/acme/signal-lab" in html
    assert "1 support signal" in html


def test_ranking_api_returns_filtered_results_and_transparency_metadata(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "rankings-api.sqlite3")
    _seed_ranked_repo(
        store,
        repo_url="https://github.com/acme/signal-lab",
        owner="acme",
        name="signal-lab",
        language="Python",
        score=48.0,
        snapshot_at="2026-04-01T12:00:00Z",
        summary="Signal lab credibility report.",
    )
    _seed_ranked_repo(
        store,
        repo_url="https://github.com/acme/openweights",
        owner="acme",
        name="openweights",
        language="Python",
        score=32.0,
        snapshot_at="2026-04-01T13:00:00Z",
        summary="Structured training toolkit.",
    )
    _ = store.record_feedback(
        repo_url="https://github.com/acme/openweights",
        actor_identity="github:user-2",
        feedback_kind="credibility_vote",
        payload={"vote": "needs_review", "note": "Claims need verification"},
        submitted_at="2026-04-01T13:10:00Z",
    )

    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "rankings-api.sqlite3"))
    client = flask_app.app.test_client()

    response = client.get(
        "/api/rankings",
        query_string={
            "language": "Python",
            "sort": "snapshot_at",
            "direction": "asc",
            "limit": 1,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    payload = cast(dict[str, Any], cast(object, response.get_json()))
    assert payload["success"] is True
    assert payload["query"]["language"] == "Python"
    assert payload["query"]["sort"] == "snapshot_at"
    assert payload["query"]["direction"] == "asc"
    assert payload["query"]["limit"] == 1
    assert payload["meta"]["ordering_basis"] == "snapshot_at"
    assert payload["meta"]["feedback_authority"] == "supplemental_only"
    assert "Only analyzed repositories persisted by this app are included." in payload["meta"]["disclosure"]
    assert payload["total"] == 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["repo_url"] == "https://github.com/acme/signal-lab"
    assert payload["items"][0]["feedback_summary"]["total"] == 0


def test_ranking_api_rejects_unsupported_sort(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "rankings-invalid.sqlite3"))
    client = flask_app.app.test_client()

    response = client.get("/api/rankings", query_string={"sort": "feedback_count"})

    assert response.status_code == 400
    payload = cast(dict[str, Any], cast(object, response.get_json()))
    assert "Unsupported sort_by field" in payload["error"]


def test_repo_detail_page_shows_supplemental_feedback_section_and_sign_in_prompt(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "detail-feedback.sqlite3")
    repo_url = "https://github.com/acme/signal-lab"
    _seed_ranked_repo(
        store,
        repo_url=repo_url,
        owner="acme",
        name="signal-lab",
        language="Python",
        score=48.0,
        snapshot_at="2026-04-01T12:00:00Z",
        summary="Signal lab credibility report.",
    )
    _ = store.record_feedback(
        repo_url=repo_url,
        actor_identity="local:alice",
        feedback_kind="credibility_vote",
        payload={"vote": "needs_review", "note": "Claims need verification"},
        submitted_at="2026-04-01T12:05:00Z",
    )

    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "detail-feedback.sqlite3"))
    client = flask_app.app.test_client()

    response = client.get("/repos/detail", query_string={"repo_url": repo_url})

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Supplemental Feedback" in html
    assert "Feedback is supplemental only and never rewrites the core risk score or ranking basis." in html
    assert "1 needs-review signal" in html
    assert "Sign in to submit lightweight feedback" in html


def test_repo_detail_api_includes_supplemental_feedback_metadata(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "detail-feedback-api.sqlite3")
    repo_url = "https://github.com/acme/signal-lab"
    _seed_ranked_repo(
        store,
        repo_url=repo_url,
        owner="acme",
        name="signal-lab",
        language="Python",
        score=48.0,
        snapshot_at="2026-04-01T12:00:00Z",
        summary="Signal lab credibility report.",
    )
    _ = store.record_feedback(
        repo_url=repo_url,
        actor_identity="local:alice",
        feedback_kind="credibility_vote",
        payload={"vote": "support", "note": "Working demo"},
        submitted_at="2026-04-01T12:05:00Z",
    )

    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "detail-feedback-api.sqlite3"))
    client = flask_app.app.test_client()

    response = client.get("/api/repos/detail", query_string={"repo_url": repo_url})

    assert response.status_code == 200
    payload = cast(dict[str, Any], cast(object, response.get_json()))
    assert payload["success"] is True
    assert payload["feedback"]["authority"] == "supplemental_only"
    assert payload["feedback"]["summary"]["support"] == 1
    assert payload["feedback"]["summary"]["label"] == "1 support signal"


def test_feedback_api_requires_authenticated_identity(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "feedback-auth.sqlite3")
    repo_url = "https://github.com/acme/signal-lab"
    _seed_ranked_repo(
        store,
        repo_url=repo_url,
        owner="acme",
        name="signal-lab",
        language="Python",
        score=48.0,
        snapshot_at="2026-04-01T12:00:00Z",
        summary="Signal lab credibility report.",
    )

    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "feedback-auth.sqlite3"))
    client = flask_app.app.test_client()

    response = client.post(
        "/api/repos/feedback",
        json={"repo_url": repo_url, "vote": "support", "note": "Looks real"},
    )

    assert response.status_code == 401
    payload = cast(dict[str, Any], cast(object, response.get_json()))
    assert "authenticated identity" in payload["error"]


def test_feedback_api_records_dedupes_and_rate_limits_authenticated_feedback(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "feedback-submit.sqlite3")
    repo_url = "https://github.com/acme/signal-lab"
    _seed_ranked_repo(
        store,
        repo_url=repo_url,
        owner="acme",
        name="signal-lab",
        language="Python",
        score=48.0,
        snapshot_at="2026-04-01T12:00:00Z",
        summary="Signal lab credibility report.",
    )

    timestamps = iter(
        [
            "2026-04-01T12:00:00Z",
            "2026-04-01T12:00:10Z",
            "2026-04-01T12:01:10Z",
        ]
    )
    monkeypatch.setattr(flask_app, "_current_feedback_timestamp", lambda: next(timestamps))
    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "feedback-submit.sqlite3"))
    client = flask_app.app.test_client()
    with client.session_transaction() as session:
        session["feedback_identity"] = "local:alice"
        session["feedback_username"] = "alice"

    first_response = client.post(
        "/api/repos/feedback",
        json={"repo_url": repo_url, "vote": "support", "note": "Working demo"},
    )
    second_response = client.post(
        "/api/repos/feedback",
        json={"repo_url": repo_url, "vote": "disagree", "note": "Too fast"},
    )
    third_response = client.post(
        "/api/repos/feedback",
        json={"repo_url": repo_url, "vote": "support", "note": "Duplicate same window"},
    )

    first_payload = cast(FeedbackApiPayload, cast(object, first_response.get_json()))
    second_payload = cast(dict[str, Any], cast(object, second_response.get_json()))
    third_payload = cast(FeedbackApiPayload, cast(object, third_response.get_json()))
    feedback_records = store.list_feedback(repo_url)

    assert first_response.status_code == 200
    assert first_payload["success"] is True
    assert first_payload["feedback"]["outcome"] == "created"
    assert first_payload["feedback"]["summary"]["support"] == 1

    assert second_response.status_code == 429
    assert second_payload["error"] == "Feedback rate limit exceeded"

    assert third_response.status_code == 200
    assert third_payload["feedback"]["outcome"] == "duplicate_collapsed"
    assert third_payload["feedback"]["summary"]["support"] == 1
    assert len(feedback_records) == 1
    assert feedback_records[0]["payload"]["vote"] == "support"


def test_integrated_v1_navigation_flow_keeps_working_without_deferred_features(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "v1-flow.sqlite3"))
    monkeypatch.setattr(app_runtime, "fetch_repo_basic_info", lambda repo_url, timeout=10: _repo_data())
    monkeypatch.setattr(app_runtime, "analyze_repo_structure", lambda repo_data: _structure_result())
    monkeypatch.setattr(app_runtime, "retrieve_similar_projects", lambda **kwargs: _retrieved_peers())
    monkeypatch.setattr(app_runtime, "compute_fake_risk_score", lambda **kwargs: _scoring_result())
    monkeypatch.setattr(flask_app, "_current_feedback_timestamp", lambda: "2026-04-01T12:00:00Z")

    client = flask_app.app.test_client()
    repo_url = "https://github.com/acme/signal-lab"

    landing_response = client.get("/")
    analyze_response = client.post(
        "/analyze",
        data={"repo_url": repo_url},
        follow_redirects=True,
    )
    detail_response = client.get("/repos/detail", query_string={"repo_url": repo_url})
    rankings_before_feedback = client.get("/rankings")

    assert landing_response.status_code == 200
    assert analyze_response.status_code == 200
    assert detail_response.status_code == 200
    assert rankings_before_feedback.status_code == 200

    analyze_html = analyze_response.get_data(as_text=True)
    detail_html = detail_response.get_data(as_text=True)
    rankings_before_html = rankings_before_feedback.get_data(as_text=True)

    assert 'href="/repos/detail?repo_url=https://github.com/acme/signal-lab"' in analyze_html
    assert 'href="/rankings"' in analyze_html
    assert "Snapshot v1 persisted" in analyze_html
    assert "Chronological Score History" in detail_html
    assert "Snapshot v1" in detail_html
    assert "Sign in to submit lightweight feedback" in detail_html
    assert "Anonymous feedback is not enabled." in detail_html
    assert "twitter" not in detail_html.lower()
    assert "x.com" not in detail_html.lower()
    assert "No supplemental feedback yet" in rankings_before_html

    login_response = client.post(
        "/auth/login",
        data={"username": "alice", "next": f"/repos/detail?repo_url={repo_url}"},
        follow_redirects=True,
    )
    feedback_response = client.post(
        "/repos/feedback",
        data={"repo_url": repo_url, "vote": "support", "note": "Working demo"},
        follow_redirects=True,
    )
    rankings_after_feedback = client.get("/rankings")

    assert login_response.status_code == 200
    assert feedback_response.status_code == 200
    assert rankings_after_feedback.status_code == 200

    login_html = login_response.get_data(as_text=True)
    feedback_html = feedback_response.get_data(as_text=True)
    rankings_after_html = rankings_after_feedback.get_data(as_text=True)

    assert "Signed in as alice" in login_html
    assert "Submit lightweight feedback" in login_html
    assert "Supplemental feedback recorded." in feedback_html
    assert "1 support signal" in feedback_html
    assert "al***" in feedback_html
    assert "1 support signal" in rankings_after_html
    assert "signal-lab" in rankings_after_html


def test_analyze_repository_falls_back_without_peer_candidates_and_still_supports_v1_views(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store = PersistenceStore(tmp_path / "fallback.sqlite3")
    monkeypatch.setattr(app_runtime, "fetch_repo_basic_info", lambda repo_url, timeout=10: _repo_data())
    monkeypatch.setattr(app_runtime, "analyze_repo_structure", lambda repo_data: _structure_result())

    result = cast(
        AnalysisPayload,
        cast(
            object,
            app_runtime.analyze_repository(
                "https://github.com/acme/signal-lab",
                store=store,
                candidate_projects=[],
                analyzed_at="2026-04-01T10:00:00Z",
            ),
        ),
    )
    with flask_app.app.test_request_context():
        analysis_payload = cast(dict[str, object], cast(object, result))
        surface_payload = cast(dict[str, Any], flask_app._build_analysis_surface_payload(analysis_payload))

    history = store.get_repo_history("https://github.com/acme/signal-lab")
    latest = cast(dict[str, Any], history[0])
    retrieval = cast(dict[str, Any], latest["peer_retrieval"])
    retrieval_meta = cast(dict[str, Any], retrieval["retrieval_metadata"])
    scoring_result = cast(dict[str, Any], result["scoring_result"])

    assert result["snapshot"]["snapshot_version"] == 1
    assert result["repo_identity"]["repo_url"] == "https://github.com/acme/signal-lab"
    assert result["repo_identity"]["source"] == "github"
    assert result["repo_identity"]["repo_id"] > 0
    assert surface_payload["detail_url"] == "/repos/detail?repo_url=https://github.com/acme/signal-lab"
    assert surface_payload["rankings_url"] == "/rankings"
    assert retrieval["selected_peers"] == []
    assert retrieval["peer_baseline"] is None
    assert retrieval_meta["selected_count"] == 0
    assert retrieval_meta["comparable_count"] == 0
    assert "No directly comparable peers were found" in str(retrieval_meta["disclosure"])
    assert len(cast(list[dict[str, Any]], scoring_result["evidence_cards"])) >= 3
    assert len(cast(list[str], scoring_result["guardrail_notes"])) >= 1
    assert "baseline" in str(scoring_result["peer_baseline_summary"]).lower()
    assert len(history) == 1


def test_rankings_keep_feedback_supplemental_to_core_ordering(monkeypatch, tmp_path: Path) -> None:
    store = PersistenceStore(tmp_path / "rankings-feedback-order.sqlite3")
    _seed_ranked_repo(
        store,
        repo_url="https://github.com/acme/high-risk",
        owner="acme",
        name="high-risk",
        language="Python",
        score=72.0,
        snapshot_at="2026-04-01T12:00:00Z",
        summary="High risk repo.",
    )
    _seed_ranked_repo(
        store,
        repo_url="https://github.com/acme/community-favorite",
        owner="acme",
        name="community-favorite",
        language="Python",
        score=28.0,
        snapshot_at="2026-04-01T11:00:00Z",
        summary="Lower risk but heavily discussed repo.",
    )
    for actor_identity, submitted_at in [
        ("local:alice", "2026-04-01T12:05:00Z"),
        ("local:bob", "2026-04-01T12:06:00Z"),
        ("local:carol", "2026-04-01T12:07:00Z"),
    ]:
        _ = store.record_feedback(
            repo_url="https://github.com/acme/community-favorite",
            actor_identity=actor_identity,
            feedback_kind="credibility_vote",
            payload={"vote": "support", "note": "Looks real"},
            submitted_at=submitted_at,
        )

    monkeypatch.setenv("AI_FAKE_PROJECT_DB_PATH", str(tmp_path / "rankings-feedback-order.sqlite3"))
    client = flask_app.app.test_client()

    response = client.get(
        "/api/rankings",
        query_string={"sort": "latest_fake_risk_score", "direction": "desc"},
    )

    assert response.status_code == 200
    payload = cast(dict[str, Any], cast(object, response.get_json()))
    items = cast(list[dict[str, Any]], payload["items"])

    assert payload["success"] is True
    assert [item["repo_url"] for item in items] == [
        "https://github.com/acme/high-risk",
        "https://github.com/acme/community-favorite",
    ]
    assert items[0]["latest_fake_risk_score"] == 72.0
    assert items[0]["feedback_summary"]["total"] == 0
    assert items[1]["latest_fake_risk_score"] == 28.0
    assert items[1]["feedback_summary"]["support"] == 3
    assert payload["meta"]["feedback_authority"] == "supplemental_only"
    assert "feedback is supplemental and never authoritative for rank ordering" in payload["meta"]["disclosure"]
