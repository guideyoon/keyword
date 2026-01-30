
import requests
from bs4 import BeautifulSoup

def test_kin_scrape():
    # Example Kin Link (from previous output or random)
    # https://kin.naver.com/qna/detail.naver?d1id=7&dirId=70305&docId=490422915
    url = "https://kin.naver.com/qna/detail.naver?d1id=7&dirId=70305&docId=490422915"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Method 2: Look for anything that looks like a date
        # often "date" class
        dates = soup.select(".date")
        for d in dates:
            print("Date class:", d.get_text())
            
        # Method 3: meta
        # <span class="c-userinfo__info">2024.12.04.</span>
        infos = soup.select(".c-userinfo__info")
        for info in infos:
            print("UserInfo:", info.get_text())
            
        print("HTML snippet:", soup.prettify()[:500])
        
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_kin_scrape()
