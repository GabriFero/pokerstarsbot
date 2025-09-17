import sys
import time
import requests
from dotenv import dotenv_values
from whatismyip import amionline

PROXY_PATH = "config/proxy.env"
PROXY_CONFIG = dotenv_values(PROXY_PATH)
webshare_session = requests.Session()
webshare_headers = {
    "Authorization": f"Token {PROXY_CONFIG['API_KEY']}"
}
webshare_session.headers.update(webshare_headers)
last_time = time.perf_counter()
minutes_diff = 30
last_ip = None
wait = 30


def post_proxy_ip_auth(use_proxies):
    global last_ip, last_time
    attempts = 4
    while attempts > 0:
        is_online = amionline()
        # 60 * minutes_diff is the total elapsed seconds
        if is_online and ((time.perf_counter() - last_time) > (60 * minutes_diff) or not last_ip):
            last_time = time.perf_counter()
            latest_ip_addr = get_current_ip()
            print(f"CONNESSO ALLA RETE. IP = {latest_ip_addr}")
            last_ip = latest_ip_addr
            accepted_ip_IDs = get_authorized_ip_IDs()
            if accepted_ip_IDs and last_ip not in accepted_ip_IDs:
                authorize_ip(last_ip)
            return
        elif not is_online:
            attempts -= 1
            print(f"IL DEVICE RISULTA OFFLINE, ASSICURARSI DI ESSERE CONNESSI AD INTERNET. "
                  f"{attempts + 1} TENTATIVI RIMASTI. "
                  f"NUOVO TENTATIVO DI RICONNESSIONE ENTRO {wait} SECONDI...")
            time.sleep(wait)
        else:
            return

    sys.exit("IL DEVICE RISULTA OFFLINE ED È STATO RAGGIUNTO IL NUMERO MAX DI TENTATIVI DI RICONNESSIONE. "
             "CHIUSURA BOT IN CORSO.")


def get_proxies():
    proxy_response = webshare_session.get(
        url="https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=25",
        timeout=15,
    ).json()
    proxies = set(f"{proxy['proxy_address']}:{proxy['port']}"
                  for proxy
                  in proxy_response["results"]
                  if proxy["country_code"] == "IT")
    return proxies


def get_authorized_ip_IDs():
    ip_list_response = webshare_session.get(
        url="https://proxy.webshare.io/api/v2/proxy/ipauthorization/",
        timeout=15,
    ).json()

    return [res["id"] for res in ip_list_response["results"]]


def del_listed_ip(ip: str):
    webshare_session.delete(
        url=f"https://proxy.webshare.io/api/v2/proxy/ipauthorization/{ip}/",
        timeout=15,
    )


def get_current_ip():
    curr_ip_response = webshare_session.get(
        url="https://proxy.webshare.io/api/v2/proxy/ipauthorization/whatsmyip/",
        timeout=15,
    ).json()

    return curr_ip_response["ip_address"]


def authorize_ip(ip: str):
    webshare_session.post(
        url="https://proxy.webshare.io/api/v2/proxy/ipauthorization/",
        timeout=15,
        json={"ip_address": ip},
    )
