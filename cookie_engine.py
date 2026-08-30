import http.cookiejar                   #A std lib, stores and manages cookies, handles cookies matching rule
from email.message import Message       # Provides a header container that is compactible with CookieJar extraction method
import urllib.request                   # Provides Request object used by CookieJar for cookie extration and generation
import json                             # Provides JSON serialization and deserialization for persistent cookie storage.



class ResponseAdapter():
    """ Converts the header into an response object-like structure for Cookiejar extract to access"""

    def __init__(self, message):
        self.message = message

    def info(self):
        return self.message





class CookieEngine():
    """ Manages cookie extraction, storage, generation, and persistence."""

    def __init__(self):

        """creating the CookieJar that stores all cookies managed by the session."""
        self.cookie_jar = http.cookiejar.CookieJar()

    def headers_to_message(self, headers):
        """Solve compactibility problem, changes the dict headers by creating a Message object to hold the HTTP response headers."""

        message = Message()

        for name, value in headers.items():             # Iterate through every header name and value from the HTTP response.
            if isinstance(value,(list, tuple)):
                for val in value:
                    message.add_header(name, val)
            else:
                message.add_header(name, value)

        return message                                  #used by ResponseAdapter
 

    
    def extract_from_response(self, response, url):
        """To extract Set_Cookie header from http response message and store them in CookieJar"""


        """getting headers from response message"""
        headers = response.headers

        """converting headers to message using headers_to_message"""
        message = self.headers_to_message(headers)

        """passing message through response adapter for the extract method of CookieJar.
        Response_Adapter serves as the response from server"""
        response_adapter = ResponseAdapter(message)

        """creating request object containing url as expected by CookieJar extract method"""
        request = urllib.request.Request(url)

        """CookieJar extraction of cookies from response headers and stored in cookie_jar"""
        self.cookie_jar.extract_cookies(response_adapter, request)


    def get_cookie_header(self, url):
        """Outgoing cookie site, provide cookies for Request header"""

        """creating a request object so CookieJar can identify which cookie apply to the url"""
        request = urllib.request.Request(url)


        """Ask CookieJar to select applicable cookies and add them to the request."""
        self.cookie_jar.add_cookie_header(request)

        """Retrieve the generated Cookie header from the Request object."""
        cookie_header = request.get_header("Cookie")

        """Return cookie header to be used in the HTTP Request pipeline"""
        return cookie_header


    def save_cookie_as_json(self, filename):
        """Allows for persistent storage of cookies in json"""

        """Create a list to hold cookies for json serialization"""
        cookies = []

        """Iterate through all cookies currently stored in CookieJar, creates a dict, appends into the cookies list"""
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

        """Create the json structure and include a format version for future compatibility"""
        data = {
            "version": 1,
            "cookies": cookies
        }

        """converts python dict to json and write it to a file"""
        with open(filename, "w", encoding = "utf-8") as file:
            json.dump(data, file, indent = 4)


    def load_json_for_cookie_request(self, filename):
        """loads json file ----> python dict  -----> cookie object -----> cookie_jar"""


        """opens the saved json file for reading, converts cookies.json to python dict"""
        with open(filename, "r", encoding = "utf-8") as file:
            data = json.load(file)


        """retrieving cookies (list of dict)"""
        cookies = data["cookies"]


        """Reconstruct each Cookie object from its saved dictionary representation."""
        for cookie_info in cookies:

            # extra parameters are needed as default in HTTP Request header
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

            """Add the reconstructed cookie to CookieJar so it can be used for future requests."""
            self.cookie_jar.set_cookie(cookie)
                



