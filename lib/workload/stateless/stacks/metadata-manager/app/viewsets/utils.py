import jwt


def get_email_from_jwt(request) -> str | None:
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    token = auth_header
    if auth_header.lower().startswith('bearer '):
        token = auth_header.split()[1]

    decoded_token = jwt.decode(token, options={"verify_signature": False})
    return decoded_token.get('email')
