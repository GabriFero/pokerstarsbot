import sys
import time
import requests
from dotenv import dotenv_values
from whatismyip import amionline

PROXY_PATH = "config/proxy.env"
PROXY_CONFIG = dotenv_values(PROXY_PATH)
proxyscrape_session = requests.Session()
proxyscrape_headers = {
    "Authorization": f"Token {PROXY_CONFIG['API_KEY']}"
}
proxyscrape_session.headers.update(proxyscrape_headers)
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
            if use_proxies:
                authorized_ips, max_ids = get_authorized_ip_IDs()
                if not authorized_ips or last_ip not in authorized_ips:
                    if len(authorized_ips) == max_ids:
                        del_listed_ip(authorized_ips[0])
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
    proxy_response = requests.get(
        f"https://api.proxyscrape.com/v2/account/datacenter_shared/proxy-list?auth={PROXY_CONFIG['API_KEY']}"
        f"&type=getproxies&country[]=it&protocol=http&format=normal&status=all",
    ).text.removesuffix("\r\n").split("\r\n")
    return proxy_response


def get_authorized_ip_IDs():
    params = {
        "auth": PROXY_CONFIG["API_KEY"],
        "type": "get",
    }
    ip_list_response = requests.get("https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist",
                                    params=params).json()

    return [ip for ip in ip_list_response["whitelisted"]], ip_list_response["maxips"]


def del_listed_ip(ip: str):
    response = requests.get(
        f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={PROXY_CONFIG['API_KEY']}"
        f"&type=remove&ip[]={ip}",
    )


def authorize_ip(ip: str):
    response = requests.get(
        f"https://api.proxyscrape.com/v2/account/datacenter_shared/whitelist?auth={PROXY_CONFIG['API_KEY']}"
        f"&type=add&ip[]={ip}",
    )


def get_current_ip():
    ip = requests.get(" https://api.ipify.org/").text

    return ip
