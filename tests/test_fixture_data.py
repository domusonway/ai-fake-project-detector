from .fixtures import (
    REQUIRED_COHORTS,
    build_peer_baseline,
    get_project_fixtures,
    history_snapshots,
    retrieval_candidate_projects,
    retrieval_target_features,
)


def test_fixture_cohorts_are_labeled_and_complete():
    fixtures = get_project_fixtures()

    assert [fixture["cohort"] for fixture in fixtures] == list(REQUIRED_COHORTS)
    assert {fixture["cohort"] for fixture in fixtures} == set(REQUIRED_COHORTS)
    assert all("project_features" in fixture for fixture in fixtures)
    assert all("history_snapshot" in fixture for fixture in fixtures)


def test_peer_baseline_is_deterministic_and_offline():
    baseline = build_peer_baseline()

    assert baseline["sample_size"] == 3
    assert baseline["cohorts"] == list(REQUIRED_COHORTS)
    assert baseline["language_distribution"]
    assert 0 <= baseline["has_tests_rate"] <= 1
    assert 0 <= baseline["license_file_present_rate"] <= 1


def test_retrieval_and_history_fixtures_cover_required_shapes():
    candidates = retrieval_candidate_projects()
    snapshots = history_snapshots()
    target = retrieval_target_features()

    assert len(candidates) == 3
    assert {candidate["cohort"] for candidate in candidates} == set(REQUIRED_COHORTS)
    assert all("repo_url" in candidate for candidate in candidates)
    assert target["has_entry_point"] is True
    assert len(snapshots) == 3
    assert {snapshot["cohort"] for snapshot in snapshots} == set(REQUIRED_COHORTS)
