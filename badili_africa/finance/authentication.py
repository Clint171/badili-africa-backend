from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class BearerTokenAuthentication(TokenAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth = super().authenticate(request)
        if auth is None:
            return None

        user, token = auth
        if not user.is_active:
            raise AuthenticationFailed("User inactive or deleted.")

        return user, token
