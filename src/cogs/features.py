import requests
import numpy as np
import orjson as json
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import RequestException

roblox_cookie = {".ROBLOSECURITY": "_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_CAEaAhADIhwKBGR1aWQSFDExMjAxNTEzNTE3MjA0NTQ2MzI4KAM.kZEPVF8s8i50xvOXRbyUk9Do4GbZ33uv03y8TlWTTj5AhF4rguoIq8-e4YKFtrB_Oz2NjPeNWW9XWw4vvoGUHsIy5m8-YDK2xhCoPlS6QKSm7PeEJHJn9nT-RuFajcNJ-z0e4QR8oQvrCT3pIP4YYi70HAjQbVs4JJu1SFF1snTshkC-sYMMhrlFSvd1WYcQBPC2Xr_kPLqvRWnJ9zAZKcomKHTZ6vN0SKzUw9jHOEPn_QDEkxgQ1FyzQ-c_JJLC-Xvxc_A0J4fblflWypePH6EL_E8uTMpA-E3sd1Z26aymA_MbGrBB59GzX9Nd6I320Q5ccAy8cuE5dOpkUViELZm2M2lbTEtCBLVyZS95AdxIzGbxrtwsxQUXvvl3w1pn55xKpWjibyX0OMiwqYE3BHb0o3DMkW2G2te8bHEG9Q-NwB56LSj81NfTy6vtHf7kag_TwOB2qaHrr8EKZnbiQPma71wMk5Z0ImltcFSuUH5yWdcLrYGY5EB-9PzZjzJm51WCn0qGV37v2BfO4dhxjDWad6U8WxIY-dNRPOjVWrPJbI3npbw2ezYcCMGkpsTPES-qIRqIzQmPGM9lCyurYoBsuL7fe2BwseXavJtHhcbEsncPIbJuPuKtT_cZoo5lImhjKA"}

def retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """
    retry session function that retries a request in case of connection errors or status codes
    """
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_page(url):
    try:
        response = retry_session().get(url)
        check = response.json()
        if "data" in check:
            clothings = np.array(check['data'])
        else:
            clothings = np.array([])

        if "nextPageCursor" in check and check['nextPageCursor']:
            return clothings, check['nextPageCursor']
        else:
            return clothings, ""
    except RequestException as e:
        print(f"Error requesting page {url}: {e}")
        return np.array([]), ""

def fclothings(id):
    clothings = 0
    cursor = None


    url = f"https://catalog.roblox.com/v1/search/items/details?Category=3&CreatorTargetId={id}&CreatorType=2&Limit=30"
    clothings_data, cursor = get_page(url)
    clothings += len(clothings_data)


    while cursor:
        urls = [
            f"https://catalog.roblox.com/v1/search/items/details?Category=3&CreatorTargetId={id}&CreatorType=2&Limit=30&cursor={cursor}" for _ in range(10)
        ]
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(get_page, urls))

        for result in results:
            clothings_data, cursor = result
            clothings += len(clothings_data)

    return clothings

def frobux(id):
    global roblox_cookie
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        session = requests.Session()
        session.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            future = executor.submit(session.get, f'https://economy.roblox.com/v1/groups/{id}/currency', cookies=roblox_cookie, timeout=5)
        except RequestException as e:
            print(e)
            return 0
        
        try:
            response = future.result()
            data = json.loads(response.text)
            if "robux" in data:
                robux = data.get("robux", 0)
            else:
                robux = 0
        except RequestException as e:
            print(e)
            return 0
    
    return robux

def fgamevisits(id):
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=retries))

    with ThreadPoolExecutor(max_workers=10) as executor:
        future = executor.submit(session.get, f'https://games.roblox.com/v2/groups/{id}/games?accessFilter=All&sortOrder=Asc&limit=100', timeout=5)

        try:
            response = future.result()
            os = response.json()
            if "data" in os:
                data = os["data"]
            else:
                data = 0

        except requests.exceptions.RequestException as e:
            print(e)
            return 0

    if not data:
        return 0

    visits = np.array([game["placeVisits"] for game in data])
    total_visits = np.sum(visits)
    
    return total_visits
