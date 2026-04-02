from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SCORING_VERSION = "v1-risk-rubric-2026-04-01"


def compute_fake_risk_score(project_features, peer_baseline=None, voting_signals=None):
    if not isinstance(project_features, dict):
        raise ValueError("project_features must be a dictionary")

    required_features = [
        "code_to_doc_ratio",
        "bytes_ratio",
        "max_depth",
        "has_entry_point",
        "has_tests",
        "has_config_files",
        "has_ci_cd",
        "license_file_present",
        "file_type_distribution",
        "language",
        "stargazers_count",
        "description",
        "size",
    ]

    for feature in required_features:
        if feature not in project_features:
            raise ValueError(f"Missing required feature: {feature}")

    _validate_project_features(project_features)

    code_to_doc_ratio = float(project_features["code_to_doc_ratio"])
    bytes_ratio = float(project_features["bytes_ratio"])
    max_depth = int(project_features["max_depth"])
    has_entry_point = bool(project_features["has_entry_point"])
    has_tests = bool(project_features["has_tests"])
    has_config_files = bool(project_features["has_config_files"])
    has_ci_cd = bool(project_features["has_ci_cd"])
    license_file_present = bool(project_features["license_file_present"])
    file_type_distribution = project_features["file_type_distribution"] or {}
    stargazers_count = int(project_features["stargazers_count"])
    description = project_features.get("description") or ""
    size = int(project_features["size"])

    peer_meta = _peer_baseline_meta(peer_baseline)
    early_real_signal = _early_real_signal(project_features)

    delivery_risk = _delivery_risk(
        has_entry_point,
        has_tests,
        has_config_files,
        has_ci_cd,
        license_file_present,
        early_real_signal,
    )
    substance_risk = _substance_risk(code_to_doc_ratio, bytes_ratio, max_depth, size, early_real_signal)
    evidence_risk = _evidence_risk(description, file_type_distribution, code_to_doc_ratio, has_entry_point, has_tests)
    peer_gap_risk = _peer_gap_risk(project_features, peer_baseline, peer_meta)
    community_risk = _community_risk(
        stargazers_count,
        voting_signals,
        delivery_risk,
        substance_risk,
        evidence_risk,
        early_real_signal,
    )
    hype_gap_risk = _hype_gap_risk(
        description,
        code_to_doc_ratio,
        size,
        stargazers_count,
        delivery_risk,
        substance_risk,
        early_real_signal,
    )

    dimension_scores = {
        "delivery": delivery_risk * 30.0,
        "substance": substance_risk * 20.0,
        "evidence": evidence_risk * 15.0,
        "peer_gap": peer_gap_risk * 15.0,
        "community": community_risk * 10.0,
        "hype_gap": hype_gap_risk * 10.0,
    }

    guardrail_notes = _build_guardrail_notes(early_real_signal, peer_meta)
    peer_baseline_summary = _peer_baseline_summary(project_features, peer_baseline, peer_meta)

    fake_risk_score = _clamp(sum(dimension_scores.values()), 0.0, 100.0)
    fake_risk_score, dimension_scores, guardrail_notes = _apply_early_real_protection(
        fake_risk_score,
        dimension_scores,
        delivery_risk,
        substance_risk,
        evidence_risk,
        early_real_signal,
        guardrail_notes,
    )

    risk_level = _risk_level(fake_risk_score)
    risk_band = _risk_band(fake_risk_score)

    evidence_cards = _build_evidence_cards(
        project_features,
        dimension_scores,
        peer_meta,
        fake_risk_score,
    )

    return {
        "fake_risk_score": round(fake_risk_score, 2),
        "risk_level": risk_level,
        "risk_band": risk_band,
        "dimension_scores": {key: round(value, 2) for key, value in dimension_scores.items()},
        "evidence_cards": evidence_cards,
        "guardrail_notes": guardrail_notes,
        "peer_baseline_summary": peer_baseline_summary,
        "peer_baseline_meta": {
            "sample_size": peer_meta["sample_size"],
            "confidence": peer_meta["confidence"],
        },
        "version": SCORING_VERSION,
    }


def _validate_project_features(project_features):
    numeric_fields = ["code_to_doc_ratio", "bytes_ratio", "max_depth", "stargazers_count", "size"]
    for field in numeric_fields:
        value = project_features[field]
        if not isinstance(value, (int, float)):
            raise TypeError(f"Invalid type for feature: {field}")
        if field == "stargazers_count" and value < 0:
            raise ValueError("stargazers_count cannot be negative")
        if value < 0:
            raise ValueError(f"{field} cannot be negative")

    boolean_fields = [
        "has_entry_point",
        "has_tests",
        "has_config_files",
        "has_ci_cd",
        "license_file_present",
    ]
    for field in boolean_fields:
        value = project_features[field]
        if not isinstance(value, (bool, int)):
            raise TypeError(f"Invalid type for feature: {field}")

    if not isinstance(project_features["file_type_distribution"], dict):
        raise TypeError("file_type_distribution must be a dictionary")

    if not isinstance(project_features["language"], str):
        raise TypeError("language must be a string")


def _delivery_risk(has_entry_point, has_tests, has_config_files, has_ci_cd, license_file_present, early_real_signal):
    weights = {
        "has_entry_point": 0.35,
        "has_tests": 0.25,
        "has_config_files": 0.15,
        "has_ci_cd": 0.10,
        "license_file_present": 0.15,
    }
    if early_real_signal:
        weights["has_ci_cd"] = 0.05
        weights["has_tests"] = 0.30

    total_weight = sum(weights.values()) or 1.0
    missing_weight = 0.0
    if not has_entry_point:
        missing_weight += weights["has_entry_point"]
    if not has_tests:
        missing_weight += weights["has_tests"]
    if not has_config_files:
        missing_weight += weights["has_config_files"]
    if not has_ci_cd:
        missing_weight += weights["has_ci_cd"]
    if not license_file_present:
        missing_weight += weights["license_file_present"]
    return _clamp(missing_weight / total_weight, 0.0, 1.0)


def _substance_risk(code_to_doc_ratio, bytes_ratio, max_depth, size, early_real_signal):
    ratio_risk = _risk_from_ratio(code_to_doc_ratio, 0.6, 2.5)
    bytes_risk = _risk_from_ratio(bytes_ratio, 0.6, 2.5)
    depth_risk = _depth_risk(max_depth)
    size_risk = _size_risk(size)
    risk = (ratio_risk * 0.40) + (bytes_risk * 0.35) + (depth_risk * 0.15) + (size_risk * 0.10)
    if early_real_signal:
        risk *= 0.9
    return _clamp(risk, 0.0, 1.0)


def _evidence_risk(description, file_type_distribution, code_to_doc_ratio, has_entry_point, has_tests):
    desc_len = len(description.strip())
    type_count = len(file_type_distribution)
    desc_risk = _risk_from_range(desc_len, 30, 90)
    type_risk = _risk_from_range(type_count, 3, 6)
    proof_penalty = 0.0
    if code_to_doc_ratio < 0.8:
        proof_penalty += 0.35
    if not has_entry_point:
        proof_penalty += 0.25
    if not has_tests:
        proof_penalty += 0.25
    return _clamp((desc_risk * 0.20) + (type_risk * 0.20) + proof_penalty, 0.0, 1.0)


def _peer_gap_risk(project_features, peer_baseline, peer_meta):
    if not isinstance(peer_baseline, dict) or not peer_baseline:
        return 0.1

    downside_gaps = [
        _downside_gap_ratio(project_features["code_to_doc_ratio"], peer_baseline.get("code_to_doc_ratio_mean")),
        _downside_gap_ratio(project_features["bytes_ratio"], peer_baseline.get("bytes_ratio_mean")),
        _downside_gap_ratio(project_features["max_depth"], peer_baseline.get("max_depth_mean")),
        _downside_gap_boolean(project_features["has_entry_point"], peer_baseline.get("has_entry_point_rate")),
        _downside_gap_boolean(project_features["has_tests"], peer_baseline.get("has_tests_rate")),
        _downside_gap_boolean(project_features["has_config_files"], peer_baseline.get("has_config_files_rate")),
        _downside_gap_boolean(project_features["has_ci_cd"], peer_baseline.get("has_ci_cd_rate")),
        _downside_gap_boolean(project_features["license_file_present"], peer_baseline.get("license_file_present_rate")),
        _downside_gap_ratio(project_features["stargazers_count"], peer_baseline.get("stargazers_count_mean")),
    ]
    raw_gap = sum(downside_gaps) / len(downside_gaps)
    confidence_weight = _peer_confidence_weight(peer_meta)
    conservative_gap = raw_gap * confidence_weight
    if peer_meta["low_confidence_peer"] or peer_meta["sample_size"] < 3:
        conservative_gap = min(conservative_gap, 0.35)
    return _clamp(max(conservative_gap, 0.05), 0.0, 1.0)


def _community_risk(stargazers_count, voting_signals, delivery_risk, substance_risk, evidence_risk, early_real_signal):
    attention_factor = _attention_factor(stargazers_count)
    intrinsic_weakness = max(delivery_risk, substance_risk, evidence_risk)
    attention_mismatch = attention_factor * intrinsic_weakness

    vote_risk = 0.0
    if isinstance(voting_signals, dict) and voting_signals:
        vote_count = int(voting_signals.get("vote_count", 0) or 0)
        positive_ratio = float(voting_signals.get("positive_ratio", 0.5) or 0.5)
        controversy_score = float(voting_signals.get("controversy_score", 0.0) or 0.0)
        if vote_count >= 10:
            volume_weight = _clamp(vote_count / 50.0, 0.2, 1.0)
            vote_risk = _clamp(((1.0 - positive_ratio) * 0.7 + controversy_score * 0.3) * volume_weight, 0.0, 1.0)

    risk = max(attention_mismatch * 0.85, vote_risk * 0.55)
    if early_real_signal:
        risk *= 0.6
    return _clamp(risk, 0.0, 1.0)


def _hype_gap_risk(description, code_to_doc_ratio, size, stargazers_count, delivery_risk, substance_risk, early_real_signal):
    narrative_factor = _narrative_factor(description)
    attention_factor = _attention_factor(stargazers_count)
    implementation_gap = max(delivery_risk, substance_risk, _risk_from_ratio(code_to_doc_ratio, 0.8, 2.0))
    size_penalty = 0.25 if size < 8000 else 0.0
    risk = ((narrative_factor * 0.6) + (attention_factor * 0.4) + size_penalty) * implementation_gap
    if early_real_signal:
        risk *= 0.45
    return _clamp(risk, 0.0, 1.0)


def _build_evidence_cards(project_features, dimension_scores, peer_meta, fake_risk_score):
    cards = [
        {
            "type": "delivery_readiness",
            "description": "Checks for entry point, tests, config files, CI, and license coverage.",
            "value": {
                "has_entry_point": bool(project_features["has_entry_point"]),
                "has_tests": bool(project_features["has_tests"]),
                "has_config_files": bool(project_features["has_config_files"]),
                "has_ci_cd": bool(project_features["has_ci_cd"]),
                "license_file_present": bool(project_features["license_file_present"]),
            },
            "threshold": "Missing shipping signals should stay limited and explainable.",
            "passed": dimension_scores["delivery"] <= 10,
            "risk_signal": round(dimension_scores["delivery"], 2),
        },
        {
            "type": "substance_balance",
            "description": "Compares code/document balance, depth, and repository size as weak maturity signals.",
            "value": {
                "code_to_doc_ratio": round(float(project_features["code_to_doc_ratio"]), 3),
                "bytes_ratio": round(float(project_features["bytes_ratio"]), 3),
                "max_depth": int(project_features["max_depth"]),
                "size": int(project_features["size"]),
            },
            "threshold": "Healthy code/doc ratios and some implementation depth reduce risk.",
            "passed": dimension_scores["substance"] <= 8,
            "risk_signal": round(dimension_scores["substance"], 2),
        },
        {
            "type": "peer_baseline",
            "description": "Peer comparison stays conservative when the baseline is sparse or low confidence.",
            "value": {
                "sample_size": peer_meta["sample_size"],
                "confidence": peer_meta["confidence"],
                "sparse_peer": peer_meta["sparse_peer"],
            },
            "threshold": "Low-confidence peers should not amplify penalties unfairly.",
            "passed": dimension_scores["peer_gap"] <= 6,
            "risk_signal": round(dimension_scores["peer_gap"], 2),
        },
        {
            "type": "attention_mismatch",
            "description": "Measures whether attention and narrative strength outrun observable delivery signals.",
            "value": {
                "stars": int(project_features["stargazers_count"]),
                "description_length": len(str(project_features.get("description") or "").strip()),
                "total_risk": round(fake_risk_score, 2),
            },
            "threshold": "High attention with weak shipping evidence should raise risk.",
            "passed": (dimension_scores["community"] + dimension_scores["hype_gap"]) <= 8,
            "risk_signal": round(dimension_scores["community"] + dimension_scores["hype_gap"], 2),
        },
    ]
    return cards[: max(3, len(cards))]


def _build_guardrail_notes(early_real_signal, peer_meta):
    notes = [
        "Scoring is based on public repository evidence and should be treated as a verification aid, not a verdict.",
    ]
    if peer_meta["baseline_available"] is False:
        notes.append("Peer baseline was unavailable, so peer-gap scoring stayed near neutral instead of amplifying risk.")
    elif peer_meta["low_confidence_peer"] or peer_meta["sparse_peer"]:
        notes.append(peer_meta["disclosure"])
    else:
        notes.append(
            f"Peer baseline used {peer_meta['sample_size']} comparable peers with {peer_meta['confidence']} confidence."
        )

    if early_real_signal:
        notes.append("Early-but-real guardrail applied: small scale or missing CI alone should not inflate the repo into a high-risk band.")

    return notes


def _apply_early_real_protection(fake_risk_score, dimension_scores, delivery_risk, substance_risk, evidence_risk, early_real_signal, guardrail_notes):
    if not early_real_signal:
        return fake_risk_score, dimension_scores, guardrail_notes

    if delivery_risk <= 0.30 and substance_risk <= 0.40 and evidence_risk <= 0.35:
        if dimension_scores["community"] > 5.0:
            dimension_scores["community"] = 5.0
        if dimension_scores["hype_gap"] > 4.0:
            dimension_scores["hype_gap"] = 4.0
        adjusted_total = sum(dimension_scores.values())
        if adjusted_total > 40.0:
            fake_risk_score = 40.0
            if not any("Early-but-real" in note for note in guardrail_notes):
                guardrail_notes.append("Early-but-real guardrail capped maturity-driven penalties at the PRD mild-risk boundary.")
            return fake_risk_score, dimension_scores, guardrail_notes
        return adjusted_total, dimension_scores, guardrail_notes

    return fake_risk_score, dimension_scores, guardrail_notes


def _peer_baseline_summary(project_features, peer_baseline, peer_meta):
    if not isinstance(peer_baseline, dict) or not peer_baseline:
        return "Peer baseline unavailable; peer comparison stayed near neutral to avoid over-penalizing the repository."

    ratio = float(project_features["code_to_doc_ratio"])
    ratio_mean = float(peer_baseline.get("code_to_doc_ratio_mean", 0.0) or 0.0)
    relation = "near the peer baseline"
    if ratio_mean > 0:
        if ratio >= ratio_mean * 1.1:
            relation = "above the peer baseline"
        elif ratio <= ratio_mean * 0.9:
            relation = "below the peer baseline"

    confidence_clause = (
        f"sample_size={peer_meta['sample_size']}, confidence={peer_meta['confidence']}"
        if peer_meta["baseline_available"]
        else "baseline unavailable"
    )
    summary = f"Code/document balance is {relation}; peer baseline {confidence_clause}."
    if peer_meta["low_confidence_peer"] or peer_meta["sparse_peer"]:
        summary = f"{summary} {peer_meta['disclosure']}"
    return summary


def _peer_baseline_meta(peer_baseline: Any) -> dict[str, Any]:
    if not isinstance(peer_baseline, Mapping) or not peer_baseline:
        return {
            "baseline_available": False,
            "sample_size": 0,
            "confidence": "low",
            "sparse_peer": True,
            "low_confidence_peer": True,
            "disclosure": "Peer baseline was unavailable, so downstream scoring stayed conservative.",
        }

    nested = peer_baseline.get("retrieval_metadata")
    nested_meta = nested if isinstance(nested, Mapping) else {}

    sample_size_value = peer_baseline.get("sample_size")
    if sample_size_value is None:
        sample_size_value = nested_meta.get("sample_size")
    if sample_size_value is None:
        sample_size_value = nested_meta.get("comparable_peer_count")
    sample_size = _coerce_int(sample_size_value, 0)

    confidence_value = peer_baseline.get("confidence")
    if confidence_value is None:
        confidence_value = nested_meta.get("confidence")
    confidence = _coerce_str(confidence_value, _default_confidence(sample_size))

    sparse_peer = bool(peer_baseline.get("sparse_peer", nested_meta.get("sparse_peer", sample_size < 3)))
    low_confidence_peer = bool(
        peer_baseline.get("low_confidence_peer", nested_meta.get("low_confidence_peer", confidence == "low"))
    )
    disclosure_value = peer_baseline.get("disclosure")
    if disclosure_value is None:
        disclosure_value = nested_meta.get("disclosure")
    disclosure = _coerce_str(
        disclosure_value,
        _default_disclosure(sample_size, sparse_peer, low_confidence_peer),
    )
    return {
        "baseline_available": True,
        "sample_size": sample_size,
        "confidence": confidence,
        "sparse_peer": sparse_peer,
        "low_confidence_peer": low_confidence_peer,
        "disclosure": disclosure,
    }


def _default_confidence(sample_size):
    if sample_size >= 3:
        return "high"
    if sample_size == 2:
        return "medium"
    return "low"


def _default_disclosure(sample_size, sparse_peer, low_confidence_peer):
    if sample_size == 0:
        return "Peer baseline was unavailable, so downstream scoring stayed conservative."
    if sparse_peer and low_confidence_peer:
        return "Peer baseline is sparse and low confidence; downstream scoring stayed conservative."
    if sparse_peer:
        return "Peer baseline is sparse; downstream scoring stayed conservative."
    if low_confidence_peer:
        return "Peer baseline confidence is low; downstream scoring stayed conservative."
    return "Peer baseline confidence is stable enough for contextual comparison."


def _coerce_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _coerce_str(value: object, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value or default
    return str(value)


def _peer_confidence_weight(peer_meta):
    confidence = peer_meta["confidence"]
    if confidence == "high":
        return 1.0
    if confidence == "medium":
        return 0.55
    return 0.25


def _early_real_signal(project_features):
    return bool(
        project_features["has_entry_point"]
        and project_features["has_tests"]
        and project_features["license_file_present"]
        and float(project_features["code_to_doc_ratio"]) >= 1.0
        and float(project_features["bytes_ratio"]) >= 1.0
        and int(project_features["stargazers_count"]) <= 200
    )


def _risk_level(score):
    if score <= 20:
        return "low"
    if score <= 40:
        return "medium"
    if score <= 60:
        return "high"
    return "extreme"


def _risk_band(score):
    if score <= 20:
        return "trusted"
    if score <= 40:
        return "mild_suspicious"
    if score <= 60:
        return "moderate_suspicious"
    if score <= 80:
        return "high_suspicious"
    return "very_high_suspicious"


def _risk_from_ratio(value, low, high):
    if value <= low:
        return 1.0
    if value >= high:
        return 0.0
    return (high - value) / (high - low)


def _risk_from_range(value, low, high):
    if value <= low:
        return 1.0
    if value >= high:
        return 0.0
    return (high - value) / (high - low)


def _depth_risk(max_depth):
    if max_depth <= 0:
        return 1.0
    if max_depth == 1:
        return 0.45
    if max_depth == 2:
        return 0.15
    return 0.0


def _size_risk(size):
    if size <= 1000:
        return 1.0
    if size <= 5000:
        return 0.45
    if size <= 15000:
        return 0.15
    return 0.0


def _attention_factor(stargazers_count):
    if stargazers_count < 200:
        return 0.0
    if stargazers_count >= 5000:
        return 1.0
    return _clamp((stargazers_count - 200) / 4800.0, 0.0, 1.0)


def _narrative_factor(description):
    text = description.strip().lower()
    if not text:
        return 0.0
    hype_keywords = ["ambitious", "revolution", "reinvent", "vision", "ever", "platform", "breakthrough"]
    keyword_hits = sum(1 for keyword in hype_keywords if keyword in text)
    length_factor = _clamp(len(text) / 120.0, 0.0, 1.0)
    keyword_factor = _clamp(keyword_hits / 3.0, 0.0, 1.0)
    return _clamp((length_factor * 0.35) + (keyword_factor * 0.65), 0.0, 1.0)


def _downside_gap_ratio(value, baseline):
    if baseline is None or baseline <= 0:
        return 0.0
    if value >= baseline:
        return 0.0
    return _clamp((baseline - value) / baseline, 0.0, 1.0)


def _downside_gap_boolean(value, baseline_rate):
    if baseline_rate is None:
        return 0.0
    if value:
        return 0.0
    return _clamp(float(baseline_rate), 0.0, 1.0)


def _clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))
