from pokerstars.pokerstars_constants import CHROME_VERSION

alberatura_header = {
    'Accept': '*/*',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Origin': 'https://www.pokerstars.it',
    'Referer': 'https://www.pokerstars.it/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  f"Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36",
    'sec-ch-ua': f'"Google Chrome";v="{CHROME_VERSION}", "Not;A=Brand";v="24", "Chromium";v="{CHROME_VERSION}"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

alberatura_url = "https://betting.pokerstars.it/api/lettura-palinsesto-sport/palinsesto/live/alberatura"