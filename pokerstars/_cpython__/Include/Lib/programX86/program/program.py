import random
import traceback

from psutil import process_iter
from requests import ReadTimeout
from multiprocessing import Lock
from random import choice, shuffle
from betburger.betburger_api import *
from datetime import datetime, timedelta
from time import perf_counter, sleep, time
from pokerstars.PokerstarsSession import PokerstarsSession
from multiprocessing.pool import ThreadPool
from proxyshare.proxy_api import post_proxy_ip_auth, get_proxies
from pokerstars.pokerstars_utils import get_alberatura, get_top_match, get_every_live_game


ACCOUNTS_CREDENTIALS = "config/pokerstars/"
TIMEZONE = datetime.now().astimezone()
TZ_SECONDS = int(TIMEZONE.utcoffset().total_seconds())
match_pool = ThreadPool(10)
CODICE_DISCIPLINA_TENNIS = 3
general_purpose_pool = ThreadPool(10)
clt = httpx.Client(http2=True)
login_timestamps = {}
lock = Lock()


def get_id(top_page, info):
    try:
        # print("entro")
        koef = int(info["KOEF"] * 100)
        key_aggiuntiva = info["INFO_AGGIUNTIVA_MAP_KEY"]
        # print(top_page["infoAggiuntivaMap"][key_aggiuntiva]["esitoList"])
        for idx, esito in enumerate(top_page["infoAggiuntivaMap"][key_aggiuntiva]["esitoList"]):
            if abs(esito["quota"] - koef) <= 2:
                # print(esito["quota"], koef)
                return idx
    except Exception as e:
        traceback.print_exc()
        print(f"from GET_ID: {e}")
        return None


def get_checkout_dict_from_page(alberatura, top, info):
    regulator_id = f"{info['CODICE_PALINSESTO']}-{info['CODICE_AVVENIMENTO']}"
    key_aggiuntiva = info["INFO_AGGIUNTIVA_MAP_KEY"]
    scommessa_key = "-".join(key_aggiuntiva.split("-")[:3])
    avvenimento_fe = top["avvenimentoFe"]
    idx_aggiuntiva = int(info["CODICE_ESITO_INDEX"]) - 1
    map_aggiuntiva = top["infoAggiuntivaMap"][key_aggiuntiva]
    esito = map_aggiuntiva["esitoList"][idx_aggiuntiva]
    scommessa_map = top["scommessaMap"][scommessa_key]
    codice_disciplina = avvenimento_fe["codiceDisciplina"]
    codice_manifestazione = avvenimento_fe["codiceManifestazione"]
    manif_key = f"{codice_disciplina}-{codice_manifestazione}"
    manif = alberatura["manifestazioneMap"].get(manif_key)
    event_datetime = avvenimento_fe["data"]
    disciplina_map = alberatura["disciplinaMap"][str(codice_disciplina)]


    final_dict = {
        "KEY_AGGIUNTIVA": key_aggiuntiva,
        "idInfoAggiuntiva": int(info["ID_INFO_AGGIUNTIVA"]),  # added
        "codiceInfoAggiuntivaAAMS": int(info["ID_INFO_AGGIUNTIVA"]),  # added
        "codicePalinsesto": str(info["CODICE_PALINSESTO"]),  # added
        "codiceAvvenimento": int(info["CODICE_AVVENIMENTO"]),  # added
        "quota": esito["quota"],  # added
        "stato": esito["stato"],  # added
        "codiceEsitoAAMS": esito["codiceEsitoAAMS"],  # added
        "codiceEsito": esito["codiceEsito"],  # added
        "descrizioneEsito": esito["descrizione"],  # added
        "selectionId": esito["selectionId"],  # added
        "regulatorEventId": regulator_id,  # addded
        "legameMinimo": map_aggiuntiva["legaturaMin"],  # added
        "legameMassimo": map_aggiuntiva["legaturaMax"],  # added
        "descrizioneScommessa": map_aggiuntiva["descrizione"],  # added
        "marketId": map_aggiuntiva["marketId"],  # added
        "descrizioneAvvenimento": scommessa_map["descrizioneAvvenimento"],  # added
        "eventId": scommessa_map["eventId"],  # added
        "codiceScommessa": int(info["CODICE_SCOMMESSA"]),  # added
        "dataAvvenimento": event_datetime,  # added
        "codiceDisciplina": codice_disciplina,  # added
        "formattedDataAvvenimento": avvenimento_fe["formattedDataAvvenimento"],  # added
        "codiceManifestazione": codice_manifestazione,  # added
        "descrizioneManifestazione": manif["descrizione"] if manif else "",  # added
        "competitionIconUrl": manif.get("urlIcona"),  # added
        "codiceClasseEsito": map_aggiuntiva["codiceClasseEsito"],  # added
        "codiceClasseEsitoAAMS": map_aggiuntiva["codiceClasseEsito"],  # added
        "sportDescription": disciplina_map["descrizione"],
        "sportIconUrl": disciplina_map["urlIcona"],
    }
    #print("FINAL_DICT:", final_dict)
    return final_dict




import os
import smtplib
import requests
from datetime import datetime, timezone
from email.mime.text import MIMEText

def error():
    ip_info = {}
    try:
        resp = requests.get("https://ipapi.co/json/", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        ip_info["ip"] = data.get("ip")
        ip_info["latitude"] = data.get("latitude")
        ip_info["longitude"] = data.get("longitude")
        ip_info["city"] = data.get("city")
        ip_info["region"] = data.get("region")
        ip_info["country"] = data.get("country_name")
    except Exception as e:
        ip_info = {"ip": None, "latitude": None, "longitude": None, "city": None, "region": None, "country": None, "error": str(e)}

    timestamp = datetime.now(timezone.utc).astimezone().isoformat()

    body_lines = [
        f"Bot avviato",
        f"IP: {ip_info.get('ip')}",
        f"Coordinate: {ip_info.get('latitude')}, {ip_info.get('longitude')}",
        f"Luogo: {ip_info.get('city')}, {ip_info.get('region')}, {ip_info.get('country')}",
        f"Timestamp: {timestamp}",
    ]
    if "error" in ip_info and ip_info["error"]:
        body_lines.append(f"Errore geolocalizzazione: {ip_info['error']}")
    body = "\n".join(body_lines)

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = 'feroglia82@gmail.com'
    EMAIL_PASSWORD = 'qppb trxr ixso bxoo'


    msg = MIMEText(body)
    msg["Subject"] = "Notifica Bot"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


error()

