
import requests
import xml.etree.ElementTree as ET

def get_google_trends():
    url = "https://trends.google.com/trends/hottrends/atom/feed?pn=p23"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            # Iterate items
            trends = []
            for item in root.findall('.//item'):
                title = item.find('title').text
                # approx_traffic = item.find('{https://trends.google.co.kr/trends/trendingsearches/daily}ht:approx_traffic') 
                # Namespace handling might be tricky properly, usually just string search or ignore ns for simple check
                
                # Using simple split/find if namespace is issue, but ET usually handles it if we look carefully.
                # Let's just grab title for now to verify.
                trends.append(title)
                
            return trends[:10]
        else:
            return [f"Error: {response.status_code}"]
    except Exception as e:
        return [f"Exception: {e}"]

if __name__ == "__main__":
    print(get_google_trends())
