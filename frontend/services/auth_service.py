# Auth service for login, stll needs modification or even refactorization, error on self.base_url
import requests

class AuthService:
    def __init__(self):
        # should point to core-urls, then core-urls to api-urls.py, then api-urls.py to user_api.py then handle login logic
        # self.base_url = 'http://localhost:8000/api/users/login/api/'
        self.base_url = "http://127.0.0.1:8000/api/users/login/api/"

    def login(self, username, password):
        """Authenticate user by sending a POST request to the Django backend."""
        payload = {"identifier": username, "password": password}
        try:
            resp = requests.post(self.base_url, json=payload, timeout=10)
        
            try:
                body = resp.json()
            except ValueError:
                body = {}

            if resp.status_code == 200:
                token = body.get("access_token")
                roles = body.get("roles", [])
                primary_role = body.get("primary_role")
                return LoginResult(True, username=username, token=token, roles=roles, primary_role=primary_role)

            msg = body.get("message") or body.get("detail")
            if not msg and "errors" in body:
                msg = body["errors"]
            if not msg:
                msg = f"HTTP {resp.status_code}"
            return LoginResult(False, error=msg)

        except requests.RequestException as e:
            return LoginResult(False, error=f"Cannot reach backend: {e}")

    # def login(self, username, password):
    #     """Authenticate user by sending a POST request to the Django backend."""
    #     data = {'username': username, 'password': password}
    #     try:
    #         resp = requests.post(self.base_url, json={'username': username, 'password': password}, timeout=10)
    #         if resp.status_code == 200:
    #             # details are returned like this
    #             # return Response({
    #             #     'message': 'Login successful',
    #             #     'access_token': str(refresh.access_token),
    #             #     'roles': roles,
    #             #     'primary_role': primary_role,
    #             #     'username': user.username,
    #             # }, status=status.HTTP_200_OK)
    #             token = resp.json().get("access_token")
    #             roles= resp.json().get("roles")
    #             primary_role=resp.json().get("primary_role")
    #             return LoginResult(True, username=username, token=token, roles=roles, primary_role=primary_role)
    #         else:
    #             msg = resp.json().get("message", f"HTTP {resp.status_code}")
    #             return LoginResult(False, error=msg)
    #     except requests.RequestException as e:
    #         return LoginResult(False, error=f"Cannot reach backend: {e}")


class LoginResult:
    def __init__(self, ok, username=None, token=None, roles=None, primary_role=None, error=None):
        self.ok = ok
        self.username = username
        self.token = token
        self.roles = roles or []
        self.primary_role = primary_role
        self.error = error

