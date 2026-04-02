import sys
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

DEMO_SURFACE_NOTICE = (
    'Demo-only mock surface. Use flask_app.py for the canonical V1 web app and JSON API.'
)

# Mock data for demonstration
MOCK_REPO_DATA = {
    "owner": "octocat",
    "name": "Hello-World",
    "description": "This is a test repository",
    "stargazers_count": 42,
    "forks_count": 8,
    "language": "Python",
    "size": 10240,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-06-01T00:00:00Z"
}

MOCK_STRUCTURE_RESULT = {
    "file_count": 15,
    "dir_count": 5,
    "code_files": 10,
    "doc_files": 3,
    "code_to_doc_ratio": 3.33,
    "code_bytes": 24320,
    "doc_bytes": 4352,
    "bytes_ratio": 5.59,
    "max_depth": 2,
    "avg_depth": 1.05,
    "file_type_distribution": {".md": 2, ".py": 10, ".txt": 2, "": 1},
    "has_entry_point": True,
    "has_tests": True,
    "has_config_files": True,
    "has_ci_cd": True,
    "license_file_present": True,
    "readme_quality_score": 0.65,
    "structure_score": 0.95
}

MOCK_SCORING_RESULT = {
    "fake_risk_score": 25.0,
    "risk_level": "low",
    "dimension_scores": {
        "delivery": 25.0,
        "substance": 18.0,
        "evidence": 12.0,
        "peer_gap": 8.0,
        "community": 9.0,
        "hype_gap": 5.0
    },
    "evidence_cards": [
        {
            "type": "code_to_doc_ratio",
            "description": "代码文件与文档文件比例",
            "value": 3.33,
            "threshold": "理想范围: 1.0-10.0",
            "passed": True
        },
        {
            "type": "description_quality",
            "description": "项目描述长度和质量",
            "value": 150,
            "threshold": ">100字符表示基本描述, >500字符表示详细描述",
            "passed": True
        },
        {
            "type": "file_structure",
            "description": "基本文件结构完整度",
            "value": True,
            "threshold": "包含入口点、测试和配置文件",
            "passed": True
        }
    ],
    "guardrail_notes": [
        "评分基于公开仓库数据，不涉及私有代码",
        "评分结果应结合人工审查和业务背景综合判断"
    ],
    "peer_baseline_summary": "与同类Python项目相比，代码结构略高于平均水平"
}

@app.route('/')
def index():
    flash(DEMO_SURFACE_NOTICE, 'warning')
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    repo_url = request.form.get('repo_url', '').strip()
    
    if not repo_url:
        flash('Please enter a GitHub repository URL', 'warning')
        return redirect(url_for('index'))
    
    analysis_data = {
        'repo_info': {
            'owner': MOCK_REPO_DATA['owner'],
            'name': MOCK_REPO_DATA['name'],
            'url': repo_url,
            'description': MOCK_REPO_DATA['description'],
            'stars': MOCK_REPO_DATA['stargazers_count'],
            'forks': MOCK_REPO_DATA['forks_count'],
            'language': MOCK_REPO_DATA['language'],
            'size_kb': MOCK_REPO_DATA['size'],
            'created_at': MOCK_REPO_DATA['created_at'],
            'updated_at': MOCK_REPO_DATA['updated_at']
        },
        'structure_analysis': MOCK_STRUCTURE_RESULT,
        'scoring_result': MOCK_SCORING_RESULT,
        'surface_notice': DEMO_SURFACE_NOTICE,
        'surface_role': 'demo-only',
    }
    
    return render_template('results.html', data=analysis_data)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json()
    if not data or 'repo_url' not in data:
        return jsonify({'error': 'Missing repo_url parameter'}), 400
    
    repo_url = data['repo_url'].strip()
    
    if not repo_url:
        return jsonify({'error': 'Empty repo_url parameter'}), 400
    
    return jsonify({
        'success': True,
        'surface_role': 'demo-only',
        'surface_notice': DEMO_SURFACE_NOTICE,
        'repo_info': {
            'owner': MOCK_REPO_DATA['owner'],
            'name': MOCK_REPO_DATA['name'],
            'url': repo_url,
            'description': MOCK_REPO_DATA['description'],
            'stars': MOCK_REPO_DATA['stargazers_count'],
            'forks': MOCK_REPO_DATA['forks_count'],
            'language': MOCK_REPO_DATA['language'],
            'size_kb': MOCK_REPO_DATA['size']
        },
        'structure_analysis': MOCK_STRUCTURE_RESULT,
        'scoring_result': MOCK_SCORING_RESULT
    })

if __name__ == '__main__':
    print(DEMO_SURFACE_NOTICE, file=sys.stderr)
    app.run(debug=True, host='0.0.0.0', port=5001)
