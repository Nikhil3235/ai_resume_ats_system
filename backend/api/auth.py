import logging
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import SUPABASE_JWT_SECRET, SUPABASE_URL

logger = logging.getLogger('ats_resume_scorer')

_bearer_scheme = HTTPBearer(auto_error=False)

_ASYMMETRIC_ALGS = ['ES256', 'RS256']

_jwks_client: jwt.PyJWKClient | None = None


def _get_jwks_client() -> jwt.PyJWKClient | None:
    global _jwks_client
    if _jwks_client is not None:
        return _jwks_client
    if not SUPABASE_URL:
        return None
    jwks_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    _jwks_client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    return _jwks_client


def _verify_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    alg = header.get('alg')

    if alg in _ASYMMETRIC_ALGS:
        jwks_client = _get_jwks_client()
        if jwks_client is None:
            raise jwt.InvalidTokenError(
                'SUPABASE_URL not configured — cannot fetch JWKS to verify token'
            )
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            signing_key,
            algorithms=_ASYMMETRIC_ALGS,
            audience='authenticated',
        )

    if alg == 'HS256':
        if not SUPABASE_JWT_SECRET:
            raise jwt.InvalidTokenError(
                'HS256 token received but SUPABASE_JWT_SECRET is not configured'
            )
        return jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            audience='authenticated',
        )

    raise jwt.InvalidTokenError(f'Unsupported JWT algorithm: {alg}')


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    # Allow guest evaluations when no token is supplied (e.g. mobile testing, demo evaluations)
    if creds is None or not creds.credentials or creds.credentials in ('guest', 'null', 'none', ''):
        return 'guest'

    if not SUPABASE_URL and not SUPABASE_JWT_SECRET:
        logger.warning('Neither SUPABASE_URL nor SUPABASE_JWT_SECRET configured — treating as guest evaluation')
        return 'guest'

    try:
        payload = _verify_token(creds.credentials)
        user_id = payload.get('sub')
        return user_id or 'guest'
    except Exception as exc:
        logger.warning(f'Token verification failed ({exc}) — treating as guest evaluation.')
        return 'guest'