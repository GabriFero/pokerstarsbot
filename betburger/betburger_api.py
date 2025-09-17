import os
import traceback

import httpx
from time import sleep, time
from imaplib import IMAP4_SSL
from datetime import datetime
from traceback import print_exc
from os import getcwd, mkdir, path
import xml.etree.ElementTree as et
from json import loads, load, dumps, dump
from email import message_from_bytes
from dotenv import dotenv_values, unset_key, set_key

header = {
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
}
err_counter = 30
DOMAIN = "https://www.pokerstars.it/"
SETTINGS_PATH = f"{os.getcwd()}\\config\\betburger\\settings.json"
POKERSTARS_BOOKMAKER_ID = 103
SERVER = "imap.gmail.com"
mail = IMAP4_SSL(SERVER)
mail_config = dotenv_values("config/gmail.env")
mail.login(mail_config["EMAIL"], mail_config["PASSWORD"])
client = httpx.Client(http2=True)
client.headers.update(header)
SOCCER_ID = 7
TABLE_TENNIS_ID = 13

# def extract_settings():
#     if not path.exists(SETTINGS_PATH):
#         mkdir(SETTINGS_PATH)


def _retrieve_single_filter(args):
    f = None
    try:
        f = open("betburger\\received_dtos.txt", "a")  # this can get heavy, check for file size
        api_key = args[0]
        filter_id: str = args[1]
        url = args[2]
        left, right = args[3][0], args[3][1]
        invalid_choices = args[4] if args[4] else None

        # print(f"IL FILTRO {filter_id} HA LIMITI {left, right}")
        data = {
            "per_page": "5",
            "search_filter[]": [filter_id],
            "access_token": api_key
        }
        api_response = None
        attempts = 3
        while not api_response and attempts > 0:
            try:
                api_response = client.post(url, data=data, timeout=15)
                #print(api_response.text)
                if api_response.status_code == 429:
                    return 429, filter_id
            except Exception as e:
                print(e)
                print(f"retrieve_single_filter errore durante il tentativo n.{attempts}.")
                sleep(0.5)
                attempts -= 1
        if not attempts:
            return None, filter_id

        if api_response.status_code == 200:

            content = loads(api_response.text)
            # print(f"{filter_id}, {api_response.status_code}, {len(content['bets'])}")
            # if len(content["bets"]) > 0:
            # print("RICEZIONE DA BETBURGER:", perf_counter())
            scelte = []
            bts = len(content["bets"])
            if bts >= 20:
                return "block"
            if bts > 0:
                f.write(datetime.fromtimestamp(time()).strftime("%m/%d/%Y, %H:%M:%S"))
                f.write(dumps(content, indent=3))
                f.write("\n\n")
            count = 0
            for dto in content["bets"]:
                # print(f"TEMPO TRASCORSO DALLA DETECTION DI BETBURGER:", time() - dto["updated_at"])
                if not left <= dto["koef"] <= right or dto["bookmaker_id"] != POKERSTARS_BOOKMAKER_ID:
                    count = count + 1 if not left <= dto["koef"] <= right else count
                    continue
                ahead = True
                if invalid_choices:
                    for invalid in invalid_choices:
                        if invalid["sport"] == dto["sport_id"] \
                                and (invalid["variation"] == dto["market_and_bet_type"] or not invalid["variation"]) \
                                and (invalid["period"] == dto["period_id"] or not invalid["period"]) \
                                and (invalid["value"] == dto["market_and_bet_type_param"] or not invalid["value"]):
                            ahead = False
                            break
                if not ahead:
                    continue
                scelte.append(dto)

            if count > 0:
                print(f"SCARTATE {count} SCOMMESSE A CAUSA DEL BUG DI BETBURGER")
            #print(scelte)
            return scelte, filter_id

    except Exception:
        print_exc()
        return None, args[1]
    finally:
        if f:
            f.close()


def get_bets(filter_pool):
    result = {}
    at_least_one_enabled = False
    try:
        with open(SETTINGS_PATH, "r") as json_file:
            config = load(json_file)
            # filters = [filt["id"] for filt in config["filters"]]
        for api in config["api"]:
            enabled = api["enabled"]
            at_least_one_enabled |= enabled
            if not enabled:
                continue
            else:
                params = [(api["key"],
                           filt["id"],
                           config["url"],
                           (filt.get("left", 0.0), filt.get("right", 10000.0)),
                           api.get("invalid")) for filt in api["filters"]]
                # print("PARAMS DA BETBURGER:", params)

                for pool_res in filter_pool.map_async(_retrieve_single_filter, params).get():
                    try:
                        if pool_res[0] is None:
                            print(f"ERRORE DA PARTE DI BETBURGER SU FILTRO {pool_res[1]} GESTITO CON SUCCESSO.")
                        elif pool_res[0] == 429:
                            print("LIMITE DI BETBURGER DI 30 RICHIESTE OGNI MEZZO MINUTO RAGGIUNTO.")
                            continue
                        elif isinstance(pool_res[0], list) and len(pool_res[0]) > 0:
                            print(f"TROVATE {len(pool_res[0])} BETS PER FILTRO {pool_res[1]}")
                            result[pool_res[1]] = pool_res[0]
                            #print(result)
                        elif isinstance(pool_res[0], str) and pool_res[0] == "block":
                            api["enabled"] = False
                            print("UN NUMERO TROPPO ALTO DI SCOMMESSE DETECTATE DA BETBURGER È SPESSO ASSOCIATO"
                                  "AD UN CAMBIO DI API KEY. API DISATTIVATA.")
                            with open(SETTINGS_PATH, "w", encoding="utf-8") as json_file:
                                dump(config, json_file, indent=3)

                    except Exception as e:
                        #print("get_bets:", e)
                        continue
    except Exception:
        print_exc()
    finally:
        if not at_least_one_enabled:
            print("LA COMUNICAZIONE CON BETBURGER È SOSPESA DAI SETTINGS. RECHECK TRA 60 SECONDI.")
            sleep(60)
        return result


def check_email_for_new_key():
    status, messages = mail.select("KEY")
    if status != "OK":
        exit("Incorrect mail box")
    status, data = mail.search(None, "(UNSEEN)")
    data_idx = str(data[0]).split("'")[1].split(" ")
    allowed = mail_config.get("ALLOWED")
    key = None

    for i in data_idx:
        if i == data_idx[-1]:
            res, data = mail.fetch(str(i), '(RFC822)')
            for response in data:
                if isinstance(response, tuple):
                    message = message_from_bytes(response[1])
                    mail_from = message["from"].split()[-1].lstrip("<").rstrip(">")
                    if (not allowed) or (mail_from in allowed):
                        if message.is_multipart():
                            for part in message.walk():
                                try:
                                    mail_content = part.get_payload(decode=True).decode()
                                    key = ''.join(et.fromstring(mail_content).itertext())
                                    print(f"NUOVA BETBURGER API KEY: {key}")
                                except Exception:
                                    pass
                    elif mail_from not in allowed:
                        print(f"RICEVUTA MAIL POTENZIALMENTE MALEVOLA DA {mail_from}.")

        mail.store(i, '+FLAGS', '\\Deleted')

    if key:
        unset_key("config/betburger/keys.env", "KEY")
        set_key("config/betburger/keys.env", "KEY", key)


def extract_info_from_dtos(bet_dtos: list, filter_id: int):
    global err_counter
    bet_info = {}

    for i in range(len(bet_dtos)):
        key = bet_dtos[i]["id"]
        bet_info[key] = {}
        try:
            if not bet_dtos[i]["direct_link"]:
                raise Exception
            book_dir_link = bet_dtos[i]["bookmaker_event_direct_link"]
            bet_info[key]["BET_URL"] = f"{DOMAIN}/scommesse-live{book_dir_link}"
            split_dirlink = bet_dtos[i]["direct_link"].split("|")
            # infoAggiuntivaMap[2-3-4-1][0] to extract content about that specific bet
            bet_info[key]["CODICE_ESITO_INDEX"] = split_dirlink[0]
            bet_info[key]["ID_INFO_AGGIUNTIVA"] = split_dirlink[1]
            bet_info[key]["CODICE_PALINSESTO"] = split_dirlink[2]
            bet_info[key]["CODICE_AVVENIMENTO"] = split_dirlink[3]
            bet_info[key]["CODICE_SCOMMESSA"] = split_dirlink[4]
            bet_info[key]["CODICE_CLASSE_ESITO"] = split_dirlink[5]
            bet_info[key]["INFO_AGGIUNTIVA_MAP_KEY"] = \
                f"{split_dirlink[2]}-{split_dirlink[3]}-{split_dirlink[4]}-{split_dirlink[1]}"
            bet_info[key]["KOEF"] = bet_dtos[i]["koef"]

        except Exception:
            # traceback.print_exc()
            if not err_counter:
                try:
                    check_email_for_new_key()
                except Exception:
                    print_exc()
                print(f"ERRORE DI BETBURGER SU FILTRO {filter_id} ASSOCIATO ALLA SCADENZA DELLA CHIAVE API, "
                      f"FARE DI NUOVO IL LOGIN E SALVARE LA NUOVA CHIAVE SU FILE. "
                      f"SE L'ERRORE PERSISTE, CONTATTARE IL SUPPORTO.")
                err_counter = 15
            err_counter -= 1
    return bet_info
