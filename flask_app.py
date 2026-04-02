from datetime import datetime, timezone
import re
from typing import Any, cast

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from app_runtime import CANONICAL_V1_DESCRIPTION, analyze_repository, get_persistence_store  # pyright: ignore[reportImplicitRelativeImport]
from modules.repo_ingestion.repo_ingestion import GitHubAPIError  # pyright: ignore[reportImplicitRelativeImport]
from services.persistence import RankingQuery  # pyright: ignore[reportImplicitRelativeImport]

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

FEEDBACK_KIND = 'credibility_vote'
FEEDBACK_AUTHORITY = 'supplemental_only'
FEEDBACK_DEDUPE_WINDOW_MINUTES = 60
FEEDBACK_RATE_LIMIT_SECONDS = 60
SUPPORTED_FEEDBACK_VOTES = {'support', 'disagree', 'needs_review'}
USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_.-]{3,32}$')

RANKING_DISCLOSURE = (
    'Only analyzed repositories persisted by this app are included. '
    'Primary ordering is based on persisted risk snapshots or selected snapshot metadata; '
    'feedback is supplemental and never authoritative for rank ordering.'
)

SUPPORTED_RANK_SORTS = {
    'latest_fake_risk_score': 'Latest risk score',
    'snapshot_at': 'Latest update time',
    'stargazers_count': 'GitHub stars',
}


def _current_feedback_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _parse_iso8601(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


def _current_feedback_auth() -> dict[str, str | bool]:
    identity = str(session.get('feedback_identity', '')).strip()
    username = str(session.get('feedback_username', '')).strip()
    return {
        'authenticated': bool(identity),
        'identity': identity,
        'username': username,
    }


def _require_feedback_identity() -> str:
    auth = _current_feedback_auth()
    identity = str(auth['identity']).strip()
    if not identity:
        raise PermissionError('Feedback submission requires an authenticated identity')
    return identity


def _normalize_username(raw_username: str) -> str:
    username = raw_username.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError('Username must be 3-32 chars using letters, numbers, dot, dash, or underscore')
    return username


def _normalize_feedback_vote(raw_vote: object) -> str:
    vote = str(raw_vote).strip().lower()
    if vote not in SUPPORTED_FEEDBACK_VOTES:
        raise ValueError('Unsupported feedback vote')
    return vote


def _normalize_feedback_note(raw_note: object) -> str:
    note = str(raw_note or '').strip()
    if len(note) > 280:
        note = note[:280]
    return note


def _mask_actor_identity(actor_identity: str) -> str:
    _, _, raw_value = actor_identity.partition(':')
    value = raw_value or actor_identity
    if len(value) <= 2:
        return value
    return f'{value[:2]}***'


def _check_feedback_rate_limit(repo_url: str, actor_identity: str, submitted_at: str) -> None:
    submitted_dt = _parse_iso8601(submitted_at)
    for record in get_persistence_store().list_feedback(repo_url):
        if str(record.get('actor_identity', '')).strip() != actor_identity:
            continue
        previous_dt = _parse_iso8601(str(record['submitted_at']))
        delta_seconds = abs((submitted_dt - previous_dt).total_seconds())
        if delta_seconds < FEEDBACK_RATE_LIMIT_SECONDS:
            raise RuntimeError('Feedback rate limit exceeded')


def _build_feedback_payload(repo_url: str) -> dict[str, object]:
    feedback_records = get_persistence_store().list_feedback(repo_url)
    recent_activity: list[dict[str, str]] = []
    for record in feedback_records[:5]:
        payload = cast(dict[str, Any], record.get('payload', {}))
        recent_activity.append(
            {
                'vote': str(payload.get('vote', '')).strip().lower(),
                'submitted_at': str(record.get('submitted_at', '')),
                'actor_label': _mask_actor_identity(str(record.get('actor_identity', ''))),
            }
        )
    return {
        'authority': FEEDBACK_AUTHORITY,
        'summary': _build_feedback_summary(repo_url),
        'recent_activity': recent_activity,
        'dedupe_window_minutes': FEEDBACK_DEDUPE_WINDOW_MINUTES,
        'rate_limit_seconds': FEEDBACK_RATE_LIMIT_SECONDS,
        'allowed_votes': sorted(SUPPORTED_FEEDBACK_VOTES),
    }


def _build_flow_navigation(repo_url: str | None = None) -> dict[str, str]:
    navigation = {
        'analyze_url': url_for('index'),
        'rankings_url': url_for('rankings'),
    }
    if repo_url:
        navigation['detail_url'] = url_for('repo_detail', repo_url=repo_url)
        navigation['api_detail_url'] = url_for('api_repo_detail', repo_url=repo_url)
        navigation['feedback_url'] = url_for('submit_feedback')
        navigation['api_feedback_url'] = url_for('api_submit_feedback')
    return navigation


def _build_analysis_surface_payload(analysis_data: dict[str, object]) -> dict[str, object]:
    payload = dict(analysis_data)
    snapshot = cast(dict[str, Any], payload['snapshot'])
    repo_identity = cast(dict[str, Any], payload['repo_identity'])
    repo_url = cast(str, repo_identity['repo_url'])
    navigation = _build_flow_navigation(repo_url)
    payload['surface_notice'] = (
        f"Primary V1 surface: {CANONICAL_V1_DESCRIPTION}. "
        f"Snapshot v{snapshot['snapshot_version']} persisted for history and downstream detail views."
    )
    payload['detail_url'] = navigation['detail_url']
    payload['rankings_url'] = navigation['rankings_url']
    payload['navigation'] = navigation
    return payload


def _normalize_detail_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(snapshot)
    if 'scoring_result' in normalized and isinstance(normalized['scoring_result'], dict):
        return normalized

    normalized['scoring_result'] = {
        'fake_risk_score': normalized.get('fake_risk_score'),
        'risk_level': normalized.get('risk_level'),
        'risk_band': normalized.get('risk_band'),
        'dimension_scores': normalized.get('dimension_scores', {}),
        'evidence_cards': normalized.get('evidence_cards', []),
        'guardrail_notes': normalized.get('guardrail_notes', []),
        'peer_baseline_summary': normalized.get('peer_baseline_summary', ''),
        'peer_baseline_meta': normalized.get('peer_baseline_meta', {}),
        'version': normalized.get('version', ''),
    }
    return normalized


def _record_feedback_submission(repo_url: str, vote: object, note: object) -> dict[str, object]:
    actor_identity = _require_feedback_identity()
    normalized_vote = _normalize_feedback_vote(vote)
    normalized_note = _normalize_feedback_note(note)
    submitted_at = _current_feedback_timestamp()
    _check_feedback_rate_limit(repo_url, actor_identity, submitted_at)
    result = cast(
        dict[str, Any],
        get_persistence_store().record_feedback(
            repo_url=repo_url,
            actor_identity=actor_identity,
            feedback_kind=FEEDBACK_KIND,
            payload={'vote': normalized_vote, 'note': normalized_note},
            submitted_at=submitted_at,
            dedupe_window_minutes=FEEDBACK_DEDUPE_WINDOW_MINUTES,
        ),
    )
    return {
        'authority': FEEDBACK_AUTHORITY,
        'outcome': 'created' if bool(result['created']) else 'duplicate_collapsed',
        'created': bool(result['created']),
        'dedupe_bucket_start': str(result['dedupe_bucket_start']),
        'summary': _build_feedback_summary(repo_url),
    }

def main():
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'], endpoint='analyze')
def analyze_view():
    repo_url = request.form.get('repo_url', '').strip()
    
    if not repo_url:
        flash('Please enter a GitHub repository URL', 'warning')
        return redirect(url_for('index'))
    
    try:
        analysis_data = _build_analysis_surface_payload(cast(dict[str, object], analyze_repository(repo_url)))
        return render_template('results.html', data=analysis_data)
        
    except ValueError as e:
        flash(f'Input error: {str(e)}', 'error')
        return redirect(url_for('index'))
    except GitHubAPIError as e:
        status_code = getattr(e, "status_code", None)
        if status_code is None:
            flash(f'GitHub API error: {str(e)}', 'error')
        else:
            flash(f'GitHub API error: {str(e)} (Status code: {status_code})', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

def _get_repo_url_from_json_request() -> str:
    data = request.get_json()
    if not data or 'repo_url' not in data:
        raise ValueError('Missing repo_url parameter')
    repo_url = data['repo_url'].strip()
    if not repo_url:
        raise ValueError('Empty repo_url parameter')
    return repo_url


def _json_analyze_response():
    try:
        repo_url = _get_repo_url_from_json_request()
        analysis_data = _build_analysis_surface_payload(cast(dict[str, object], analyze_repository(repo_url)))
        return jsonify({'success': True, **analysis_data})
    except ValueError as e:
        return jsonify({'error': f'Input error: {str(e)}'}), 400
    except GitHubAPIError as e:
        status_code = getattr(e, "status_code", None)
        if status_code is None:
            return jsonify({'error': f'GitHub API error: {str(e)}'}), 502
        return jsonify({'error': f'GitHub API error: {str(e)} (Status code: {status_code})'}), 502
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


def _get_repo_url_from_request_args() -> str:
    repo_url = request.args.get('repo_url', '').strip()
    if not repo_url:
        raise ValueError('Missing repo_url parameter')
    return repo_url


def _build_repo_detail_payload(repo_url: str) -> dict[str, object]:
    history = [_normalize_detail_snapshot(item) for item in get_persistence_store().get_repo_history(repo_url)]
    if not history:
        raise LookupError('No persisted analysis history found for that repository')

    latest = cast(dict[str, Any], history[0])
    latest_scoring = cast(dict[str, Any], latest.get('scoring_result', {}))
    latest_peer_meta = cast(dict[str, Any], latest_scoring.get('peer_baseline_meta', latest.get('peer_baseline_meta', {})))
    retrieval = cast(dict[str, Any], latest.get('peer_retrieval', {}))
    retrieval_meta = cast(dict[str, Any], retrieval.get('retrieval_metadata', {}))

    return {
        'repo_url': repo_url,
        'latest': latest,
        'history': history,
        'latest_peer_meta': latest_peer_meta,
        'retrieval_meta': retrieval_meta,
        'feedback': _build_feedback_payload(repo_url),
        'feedback_auth': _current_feedback_auth(),
        'navigation': _build_flow_navigation(repo_url),
        'has_peer_disclaimer': bool(
            latest_peer_meta.get('sparse_peer')
            or latest_peer_meta.get('low_confidence_peer')
            or retrieval_meta.get('sparse_peer')
            or retrieval_meta.get('low_confidence_peer')
        ),
    }


def _parse_multi_value_arg(name: str) -> tuple[str, ...]:
    values = request.args.getlist(name)
    if not values:
        raw = request.args.get(name, '').strip()
        if raw:
            values = raw.split(',')
    cleaned = [value.strip() for value in values if value and value.strip()]
    return tuple(dict.fromkeys(cleaned))


def _parse_int_query_arg(name: str, default: int) -> int:
    raw = request.args.get(name, '').strip()
    if not raw:
        return default
    return int(raw)


def _build_feedback_summary(repo_url: str) -> dict[str, int | str]:
    feedback_records = get_persistence_store().list_feedback(repo_url)
    support = 0
    disagree = 0
    needs_review = 0
    for record in feedback_records:
        payload = cast(dict[str, Any], record.get('payload', {}))
        vote = str(payload.get('vote', '')).strip().lower()
        if vote == 'support':
            support += 1
        elif vote == 'disagree':
            disagree += 1
        elif vote == 'needs_review':
            needs_review += 1
    total = len(feedback_records)
    summary_parts: list[str] = []
    if support:
        summary_parts.append(f'{support} support signal')
    if disagree:
        summary_parts.append(f'{disagree} disagree signal')
    if needs_review:
        summary_parts.append(f'{needs_review} needs-review signal')
    if not summary_parts:
        summary_parts.append('No supplemental feedback yet')
    return {
        'total': total,
        'support': support,
        'disagree': disagree,
        'needs_review': needs_review,
        'label': ', '.join(summary_parts),
    }


def _build_rankings_payload() -> dict[str, object]:
    sort_by = request.args.get('sort', 'latest_fake_risk_score').strip() or 'latest_fake_risk_score'
    direction = request.args.get('direction', 'desc').strip().lower() or 'desc'
    query = RankingQuery(
        search=request.args.get('search', '').strip() or None,
        languages=_parse_multi_value_arg('language'),
        risk_bands=_parse_multi_value_arg('risk_band'),
        sort_by=sort_by,
        descending=direction != 'asc',
        limit=_parse_int_query_arg('limit', 20),
        offset=_parse_int_query_arg('offset', 0),
    )
    store = get_persistence_store()
    ranking_result = cast(dict[str, Any], store.query_rankings(query))
    items: list[dict[str, Any]] = []
    for item in cast(list[dict[str, Any]], ranking_result['items']):
        items.append(
            {
                **item,
                'detail_url': f"/repos/detail?repo_url={item['repo_url']}",
                'feedback_summary': _build_feedback_summary(cast(str, item['repo_url'])),
            }
        )

    filter_source = cast(dict[str, Any], store.query_rankings(RankingQuery(limit=200, sort_by='snapshot_at')))
    filter_items = cast(list[dict[str, Any]], filter_source['items'])
    available_languages = sorted({str(item['language']) for item in filter_items if item.get('language')})
    available_risk_bands = sorted({str(item['risk_band']) for item in filter_items if item.get('risk_band')})

    return {
        'items': items,
        'total': ranking_result['total'],
        'navigation': _build_flow_navigation(),
        'query': {
            'search': query.search or '',
            'language': ','.join(query.languages),
            'risk_band': ','.join(query.risk_bands),
            'sort': query.sort_by,
            'direction': 'desc' if query.descending else 'asc',
            'limit': query.limit,
            'offset': query.offset,
        },
        'meta': {
            'ordering_basis': query.sort_by,
            'ordering_basis_label': SUPPORTED_RANK_SORTS.get(query.sort_by, query.sort_by),
            'feedback_authority': FEEDBACK_AUTHORITY,
            'disclosure': RANKING_DISCLOSURE,
            'supported_sorts': SUPPORTED_RANK_SORTS,
            'available_languages': available_languages,
            'available_risk_bands': available_risk_bands,
        },
    }


@app.route('/repos/detail')
def repo_detail():
    try:
        repo_url = _get_repo_url_from_request_args()
        detail_data = _build_repo_detail_payload(repo_url)
        return render_template('repo_detail.html', data=detail_data)
    except ValueError as e:
        flash(f'Input error: {str(e)}', 'error')
        return redirect(url_for('index'))
    except LookupError as e:
        flash(str(e), 'warning')
        return redirect(url_for('index'))


@app.route('/api/repos/detail', methods=['GET'])
def api_repo_detail():
    try:
        repo_url = _get_repo_url_from_request_args()
        return jsonify({'success': True, **_build_repo_detail_payload(repo_url)})
    except ValueError as e:
        return jsonify({'error': f'Input error: {str(e)}'}), 400
    except LookupError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    next_url = request.form.get('next', '').strip() or url_for('index')
    try:
        username = _normalize_username(request.form.get('username', ''))
        session['feedback_username'] = username
        session['feedback_identity'] = f'local:{username.lower()}'
        flash(f'Signed in for lightweight feedback as {username}.', 'success')
    except ValueError as e:
        flash(str(e), 'warning')
    return redirect(next_url)


@app.route('/auth/logout', methods=['POST'])
def logout():
    next_url = request.form.get('next', '').strip() or url_for('index')
    session.pop('feedback_username', None)
    session.pop('feedback_identity', None)
    flash('Signed out of lightweight feedback.', 'success')
    return redirect(next_url)


@app.route('/repos/feedback', methods=['POST'])
def submit_feedback():
    repo_url = request.form.get('repo_url', '').strip()
    redirect_target = url_for('repo_detail', repo_url=repo_url) if repo_url else url_for('index')
    try:
        if not repo_url:
            raise ValueError('Missing repo_url parameter')
        feedback = _record_feedback_submission(repo_url, request.form.get('vote', ''), request.form.get('note', ''))
        if bool(feedback['created']):
            flash('Supplemental feedback recorded.', 'success')
        else:
            flash('Duplicate supplemental feedback collapsed into the current dedupe window.', 'info')
    except PermissionError as e:
        flash(str(e), 'warning')
    except RuntimeError as e:
        flash(str(e), 'warning')
    except (LookupError, ValueError) as e:
        flash(str(e), 'warning')
    return redirect(redirect_target)


@app.route('/api/repos/feedback', methods=['POST'])
def api_submit_feedback():
    try:
        data = request.get_json() or {}
        repo_url = str(data.get('repo_url', '')).strip()
        if not repo_url:
            raise ValueError('Missing repo_url parameter')
        feedback = _record_feedback_submission(repo_url, data.get('vote', ''), data.get('note', ''))
        return jsonify({'success': True, 'feedback': feedback})
    except PermissionError as e:
        return jsonify({'error': str(e)}), 401
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 429
    except (LookupError, ValueError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@app.route('/rankings', methods=['GET'])
def rankings():
    try:
        return render_template('rankings.html', data=_build_rankings_payload())
    except ValueError as e:
        flash(f'Input error: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/api/rankings', methods=['GET'])
def api_rankings():
    try:
        return jsonify({'success': True, **_build_rankings_payload()})
    except ValueError as e:
        return jsonify({'error': f'Input error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    return _json_analyze_response()


@app.route('/api/reanalyze', methods=['POST'])
def api_reanalyze():
    return _json_analyze_response()

if __name__ == '__main__':
    main()
