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
            resp = requests.post(self.base_url, json=payload, timeout=10, headers={"Accept":"application/json"})
            raw_text = resp.text
            try:
                body = resp.json()
            except ValueError:
                body = {}

            if resp.status_code == 200:
                token = body.get("access") or body.get("access_token")
                roles = body.get("roles", [])
                primary_role = body.get("primary_role")
                return LoginResult(True, username=username, token=token, roles=roles, primary_role=primary_role)

            # explicit handling
            if resp.status_code == 401:
                return LoginResult(False, error=body.get("detail") or "Invalid username or password.")
            if resp.status_code == 400:
                if isinstance(body, dict) and any(isinstance(v, list) for v in body.values()):
                    msg = "; ".join(f"{k}: {', '.join(map(str, v))}" for k, v in body.items() if isinstance(v, list))
                else:
                    msg = body.get("detail") or body.get("message") or "Invalid request."
                return LoginResult(False, error=msg)
            if resp.status_code == 429:
                return LoginResult(False, error="Too many attempts. Try again later.")
            if 500 <= resp.status_code <= 599:
                detail = body.get("detail") or ""
                return LoginResult(False, error=f"Server error ({resp.status_code}). {detail}".strip())

            msg = body.get("message") or body.get("detail") or f"HTTP {resp.status_code}"
            return LoginResult(False, error=msg)

        except requests.Timeout:
            return LoginResult(False, error="Request timed out. Check your connection.")
        except requests.ConnectionError:
            return LoginResult(False, error="Cannot reach backend. Check server status.")
        except requests.RequestException as e:
            return LoginResult(False, error=f"Network error: {e}")


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

