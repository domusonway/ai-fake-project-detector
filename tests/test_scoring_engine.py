from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Callable, TypedDict, cast

import pytest

from modules.scoring_engine.scoring_engine import compute_fake_risk_score
from .fixtures import build_peer_baseline, get_project_fixture
from .fixtures.project_fixtures import PeerBaseline, ProjectFeatures


class RetrievalMetadataOverride(TypedDict, total=False):
    sample_size: int
    confidence: str
    sparse_peer: bool
    low_confidence_peer: bool
    disclosure: str


class PeerBaselineOverride(PeerBaseline, total=False):
    confidence: str
    sparse_peer: bool
    low_confidence_peer: bool
    disclosure: str
    retrieval_metadata: RetrievalMetadataOverride


class EvidenceCard(TypedDict, total=False):
    type: str
    description: str
    value: object
    threshold: str
    passed: bool
    risk_signal: float


class ScoreReport(TypedDict):
    fake_risk_score: float
    risk_level: str
    risk_band: str
    dimension_scores: dict[str, float]
    evidence_cards: list[EvidenceCard]
    guardrail_notes: list[str]
    peer_baseline_summary: str


_SCORER = cast(Callable[..., object], cast(object, compute_fake_risk_score))


def _project_features(cohort: str) -> ProjectFeatures:
    return deepcopy(get_project_fixture(cohort)["project_features"])


def _peer_baseline_for(
    *cohorts: str,
    sample_size: int | None = None,
    confidence: str | None = None,
    sparse_peer: bool | None = None,
    low_confidence_peer: bool | None = None,
    disclosure: str | None = None,
    retrieval_metadata: RetrievalMetadataOverride | None = None,
) -> PeerBaselineOverride:
    baseline: PeerBaselineOverride = {**build_peer_baseline([get_project_fixture(cohort) for cohort in cohorts])}
    if sample_size is not None:
        baseline["sample_size"] = sample_size
    if confidence is not None:
        baseline["confidence"] = confidence
    if sparse_peer is not None:
        baseline["sparse_peer"] = sparse_peer
    if low_confidence_peer is not None:
        baseline["low_confidence_peer"] = low_confidence_peer
    if disclosure is not None:
        baseline["disclosure"] = disclosure
    if retrieval_metadata is not None:
        baseline["retrieval_metadata"] = retrieval_metadata
    return baseline


def _compute_score(
    project_features: ProjectFeatures,
    peer_baseline: PeerBaselineOverride | None = None,
    voting_signals: Mapping[str, float | int] | None = None,
) -> ScoreReport:
    raw_result = _SCORER(
        project_features=project_features,
        peer_baseline=peer_baseline,
        voting_signals=voting_signals,
    )
    return cast(ScoreReport, raw_result)


VOTING_SIGNALS: dict[str, float | int] = {
    "vote_count": 42,
    "positive_ratio": 0.75,
    "controversy_score": 0.2,
}


def test_compute_fake_risk_score_returns_complete_explainability_payload() -> None:
    result = _compute_score(
        _project_features("substantive"),
        _peer_baseline_for("substantive", "early_but_real", "hype_heavy", confidence="high"),
        VOTING_SIGNALS,
    )

    assert 0 <= result["fake_risk_score"] <= 100
    assert result["risk_level"] in ["low", "medium", "high", "extreme"]
    assert result["risk_band"] in [
        "trusted",
        "mild_suspicious",
        "moderate_suspicious",
        "high_suspicious",
        "very_high_suspicious",
    ]

    dims = result["dimension_scores"]
    assert set(dims) == {"delivery", "substance", "evidence", "peer_gap", "community", "hype_gap"}
    assert 0 <= dims["delivery"] <= 30
    assert 0 <= dims["substance"] <= 20
    assert 0 <= dims["evidence"] <= 15
    assert 0 <= dims["peer_gap"] <= 15
    assert 0 <= dims["community"] <= 10
    assert 0 <= dims["hype_gap"] <= 10

    assert len(result["evidence_cards"]) >= 3
    assert all(card.get("type") for card in result["evidence_cards"])
    assert all("risk_signal" in card for card in result["evidence_cards"])
    assert len(result["guardrail_notes"]) >= 1
    assert isinstance(result["peer_baseline_summary"], str)


def test_scoring_matches_rubric_for_expected_cohorts() -> None:
    substantive = _compute_score(
        _project_features("substantive"),
        _peer_baseline_for("substantive", "early_but_real", confidence="high"),
        VOTING_SIGNALS,
    )
    early_but_real = _compute_score(
        _project_features("early_but_real"),
        _peer_baseline_for("substantive", "early_but_real", confidence="high"),
    )
    hype_heavy = _compute_score(
        _project_features("hype_heavy"),
        _peer_baseline_for("substantive", "early_but_real", "hype_heavy", confidence="medium"),
    )

    assert substantive["fake_risk_score"] < early_but_real["fake_risk_score"] < hype_heavy["fake_risk_score"]
    assert substantive["risk_band"] == "trusted"
    assert early_but_real["risk_band"] in {"trusted", "mild_suspicious"}
    assert hype_heavy["risk_band"] in {"high_suspicious", "very_high_suspicious"}
    assert hype_heavy["risk_level"] == "extreme"


def test_low_confidence_sparse_peer_metadata_stays_conservative() -> None:
    low_confidence_baseline = _peer_baseline_for(
        "early_but_real",
        sample_size=1,
        confidence="low",
        sparse_peer=True,
        low_confidence_peer=True,
        disclosure="Peer baseline is sparse and low confidence; downstream scoring should stay conservative.",
        retrieval_metadata={
            "sample_size": 1,
            "confidence": "low",
            "sparse_peer": True,
            "low_confidence_peer": True,
            "disclosure": "Peer baseline is sparse and low confidence; downstream scoring should stay conservative.",
        },
    )

    result = _compute_score(_project_features("early_but_real"), low_confidence_baseline)

    assert result["dimension_scores"]["peer_gap"] <= 6.0
    assert any("low confidence" in note.lower() or "sparse" in note.lower() for note in result["guardrail_notes"])
    assert "low confidence" in result["peer_baseline_summary"].lower()


def test_early_but_real_projects_get_protection_guardrail() -> None:
    result = _compute_score(
        _project_features("early_but_real"),
        _peer_baseline_for("substantive", "early_but_real", confidence="high"),
    )

    assert result["fake_risk_score"] <= 40
    assert result["dimension_scores"]["community"] <= 5
    assert any("early" in note.lower() or "real" in note.lower() for note in result["guardrail_notes"])


def test_missing_baseline_still_reports_notes_and_summary() -> None:
    result = _compute_score(_project_features("substantive"))

    assert len(result["evidence_cards"]) >= 3
    assert len(result["guardrail_notes"]) >= 1
    assert "baseline" in result["peer_baseline_summary"].lower()
    assert any("public repo" in note.lower() or "公开仓库" in note for note in result["guardrail_notes"])


def test_compute_fake_risk_score_invalid_input() -> None:
    with pytest.raises(ValueError, match="project_features must be a dictionary"):
        _unused_result: object = _SCORER(
            project_features="invalid",
            peer_baseline=build_peer_baseline(),
            voting_signals=VOTING_SIGNALS,
        )

    incomplete_features = dict(_project_features("substantive"))
    del incomplete_features["code_to_doc_ratio"]

    with pytest.raises(ValueError, match="Missing required feature"):
        _unused_result = _SCORER(
            project_features=incomplete_features,
            peer_baseline=build_peer_baseline(),
            voting_signals=VOTING_SIGNALS,
        )
