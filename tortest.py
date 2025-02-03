import requests as r

TOR_PROXY ={

    "http:":"socks5h://127.0.0.1:9050","https":"socks5h://127.0.0.1:9050"

}

def tor():
    
    try:
        response=r.get("http://check.torproject.org",proxies=TOR_PROXY)

        if "Congratulations" in response.text:
            print("connected successfully")
        else:
            print("Failed")
    except Exception as e:
        print(f"error:{e}")
tor()