import http.cookiejar
import urllib.request
import json
from email.message import Message


class ResponseAdapter:
    """
    Adapts an HTTP response's headers to the interface expected
    by CookieJar.
    """

    def __init__(self, message):
        self.message = message

    def info(self):
        return self.message


class CookieEngine:
    """
    Owns all cookie state for the HTTP session.

    Responsibilities:
        - store cookies
        - generate Cookie headers
        - extract Set-Cookie headers
        - persist cookies
    """

    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()

    def headers_to_message(self, headers):
        """Convert response headers into an email.message.Message."""
        message = Message()

        for name, value in headers.items():
            if isinstance(value, (list, tuple)):
                for item in value:
                    message.add_header(name, str(item))
            else:
                message.add_header(name, str(value))

        return message

    def extract_from_response(self, response, url):
        """
        Extract cookies from a response and store them in CookieJar.
        """
        message = self.headers_to_message(response.headers)

        response_adapter = ResponseAdapter(message)

        request = urllib.request.Request(url)

        self.cookie_jar.extract_cookies(
            response_adapter,
            request
        )

    def get_cookie_header(self, url):
        """
        Generate the Cookie header applicable to the supplied URL.
        """
        request = urllib.request.Request(url)

        self.cookie_jar.add_cookie_header(request)

        return request.get_header("Cookie")

    def save_cookie_as_json(self, filename):
        """Persist the current cookie jar as JSON."""
        cookies = []

        for cookie in self.cookie_jar:
            cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "expires": cookie.expires,
            })

        data = {
            "version": 1,
            "cookies": cookies,
        }

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def load_json_for_cookie_request(self, filename):
        """Load cookies previously persisted as JSON."""
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        for cookie_info in data["cookies"]:
            cookie = http.cookiejar.Cookie(
                version=0,
                name=cookie_info["name"],
                value=cookie_info["value"],
                port=None,
                port_specified=False,
                domain=cookie_info["domain"],
                domain_specified=True,
                domain_initial_dot=cookie_info["domain"].startswith("."),
                path=cookie_info["path"],
                path_specified=True,
                secure=cookie_info["secure"],
                expires=cookie_info["expires"],
                discard=False,
                comment=None,
                rest={},
                rfc2109=False,
            )

            self.cookie_jar.set_cookie(cookie)