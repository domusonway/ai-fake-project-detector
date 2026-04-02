"""
Debug script to understand scoring logic
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from modules.scoring_engine.scoring_engine import compute_fake_risk_score

# Test data from the failing tests
PROJECT_FEATURES = {
    "code_to_doc_ratio": 2.5,
    "bytes_ratio": 3.0,
    "max_depth": 2,
    "has_entry_point": True,
    "has_tests": True,
    "has_config_files": True,
    "has_ci_cd": False,
    "license_file_present": True,
    "file_type_distribution": {".py": 15, ".md": 3, ".txt": 2},
    "language": "Python",
    "stargazers_count": 500,
    "description": "A state-of-the-art AI framework for machine learning and deep learning",
    "size": 15360
}

PEER_BASELINE = {
    "code_to_doc_ratio_mean": 2.0,
    "bytes_ratio_mean": 2.5,
    "max_depth_mean": 1.5,
    "has_entry_point_rate": 0.8,
    "has_tests_rate": 0.7,
    "has_config_files_rate": 0.9,
    "has_ci_cd_rate": 0.3,
    "license_file_present_rate": 0.8,
    "language_distribution": {"Python": 0.6, "JavaScript": 0.2, "Other": 0.2},
    "stargazers_count_mean": 300
}

VOTING_SIGNALS = {
    "vote_count": 42,
    "positive_ratio": 0.75,
    "controversy_score": 0.2
}

print("=== NORMAL PROJECT ===")
result = compute_fake_risk_score(
    project_features=PROJECT_FEATURES,
    peer_baseline=PEER_BASELINE,
    voting_signals=VOTING_SIGNALS
)
print(f"Fake risk score: {result['fake_risk_score']}")
print(f"Risk level: {result['risk_level']}")
print(f"Dimension scores: {result['dimension_scores']}")

print("\n=== HIGH RISK PROJECT (should be bad) ===")
high_risk_features = PROJECT_FEATURES.copy()
high_risk_features.update({
    "code_to_doc_ratio": 0.1,   # 很少代码
    "bytes_ratio": 0.1,         # 很少代码字节
    "has_entry_point": False,
    "has_tests": False,
    "has_config_files": False,
    "has_ci_cd": False,
    "license_file_present": False,
    "description": "Just marketing content",
    "size": 500
})

result_high = compute_fake_risk_score(
    project_features=high_risk_features,
    peer_baseline=PEER_BASELINE,
    voting_signals=VOTING_SIGNALS
)
print(f"Fake risk score: {result_high['fake_risk_score']}")
print(f"Risk level: {result_high['risk_level']}")
print(f"Dimension scores: {result_high['dimension_scores']}")

print("\n=== LOW RISK PROJECT (should be good) ===")
low_risk_features = PROJECT_FEATURES.copy()
low_risk_features.update({
    "code_to_doc_ratio": 5.0,   # 多代码
    "bytes_ratio": 6.0,         # 多代码字节
    "has_entry_point": True,
    "has_tests": True,
    "has_config_files": True,
    "has_ci_cd": True,
    "license_file_present": True,
    "description": "Detailed implementation with examples and tests",
    "size": 50000
})

result_low = compute_fake_risk_score(
    project_features=low_risk_features,
    peer_baseline=PEER_BASELINE,
    voting_signals=VOTING_SIGNALS
)
print(f"Fake risk score: {result_low['fake_risk_score']}")
print(f"Risk level: {result_low['risk_level']}")
print(f"Dimension scores: {result_low['dimension_scores']}")