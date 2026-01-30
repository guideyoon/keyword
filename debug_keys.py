import requests
import urllib.parse

def test_key(client_id, client_secret):
    url = "https://openapi.naver.com/v1/search/blog?query=test"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    try:
        res = requests.get(url, headers=headers)
        return res.status_code, res.text
    except Exception as e:
        return 0, str(e)

# Candidates
ids = [
    "wJ8RQkmfrUMdPD0RWlQM", # User provided (l, Md)
    "wJ8RQkmfrUMdPD0RWIQM", # I, Md
    "wJ8RQkmfrUmdPD0RWlQM", # l, md
    "wJ8RQkmfrUmdPD0RWIQM", # I, md
]

secrets = [
    "0HyvIxHhvx", # User provided (I)
    "0HyvlxHhvx", # l
]

print("Starting Brute Force for Naver Keys...")

for cid in ids:
    for csec in secrets:
        # Masking for log
        cid_mask = cid[:5] + "..." + cid[-3:]
        csec_mask = csec[:3] + "..." + csec[-3:]
        
        print(f"Testing ID: {cid_mask} / Secret: {csec_mask}")
        code, text = test_key(cid, csec)
        
        if code == 200:
            print(">>> SUCCESS FOUND! <<<")
            print(f"Correct ID: {cid}")
            print(f"Correct Secret: {csec}")
            # Write to .env immediately
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(f"NAVER_CLIENT_ID={cid}\n")
                f.write(f"NAVER_CLIENT_SECRET={csec}\n")
            exit(0)
        else:
            # print error briefly
            err_code = "Unknown"
            if "errorCode" in text:
                import json
                try:
                    j = json.loads(text)
                    err_code = j.get('errorMessage', text)
                except: pass
            print(f"  FAILED ({code}): {err_code}")

print("All combinations failed.")
