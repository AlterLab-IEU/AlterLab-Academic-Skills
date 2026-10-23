"""Auth service request handlers (fictional lab data portal).

The web client talks only to this service for sign-in; this service is the only one that reads
or writes the `users` and `refresh_tokens` tables in PostgreSQL.
"""
from datetime import timedelta

from .db import db                       # thin psycopg wrapper: fetch_one / execute
from .tokens import hash_token, new_refresh_token, sign_access_jwt, verify_password

ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=14)
MAX_FAILED_LOGINS = 5
LOCKOUT = timedelta(minutes=15)


def create_session(req):
    """POST /api/v2/session  body: {email, password}"""
    user = db.fetch_one(
        "SELECT id, pw_hash, failed_logins, locked_until FROM users WHERE email = %s",
        (req.json["email"],))
    if user is None:
        return 401, {"error": "invalid_credentials"}
    if user.locked_until and user.locked_until > db.now():
        return 423, {"error": "account_locked"}
    if not verify_password(req.json["password"], user.pw_hash):
        db.execute(
            "UPDATE users SET failed_logins = failed_logins + 1, "
            "locked_until = CASE WHEN failed_logins + 1 >= %s THEN now() + %s END WHERE id = %s",
            (MAX_FAILED_LOGINS, LOCKOUT, user.id))
        return 401, {"error": "invalid_credentials"}

    db.execute("UPDATE users SET failed_logins = 0, locked_until = NULL WHERE id = %s", (user.id,))
    refresh = new_refresh_token()
    db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, now() + %s)",
        (user.id, hash_token(refresh), REFRESH_TTL))
    return 201, {"access_token": sign_access_jwt(user.id, ACCESS_TTL)}, {"Set-Cookie": f"rt={refresh}; HttpOnly; Secure"}


def refresh_session(req):
    """POST /api/v2/session/refresh  (refresh token in the rt cookie)"""
    old = req.cookies.get("rt")
    row = db.fetch_one(
        "SELECT user_id, revoked FROM refresh_tokens WHERE token_hash = %s AND expires_at > now()",
        (hash_token(old),))
    if row is None or row.revoked:
        return 401, {"error": "invalid_refresh_token"}

    # rotate: revoke the presented token and issue a new one
    db.execute("UPDATE refresh_tokens SET revoked = true WHERE token_hash = %s", (hash_token(old),))
    new = new_refresh_token()
    db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, now() + %s)",
        (row.user_id, hash_token(new), REFRESH_TTL))
    return 200, {"access_token": sign_access_jwt(row.user_id, ACCESS_TTL)}, {"Set-Cookie": f"rt={new}; HttpOnly; Secure"}


def delete_session(req):
    """DELETE /api/v2/session  (sign out)"""
    db.execute("UPDATE refresh_tokens SET revoked = true WHERE token_hash = %s",
               (hash_token(req.cookies.get("rt")),))
    return 204, None, {"Set-Cookie": "rt=; Max-Age=0"}
