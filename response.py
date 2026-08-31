from dataclasses import dataclass,field
import urllib.request 
import urllib.error
import time 
@dataclass
class Response:
    status:int 
    header: dict 
    body:str 
    reason: str 
    elapse: float 
    cookies:list 

    @classmethod 
    def from_openurllib(cls,url:str,timeout:int=10):
        start=time.perf_counter()
        try:
            with urllib.request.urlopen(url) as response:
                #obtaining headers of the Response
                status=response.status 
                header = dict(response.getheaders())
                reason=response.reason
                #reading data from opened URL
                body= response.read().decode("utf-8")
                elapsed=time.perf_counter()-start 
                cookie_raw=response.headers.get_all("Set-Cookie") or []
                cookies=[cls.cookie_parser(c) for c in cookie_raw] 
                return cls(status=status, 
                        header=header, 
                        body=body,
                        elapse=elapsed,
                        reason=reason,
                        cookies=cookies)
                
        except urllib.error.HTTPError as e:
            cookie_raw=e.headers.get_all("Set-Cookie") or []
            cookies=[cls.cookie_parser(c) for c in cookie_raw]
            return cls(status=e.code,
                    reason=e.reason,
                    header=dict(e.headers.items()),
                    body=e.read().decode("utf-8"),
                    elapse=time.perf_counter()-start,
                    cookies=cookies 
                    )
    @staticmethod 
    def cookie_parser(cookie_str):
        parts=[p.strip() for p in cookie_str.split(";")]
        name,value=parts[0].split('=',1)
        attrs={"name":name,"value":value}
        for part in parts[1:]:
            if '=' in part :
                k,v=part.split('=',1)
                attrs[k.strip().lower()]=v.strip()
            else:
                attrs[k.strip().lower()]=True 
            return attrs
if __name__=="__main__":
    req=Response.from_openurllib("https://httpbin.org/response-headers?Set-Cookie=test%3D123")
    print(req.status) 
    print("this is the header :",req.header,"\n")
    print(req.cookies,list)
    #print(req.body)

