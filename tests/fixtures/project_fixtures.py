from copy import deepcopy
from statistics import mean
from typing import Any, Sequence, TypedDict


class LicenseInfo(TypedDict):
    key: str
    name: str
    spdx_id: str


class RepoMetadata(TypedDict):
    default_branch: str
    fork: bool
    created_at: str
    updated_at: str
    size: int
    language: str
    languages_url: str
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    topics: list[str]
    license: LicenseInfo | None
    description: str
    homepage: str


class FileTreeItem(TypedDict):
    path: str
    type: str
    size: int


class RepoApiPayload(TypedDict):
    repo: RepoMetadata
    readme: str
    tree: list[FileTreeItem]
    languages: dict[str, int]


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
    description: str
    size: int


class RetrievalTargetFeatures(TypedDict):
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


class RetrievalCandidateProject(ProjectFeatures):
    repo_url: str
    cohort: str


class PeerBaseline(TypedDict):
    code_to_doc_ratio_mean: float
    bytes_ratio_mean: float
    max_depth_mean: float
    has_entry_point_rate: float
    has_tests_rate: float
    has_config_files_rate: float
    has_ci_cd_rate: float
    license_file_present_rate: float
    language_distribution: dict[str, float]
    stargazers_count_mean: float
    sample_size: int
    cohorts: list[str]


class ProjectHistorySnapshot(TypedDict):
    snapshot_id: str
    repo_url: str
    cohort: str
    analyzed_at: str
    analysis_revision: str
    peer_baseline_key: str
    project_features: ProjectFeatures | None
    notes: str


class ProjectFixture(TypedDict):
    cohort: str
    description: str
    repo_url: str
    owner: str
    name: str
    language: str
    stargazers_count: int
    size: int
    readme_content: str
    raw_file_tree: list[FileTreeItem]
    file_tree: list[FileTreeItem]
    repo_api: RepoApiPayload
    project_features: ProjectFeatures
    structure_expected: dict[str, Any]
    history_snapshot: ProjectHistorySnapshot

FIXTURE_SCHEMA_VERSION = "v1"
REQUIRED_COHORTS = ("substantive", "hype_heavy", "early_but_real")
PEER_BASELINE_KEY = "fixture-peer-baseline-v1"


PROJECT_FIXTURES: dict[str, ProjectFixture] = {
    "substantive": {
        "cohort": "substantive",
        "description": "Production-grade training and evaluation toolkit for small language models.",
        "repo_url": "https://github.com/acme-labs/openweights",
        "owner": "acme-labs",
        "name": "openweights",
        "language": "Python",
        "stargazers_count": 1850,
        "size": 54000,
        "readme_content": (
            "# OpenWeights\n\n"
            "A practical toolkit for reproducible model training, evaluation, and release notes.\n\n"
            "## Installation\n"
            "pip install openweights\n\n"
            "## Usage\n"
            "Includes examples, benchmarks, and deployment notes.\n"
        ),
        "raw_file_tree": [
            {"path": "README.md", "type": "blob", "size": 2600},
            {"path": "src", "type": "tree", "size": 0},
            {"path": "src/app.py", "type": "blob", "size": 2400},
            {"path": "src/__init__.py", "type": "blob", "size": 120},
            {"path": "src/pipelines", "type": "tree", "size": 0},
            {"path": "src/pipelines/training.py", "type": "blob", "size": 4096},
            {"path": "src/pipelines/eval.py", "type": "blob", "size": 3072},
            {"path": "tests", "type": "tree", "size": 0},
            {"path": "tests/test_core.py", "type": "blob", "size": 1536},
            {"path": "docs", "type": "tree", "size": 0},
            {"path": "docs/architecture.md", "type": "blob", "size": 1800},
            {"path": "pyproject.toml", "type": "blob", "size": 920},
            {"path": "LICENSE", "type": "blob", "size": 1100},
            {"path": ".github", "type": "tree", "size": 0},
            {"path": ".github/workflows/ci.yml", "type": "blob", "size": 800},
        ],
        "file_tree": [
            {"path": "README.md", "type": "file", "size": 2600},
            {"path": "src", "type": "dir", "size": 0},
            {"path": "src/app.py", "type": "file", "size": 2400},
            {"path": "src/__init__.py", "type": "file", "size": 120},
            {"path": "src/pipelines", "type": "dir", "size": 0},
            {"path": "src/pipelines/training.py", "type": "file", "size": 4096},
            {"path": "src/pipelines/eval.py", "type": "file", "size": 3072},
            {"path": "tests", "type": "dir", "size": 0},
            {"path": "tests/test_core.py", "type": "file", "size": 1536},
            {"path": "docs", "type": "dir", "size": 0},
            {"path": "docs/architecture.md", "type": "file", "size": 1800},
            {"path": "pyproject.toml", "type": "file", "size": 920},
            {"path": "LICENSE", "type": "file", "size": 1100},
            {"path": ".github", "type": "dir", "size": 0},
            {"path": ".github/workflows/ci.yml", "type": "file", "size": 800},
        ],
        "repo_api": {
            "repo": {
                "default_branch": "main",
                "fork": False,
                "created_at": "2024-02-01T00:00:00Z",
                "updated_at": "2026-03-30T16:00:00Z",
                "size": 54000,
                "language": "Python",
                "languages_url": "https://api.github.com/repos/acme-labs/openweights/languages",
                "stargazers_count": 1850,
                "forks_count": 220,
                "open_issues_count": 31,
                "topics": ["machine-learning", "evaluation", "tooling"],
                "license": {"key": "apache-2.0", "name": "Apache License 2.0", "spdx_id": "Apache-2.0"},
                "description": "Production-grade training and evaluation toolkit for small language models",
                "homepage": "https://openweights.dev",
            },
            "readme": (
                "# OpenWeights\n\n"
                "A practical toolkit for reproducible model training, evaluation, and release notes.\n\n"
                "## Installation\n"
                "pip install openweights\n"
            ),
            "tree": [
                {"path": "README.md", "type": "blob", "size": 2600},
                {"path": "src", "type": "tree", "size": 0},
                {"path": "src/app.py", "type": "blob", "size": 2400},
                {"path": "src/__init__.py", "type": "blob", "size": 120},
                {"path": "src/pipelines", "type": "tree", "size": 0},
                {"path": "src/pipelines/training.py", "type": "blob", "size": 4096},
                {"path": "src/pipelines/eval.py", "type": "blob", "size": 3072},
                {"path": "tests", "type": "tree", "size": 0},
                {"path": "tests/test_core.py", "type": "blob", "size": 1536},
                {"path": "docs", "type": "tree", "size": 0},
                {"path": "docs/architecture.md", "type": "blob", "size": 1800},
                {"path": "pyproject.toml", "type": "blob", "size": 920},
                {"path": "LICENSE", "type": "blob", "size": 1100},
                {"path": ".github", "type": "tree", "size": 0},
                {"path": ".github/workflows/ci.yml", "type": "blob", "size": 800},
            ],
            "languages": {"Python": 42000, "Markdown": 8500, "YAML": 2500, "TOML": 1000},
        },
        "project_features": {
            "code_to_doc_ratio": 2.3333333333333335,
            "bytes_ratio": 2.3534545454545454,
            "max_depth": 2,
            "has_entry_point": True,
            "has_tests": True,
            "has_config_files": True,
            "has_ci_cd": True,
            "license_file_present": True,
            "file_type_distribution": {".md": 2, ".py": 5, ".toml": 1, ".yml": 1, "": 1},
            "language": "Python",
            "stargazers_count": 1850,
            "description": "Production-grade training and evaluation toolkit for small language models.",
            "size": 54000,
        },
        "structure_expected": {
            "file_count": 10,
            "dir_count": 7,
            "code_files": 7,
            "doc_files": 3,
            "code_to_doc_ratio": 2.3333333333333335,
            "code_bytes": 12944,
            "doc_bytes": 5500,
            "bytes_ratio": 2.3534545454545454,
            "max_depth": 2,
            "avg_depth": 0.7333333333333333,
            "file_type_distribution": {".md": 2, ".py": 5, ".toml": 1, ".yml": 1, "": 1},
            "has_entry_point": True,
            "has_tests": True,
            "has_config_files": True,
            "has_ci_cd": True,
            "license_file_present": True,
        },
        "history_snapshot": {
            "snapshot_id": "history-substantive-001",
            "repo_url": "https://github.com/acme-labs/openweights",
            "cohort": "substantive",
            "analyzed_at": "2026-03-30T16:00:00Z",
            "analysis_revision": FIXTURE_SCHEMA_VERSION,
            "peer_baseline_key": PEER_BASELINE_KEY,
            "project_features": None,
            "notes": "Clear substantive benchmark with strong delivery and evidence signals.",
        },
    },
    "hype_heavy": {
        "cohort": "hype_heavy",
        "description": "A narrative-first AI launch brand with minimal shipping code.",
        "repo_url": "https://github.com/vision-summit/ai-revolution",
        "owner": "vision-summit",
        "name": "ai-revolution",
        "language": "JavaScript",
        "stargazers_count": 9800,
        "size": 5000,
        "readme_content": (
            "# AI Revolution\n\n"
            "The most ambitious AI platform ever described.\n\n"
            "## Vision\n"
            "Reinvent everything with AI.\n"
        ),
        "raw_file_tree": [
            {"path": "README.md", "type": "blob", "size": 1800},
            {"path": "docs", "type": "tree", "size": 0},
            {"path": "docs/vision.md", "type": "blob", "size": 1200},
            {"path": "docs/launch-plan.md", "type": "blob", "size": 1100},
            {"path": "marketing", "type": "tree", "size": 0},
            {"path": "marketing/press-release.md", "type": "blob", "size": 1300},
            {"path": "prototype", "type": "tree", "size": 0},
            {"path": "prototype/widget.js", "type": "blob", "size": 220},
            {"path": "prototype/landing.html", "type": "blob", "size": 340},
        ],
        "file_tree": [
            {"path": "README.md", "type": "file", "size": 1800},
            {"path": "docs", "type": "dir", "size": 0},
            {"path": "docs/vision.md", "type": "file", "size": 1200},
            {"path": "docs/launch-plan.md", "type": "file", "size": 1100},
            {"path": "marketing", "type": "dir", "size": 0},
            {"path": "marketing/press-release.md", "type": "file", "size": 1300},
            {"path": "prototype", "type": "dir", "size": 0},
            {"path": "prototype/widget.js", "type": "file", "size": 220},
            {"path": "prototype/landing.html", "type": "file", "size": 340},
        ],
        "repo_api": {
            "repo": {
                "default_branch": "main",
                "fork": False,
                "created_at": "2025-10-01T00:00:00Z",
                "updated_at": "2026-03-28T08:00:00Z",
                "size": 5000,
                "language": "JavaScript",
                "languages_url": "https://api.github.com/repos/vision-summit/ai-revolution/languages",
                "stargazers_count": 9800,
                "forks_count": 11,
                "open_issues_count": 2,
                "topics": ["ai", "launch", "product"],
                "license": None,
                "description": "A narrative-first AI launch brand with minimal shipping code",
                "homepage": "https://ai-revolution.example.com",
            },
            "readme": (
                "# AI Revolution\n\n"
                "The most ambitious AI platform ever described.\n\n"
                "## Vision\n"
                "Reinvent everything with AI.\n"
            ),
            "tree": [
                {"path": "README.md", "type": "blob", "size": 1800},
                {"path": "docs", "type": "tree", "size": 0},
                {"path": "docs/vision.md", "type": "blob", "size": 1200},
                {"path": "docs/launch-plan.md", "type": "blob", "size": 1100},
                {"path": "marketing", "type": "tree", "size": 0},
                {"path": "marketing/press-release.md", "type": "blob", "size": 1300},
                {"path": "prototype", "type": "tree", "size": 0},
                {"path": "prototype/widget.js", "type": "blob", "size": 220},
                {"path": "prototype/landing.html", "type": "blob", "size": 340},
            ],
            "languages": {"Markdown": 4500, "JavaScript": 500},
        },
        "project_features": {
            "code_to_doc_ratio": 0.5,
            "bytes_ratio": 0.1037037037037037,
            "max_depth": 1,
            "has_entry_point": False,
            "has_tests": False,
            "has_config_files": False,
            "has_ci_cd": False,
            "license_file_present": False,
            "file_type_distribution": {".md": 4, ".js": 1, ".html": 1},
            "language": "JavaScript",
            "stargazers_count": 9800,
            "description": "A narrative-first AI launch brand with minimal shipping code.",
            "size": 5000,
        },
        "structure_expected": {
            "file_count": 6,
            "dir_count": 4,
            "code_files": 2,
            "doc_files": 4,
            "code_to_doc_ratio": 0.5,
            "code_bytes": 560,
            "doc_bytes": 5400,
            "bytes_ratio": 0.1037037037037037,
            "max_depth": 1,
            "avg_depth": 0.5555555555555556,
            "file_type_distribution": {".md": 4, ".js": 1, ".html": 1},
            "has_entry_point": False,
            "has_tests": False,
            "has_config_files": False,
            "has_ci_cd": False,
            "license_file_present": False,
        },
        "history_snapshot": {
            "snapshot_id": "history-hype-heavy-001",
            "repo_url": "https://github.com/vision-summit/ai-revolution",
            "cohort": "hype_heavy",
            "analyzed_at": "2026-03-30T16:00:00Z",
            "analysis_revision": FIXTURE_SCHEMA_VERSION,
            "peer_baseline_key": PEER_BASELINE_KEY,
            "project_features": None,
            "notes": "Marketing-led reference case with weak delivery and evidence signals.",
        },
    },
    "early_but_real": {
        "cohort": "early_but_real",
        "description": "A small but honest CLI for annotating model outputs with tests and docs.",
        "repo_url": "https://github.com/seedline/annotator",
        "owner": "seedline",
        "name": "annotator",
        "language": "Python",
        "stargazers_count": 56,
        "size": 12000,
        "readme_content": (
            "# Annotator\n\n"
            "A compact CLI for annotating model outputs.\n\n"
            "## Usage\n"
            "Run the CLI, inspect examples, and execute tests locally.\n"
        ),
        "raw_file_tree": [
            {"path": "README.md", "type": "blob", "size": 1400},
            {"path": "src", "type": "tree", "size": 0},
            {"path": "src/main.py", "type": "blob", "size": 1800},
            {"path": "src/service.py", "type": "blob", "size": 2100},
            {"path": "src/cli.py", "type": "blob", "size": 900},
            {"path": "tests", "type": "tree", "size": 0},
            {"path": "tests/test_service.py", "type": "blob", "size": 1500},
            {"path": "docs", "type": "tree", "size": 0},
            {"path": "docs/usage.md", "type": "blob", "size": 900},
            {"path": "LICENSE", "type": "blob", "size": 1100},
            {"path": "pyproject.toml", "type": "blob", "size": 650},
        ],
        "file_tree": [
            {"path": "README.md", "type": "file", "size": 1400},
            {"path": "src", "type": "dir", "size": 0},
            {"path": "src/main.py", "type": "file", "size": 1800},
            {"path": "src/service.py", "type": "file", "size": 2100},
            {"path": "src/cli.py", "type": "file", "size": 900},
            {"path": "tests", "type": "dir", "size": 0},
            {"path": "tests/test_service.py", "type": "file", "size": 1500},
            {"path": "docs", "type": "dir", "size": 0},
            {"path": "docs/usage.md", "type": "file", "size": 900},
            {"path": "LICENSE", "type": "file", "size": 1100},
            {"path": "pyproject.toml", "type": "file", "size": 650},
        ],
        "repo_api": {
            "repo": {
                "default_branch": "main",
                "fork": False,
                "created_at": "2025-08-12T00:00:00Z",
                "updated_at": "2026-03-29T12:30:00Z",
                "size": 12000,
                "language": "Python",
                "languages_url": "https://api.github.com/repos/seedline/annotator/languages",
                "stargazers_count": 56,
                "forks_count": 4,
                "open_issues_count": 1,
                "topics": ["cli", "annotation", "mlops"],
                "license": {"key": "mit", "name": "MIT License", "spdx_id": "MIT"},
                "description": "A compact CLI for annotating model outputs with tests and docs",
                "homepage": "https://annotator.example.com",
            },
            "readme": (
                "# Annotator\n\n"
                "A compact CLI for annotating model outputs.\n\n"
                "## Usage\n"
                "Run the CLI, inspect examples, and execute tests locally.\n"
            ),
            "tree": [
                {"path": "README.md", "type": "blob", "size": 1400},
                {"path": "src", "type": "tree", "size": 0},
                {"path": "src/main.py", "type": "blob", "size": 1800},
                {"path": "src/service.py", "type": "blob", "size": 2100},
                {"path": "src/cli.py", "type": "blob", "size": 900},
                {"path": "tests", "type": "tree", "size": 0},
                {"path": "tests/test_service.py", "type": "blob", "size": 1500},
                {"path": "docs", "type": "tree", "size": 0},
                {"path": "docs/usage.md", "type": "blob", "size": 900},
                {"path": "LICENSE", "type": "blob", "size": 1100},
                {"path": "pyproject.toml", "type": "blob", "size": 650},
            ],
            "languages": {"Python": 8200, "Markdown": 2600, "TOML": 650},
        },
        "project_features": {
            "code_to_doc_ratio": 1.6666666666666667,
            "bytes_ratio": 2.0441176470588234,
            "max_depth": 1,
            "has_entry_point": True,
            "has_tests": True,
            "has_config_files": True,
            "has_ci_cd": False,
            "license_file_present": True,
            "file_type_distribution": {".md": 2, ".py": 4, ".toml": 1, "": 1},
            "language": "Python",
            "stargazers_count": 56,
            "description": "A small but honest CLI for annotating model outputs with tests and docs.",
            "size": 12000,
        },
        "structure_expected": {
            "file_count": 8,
            "dir_count": 4,
            "code_files": 5,
            "doc_files": 3,
            "code_to_doc_ratio": 1.6666666666666667,
            "code_bytes": 6950,
            "doc_bytes": 3400,
            "bytes_ratio": 2.0441176470588234,
            "max_depth": 1,
            "avg_depth": 0.45454545454545453,
            "file_type_distribution": {".md": 2, ".py": 4, ".toml": 1, "": 1},
            "has_entry_point": True,
            "has_tests": True,
            "has_config_files": True,
            "has_ci_cd": False,
            "license_file_present": True,
        },
        "history_snapshot": {
            "snapshot_id": "history-early-but-real-001",
            "repo_url": "https://github.com/seedline/annotator",
            "cohort": "early_but_real",
            "analyzed_at": "2026-03-30T16:00:00Z",
            "analysis_revision": FIXTURE_SCHEMA_VERSION,
            "peer_baseline_key": PEER_BASELINE_KEY,
            "project_features": None,
            "notes": "Early-stage but credible project with real code, tests, and docs.",
        },
    },
}


RETRIEVAL_TARGET_FEATURES: RetrievalTargetFeatures = {
    "code_to_doc_ratio": 1.5,
    "bytes_ratio": 1.4,
    "max_depth": 2,
    "has_entry_point": True,
    "has_tests": True,
    "has_config_files": True,
    "has_ci_cd": False,
    "license_file_present": True,
    "file_type_distribution": {".py": 4, ".md": 3, ".toml": 1},
    "language": "Python",
    "stargazers_count": 80,
}


def get_project_fixture(cohort: str) -> ProjectFixture:
    return deepcopy(PROJECT_FIXTURES[cohort])


def get_project_fixtures() -> list[ProjectFixture]:
    return [get_project_fixture(cohort) for cohort in REQUIRED_COHORTS]


def retrieval_candidate_projects() -> list[RetrievalCandidateProject]:
    return [
        {"repo_url": fixture["repo_url"], **deepcopy(fixture["project_features"]), "cohort": fixture["cohort"]}
        for fixture in get_project_fixtures()
    ]


def retrieval_target_features() -> RetrievalTargetFeatures:
    return deepcopy(RETRIEVAL_TARGET_FEATURES)


def build_peer_baseline(projects: Sequence[ProjectFixture] | None = None) -> PeerBaseline:
    source = get_project_fixtures() if projects is None else [deepcopy(project) for project in projects]
    feature_rows = [project["project_features"] for project in source]
    count = len(feature_rows)
    if count == 0:
        baseline: PeerBaseline = {
            "code_to_doc_ratio_mean": 0.0,
            "bytes_ratio_mean": 0.0,
            "max_depth_mean": 0.0,
            "has_entry_point_rate": 0.0,
            "has_tests_rate": 0.0,
            "has_config_files_rate": 0.0,
            "has_ci_cd_rate": 0.0,
            "license_file_present_rate": 0.0,
            "language_distribution": {},
            "stargazers_count_mean": 0.0,
            "sample_size": 0,
            "cohorts": [],
        }
        return baseline

    baseline: PeerBaseline = {
        "code_to_doc_ratio_mean": mean(project["code_to_doc_ratio"] for project in feature_rows),
        "bytes_ratio_mean": mean(project["bytes_ratio"] for project in feature_rows),
        "max_depth_mean": mean(project["max_depth"] for project in feature_rows),
        "has_entry_point_rate": mean(1.0 if project["has_entry_point"] else 0.0 for project in feature_rows),
        "has_tests_rate": mean(1.0 if project["has_tests"] else 0.0 for project in feature_rows),
        "has_config_files_rate": mean(1.0 if project["has_config_files"] else 0.0 for project in feature_rows),
        "has_ci_cd_rate": mean(1.0 if project["has_ci_cd"] else 0.0 for project in feature_rows),
        "license_file_present_rate": mean(1.0 if project["license_file_present"] else 0.0 for project in feature_rows),
        "language_distribution": _language_distribution(feature_rows),
        "stargazers_count_mean": mean(project["stargazers_count"] for project in feature_rows),
        "sample_size": count,
        "cohorts": [project.get("cohort", "unknown") for project in source],
    }
    return baseline


def history_snapshots() -> list[ProjectHistorySnapshot]:
    snapshots: list[ProjectHistorySnapshot] = []
    for fixture in get_project_fixtures():
        snapshot = deepcopy(fixture["history_snapshot"])
        snapshot["project_features"] = deepcopy(fixture["project_features"])
        snapshots.append(snapshot)
    return snapshots


def build_repo_ingestion_payloads(cohort: str = "substantive") -> RepoApiPayload:
    fixture = get_project_fixture(cohort)
    return deepcopy(fixture["repo_api"])


def _language_distribution(feature_rows: Sequence[ProjectFeatures]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for project in feature_rows:
        language = project["language"]
        counts[language] = counts.get(language, 0) + 1

    total = sum(counts.values()) or 1
    return {language: count / total for language, count in sorted(counts.items())}
