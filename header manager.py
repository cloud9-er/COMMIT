import urllib.request 
import urllib.error 
class Header_manager:
    def __init__(self,headers=None):
        self.headers=headers or {
            "User-Agent": "MyScraperBot/1.0",
            "Accept": "text/html,application/xhtml+xml",
        }
        self.opener=self.build_opener()
    def add_headers(self,key,value):
        """this is used to update a global header into a specialized header"""
        self.headers[key]=value
    def merge_headers(self,request_headers=None):
        self.request_headers=request_headers or {}
        return{ **self.headers, **self.request_headers}
    def build_request(self,url,headers=None,method=None):
        merge=self.merge_headers(headers)
        return urllib.request.Request(url,headers=merge,method=method)
    def build_opener(self):
        manager_header=self.headers
        class AddHeadersHandler(urllib.request.BaseHandler):
            def http_request(self, req):
                for key, val in manager_header.items():
                    if not req.has_header(key):
                        req.add_header(key, val)
                return req
            https_request = http_request
        return urllib.request.build_opener(AddHeadersHandler())

    def open(self, url_or_request):
        """Convenience: route a call through this manager's own opener,
        scoped to this instance only — no global state touched."""
        return self.opener.open(url_or_request)
if __name__=="__main__":
    manager=Header_manager()
#This is the test to see if it is working as expected
#Test 1 here we are going to use the global header case 
req=manager.build_request('https://www.bbc.com')
print("Global_headers", dict(req.headers.items()))
#this is test two to check if the specialized header is of higher priority than the global header 
req2 = manager.build_request(
    "https://www.bbc.com",
    headers={"Accept": "application/json"},
)
headers2 = dict(req2.header_items())
print("With override:", headers2)
#TEST THREE TO KNOW IF THE ADD_HEADER METHOD IS WORKING
manager.add_headers("Authorization","Bearer secret token",)
req3=manager.build_request("https://www.bbc.com")
header3=req3.header_items()
print(header3)



