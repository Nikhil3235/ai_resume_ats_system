import os
import logging
from pathlib import Path
from typing import Any, Dict
import streamlit as st
from supabase import Client, create_client

logger = logging.getLogger('ats_resume_scorer')


try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / '.env')
except ImportError:
    pass


def _secret(key: str, section: str = 'supabase') -> str:
    """Read from env first, then st.secrets[key], then st.secrets[section][key]."""
    val = os.getenv(key, '')
    if val:
        return val
    try:
        if hasattr(st, 'secrets'):
            if key in st.secrets:
                return str(st.secrets[key])
            if section in st.secrets and key in st.secrets[section]:
                return str(st.secrets[section][key])
    except Exception:
        pass
    return ''


import tempfile

_CACHE_FILE = Path(tempfile.gettempdir()) / 'ats_pkce_verifiers.txt'
_IN_MEMORY_VERIFIERS: list[str] = []

def _save_verifier(v: str) -> None:
    if not v:
        return
    if v not in _IN_MEMORY_VERIFIERS:
        _IN_MEMORY_VERIFIERS.append(v)
    try:
        with open(_CACHE_FILE, 'a', encoding='utf-8') as f:
            f.write(v + '\n')
    except Exception:
        pass

def _get_all_verifiers() -> list[str]:
    results = list(_IN_MEMORY_VERIFIERS)
    try:
        if _CACHE_FILE.exists():
            with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    item = line.strip()
                    if item and item not in results:
                        results.append(item)
    except Exception:
        pass
    return list(reversed(results[-30:]))


SUPABASE_URL = _secret('SUPABASE_URL')
SUPABASE_ANON_KEY = _secret('SUPABASE_ANON_KEY')


def get_oauth_redirect_url() -> str:
    """Dynamically determine current app URL to prevent redirecting cloud traffic to localhost."""
    explicit = os.getenv('AUTH_REDIRECT_URL') or _secret('AUTH_REDIRECT_URL') or _secret('redirect_uri', 'google_oauth')
    if explicit:
        return explicit.rstrip('/')

    try:
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            headers = st.context.headers
            host = headers.get('x-forwarded-host') or headers.get('host')
            if host:
                proto = headers.get('x-forwarded-proto') or ('https' if 'streamlit.app' in host else 'http')
                return f"{proto}://{host}".rstrip('/')
    except Exception:
        pass

    return 'http://localhost:8501'


OAUTH_REDIRECT_URL = get_oauth_redirect_url()


def _missing_config() -> str | None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return 'Supabase is not configured — set SUPABASE_URL and SUPABASE_ANON_KEY in .env or .streamlit/secrets.toml'
    return None


@st.cache_resource
def get_client() -> Client | None:
    """Cached singleton — preserves PKCE state across Streamlit reruns."""
    if _missing_config():
        return None
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def _session_dict(session, user) -> Dict[str, Any]:
    return {
        'access_token':  session.access_token,
        'refresh_token': session.refresh_token,
        'user_id':       user.id,
        'email':         user.email,
    }


def sign_in_with_password(email: str, password: str) -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        resp = get_client().auth.sign_in_with_password(
            {'email': email, 'password': password}
        )
        if not resp.session or not resp.user:
            return {'error': 'Invalid credentials'}
        return _session_dict(resp.session, resp.user)
    except Exception as exc:
        logger.warning(f'sign_in_with_password failed: {exc}')
        return {'error': _humanize(exc)}


def sign_up_with_password(email: str, password: str) -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        resp = get_client().auth.sign_up({
            'email': email,
            'password': password,
            'options': {'email_redirect_to': OAUTH_REDIRECT_URL}
        })
        if resp.session and resp.user:
            return _session_dict(resp.session, resp.user)
        if resp.user:
            return {'pending_confirmation': True, 'email': email}
        return {'error': 'Sign-up failed'}
    except Exception as exc:
        logger.warning(f'sign_up failed: {exc}')
        return {'error': _humanize(exc)}


def google_oauth_url() -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        redirect_to = get_oauth_redirect_url()
        client = get_client()
        resp = client.auth.sign_in_with_oauth({
            'provider': 'google',
            'options': {'redirect_to': redirect_to},
        })
        storage_key = f'{client.auth._storage_key}-code-verifier'
        verifier = client.auth._storage.get_item(storage_key) or ''
        if verifier:
            _save_verifier(verifier)
        return {'url': resp.url, 'verifier': verifier}
    except Exception as exc:
        logger.warning(f'oauth url generation failed: {exc}')
        return {'error': _humanize(exc)}


def exchange_code_for_session(auth_code: str) -> Dict[str, Any]:
    """Called once after the OAuth provider redirects back with `?code=...`."""
    err = _missing_config()
    if err:
        return {'error': err}
    client = get_client()
    redirect_to = get_oauth_redirect_url()

    storage_key = f'{client.auth._storage_key}-code-verifier'
    current_v = client.auth._storage.get_item(storage_key) or ''

    candidates = []
    if current_v:
        candidates.append(current_v)
    for v in _get_all_verifiers():
        if v not in candidates:
            candidates.append(v)

    last_err = None
    for code_verifier in candidates:
        try:
            resp = client.auth.exchange_code_for_session({
                'auth_code': auth_code,
                'code_verifier': code_verifier,
                'redirect_to': redirect_to,
            })
            if resp.session and resp.user:
                return _session_dict(resp.session, resp.user)
        except Exception as exc:
            last_err = exc
            continue

    logger.warning(f'exchange_code_for_session failed across all candidates: {last_err}')
    return {'error': _humanize(last_err or Exception('PKCE verification failed'))}


def sign_out() -> None:
    if _missing_config():
        return
    try:
        get_client().auth.sign_out()
    except Exception as exc:
        logger.warning(f'sign_out failed: {exc}')


def _humanize(exc: Exception) -> str:
    msg = str(exc)
    # supabase errors arrive as "<status>: {json blob}" — surface the human bit
    if 'invalid_grant' in msg.lower() or 'invalid login' in msg.lower():
        return 'Wrong email or password'
    if 'user already registered' in msg.lower() or 'already been registered' in msg.lower():
        return 'An account with this email already exists — try signing in'
    if 'password should be at least' in msg.lower():
        return 'Password too short (Supabase default is 6 characters)'
    return msg
