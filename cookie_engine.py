import http.cookiejar
from email.message import Message
import urllib.request
import json



class ResponseAdapter():
    """
    """

    def __init__(self, message):
        self.message = message

    def info(self):
        return self.message





class CookieEngine():
    """
    """
    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()

    def headers_to_message(self, headers):

        message = Message()

        for name, value in headers.items():
            if isinstance(value,(list, tuple)):
                for val in value:
                    message.add_header(name, val)
            else:
                message.add_header(name, value)

        return message
 

    #To extract Set_Cookie header from http response message and store them in CookieJar
    def extract_from_response(self, response, url):

        """getting headers from response message"""
        headers = response.headers

        """converting headers to message using headers_to_message"""
        message = self.headers_to_message(headers)

        """passing message through response adapter for the extract method of CookieJar
        response_adapter serves as the response from server"""
        response_adapter = ResponseAdapter(message)

        """creating request object containing url as expected by CookieJar"""
        request = urllib.request.Request(url)

        """CookieJar extraction"""
        self.cookie_jar.extract_cookies(response_adapter, request)


    def get_cookie_header(self, url):

        """creating a request object for identifying the proper url"""
        request = urllib.request.Request(url)


        """"""
        self.cookie_jar.add_cookie_header(request)

        """"""
        cookie_header = request.get_header("Cookie")

        """"""
        return cookie_header


    def save_cookie_as_json(self, filename):

        cookies = []

        for cookie in self.cookie_jar:

            cookie_info = {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "expires": cookie.expires
            }

            cookies.append(cookie_info)

        """json"""
        data = {
            "version": 1,
            "cookies": cookies
        }

        """converts pyhton dict to json"""
        with open(filename, "w", encoding = "utf-8") as file:
            json.dump(data, file, indent = 4)


    def load_json_for_cookie_request(self, filename):

        """converts cookies.json to python dict"""
        with open(filename, "r", encoding = "utf-8") as file:
            data = json.load(file)


        """getting back cookies list of dict"""
        cookies = data["cookies"]

        for cookie_info in cookies:

            cookie = http.cookiejar.Cookie(
                version = 0,
                name = cookie_info["name"],
                value = cookie_info["value"],
                port = None,
                port_specified = False,
                domain = cookie_info["domain"],
                domain_specified = True,
                domain_initial_dot = cookie_info["domain"].startswith("."),
                path = cookie_info["path"],
                path_specified = True,
                secure = cookie_info["secure"],
                expires = cookie_info["expires"],
                discard = False,
                comment = None,
                rest = {},
                rfc2109 = False
            )

            self.cookie_jar.set_cookie(cookie)
                



