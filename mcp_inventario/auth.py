import hmac

from mcp.server.auth.provider import AccessToken


class StaticTokenVerifier:
    def __init__(self, token):
        self._token = token.encode()

    async def verify_token(self, token):
        if hmac.compare_digest(token.encode(), self._token):
            return AccessToken(token=token, client_id="gestor-inventario", scopes=[])
        return None
