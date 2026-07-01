import base64

import jwt


class TwitchAuthError(Exception):
    pass


def verify_extension_jwt(token: str, secret_b64: str, dev_mode: bool = False) -> dict:
    """
    Verify a Twitch Extension Helper JWT (HS256, base64-encoded secret from
    the developer console). Returns the decoded claims, which include
    opaque_user_id (always present) and user_id (only if the viewer has
    shared identity with the extension).
    """
    if dev_mode:
        return {"user_id": "dev-user", "opaque_user_id": "dev-user", "role": "broadcaster"}

    if not secret_b64:
        raise TwitchAuthError("server misconfigured: TWITCH_EXTENSION_SECRET is not set")

    try:
        secret = base64.b64decode(secret_b64)
        claims = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise TwitchAuthError(f"invalid token: {e}") from e

    return claims
