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
    data_scadenza = calculate_data_scadenza(event_datetime)

    final_dict = {
        "KEY_AGGIUNTIVA": key_aggiuntiva,
        "idInfoAggiuntiva": int(info["ID_INFO_AGGIUNTIVA"]),  # added
        "codiceInfoAggiuntivaAAMS": int(info["ID_INFO_AGGIUNTIVA"]),  # added
        "dataScadenza": data_scadenza,  # added
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


def calculate_data_scadenza(data_avvenimento):
    scadenza_templ = "%Y-%m-%dT%H:%M:%S.%f"
    avvenimento_templ = "%Y-%m-%dT%H:%M:%S.%fZ"  # no timezone
    scadenza_dt = datetime.strptime(data_avvenimento, avvenimento_templ).replace(tzinfo=TIMEZONE.tzinfo)
    scadenza_dt += timedelta(seconds=TZ_SECONDS)
    data_scadenza = datetime.strftime(scadenza_dt, scadenza_templ)[:-3] + datetime.now(TIMEZONE.tzinfo).isoformat()[-6:]
    return data_scadenza


def kill_process(name):
    for proc in process_iter():
        if proc.name() == name:
            pass
            # proc.kill()


def update_accounts_info(sess_dict):
    with open(f"{os.getcwd()}\\config\\pokerstars\\accounts.json", "r", encoding="utf-8") as json_file:
        settings = load(json_file)
    for profile in settings["profiles"]:
        if sess_dict.get(profile["username"]):
            profile["jwt_token"] = sess_dict[profile["username"]].jwt_token
            profile["token"] = sess_dict[profile["username"]].token
            if sess_dict[profile["username"]].proxy is not None:
                profile["proxy"] = sess_dict[profile["username"]].proxy
            profile["account_id"] = sess_dict[profile["username"]].account_id
            profile["login_expiration"] = sess_dict[profile["username"]].login_expiration
    with open(f"{os.getcwd()}\\config\\pokerstars\\accounts.json", "w", encoding="utf-8") as json_file:
        dump(settings, json_file, indent=3)


def profile_handler(session_dict: dict[str: PokerstarsSession], use_proxies):
    proxies: set = None
    if use_proxies:
        proxies = get_proxies()
    with open(f"{os.getcwd()}\\config\\pokerstars\\accounts.json", "r", encoding="utf-8") as json_file:
        settings = load(json_file)
    enabled_accounts = [profile
                        for profile
                        in settings["profiles"]
                        if profile["enabled"]
                        and profile["username"] not in session_dict]
    disabled_accounts = [profile for profile in settings["profiles"] if not profile["enabled"]]
    for profile in disabled_accounts:
        try:
            del session_dict[var := profile["username"]]
            print(f"{var}: PROFILO RIMOSSO DALLA PILA DEGLI ATTIVI.")
        except Exception:
            pass
    if not enabled_accounts and not session_dict:
        print("NESSUN ACCOUNT DA LOGGARE.")
    if enabled_accounts:
        args = []
        print(f"PROCESSO DI LOGIN AVVIATO PER {', '.join([profile['username'] for profile in enabled_accounts])}")
        for i in range(length := len(enabled_accounts)):
            chosen_proxy = enabled_accounts[i].get("proxy")
            if use_proxies and not chosen_proxy:
                chosen_proxy = choice(tuple(proxies))
                if len(proxies) >= length:
                    proxies.remove(chosen_proxy)
            args.append((enabled_accounts[i], chosen_proxy))
        login_handler(args, session_dict, proxies)
        update_accounts_info(session_dict)

    remake_login = any([session_dict[key].expired_jwt for key in session_dict])
    if remake_login:
        print("PROCESSO DI RELOGIN DEI PROFILI INIZIALIZZATO. JWT TOKEN SCADUTI.")
        args = [(session_dict[key].settings, session_dict[key].proxy,
                 session_dict[key].event_bets, session_dict[key].play_bets,
                 session_dict[key].bet_timestamps)
                for key in session_dict if session_dict[key].expired_jwt]
        login_handler(args, session_dict, proxies)
        update_accounts_info(session_dict)


def login_handler(args, session_dict, proxies: set):
    global login_timestamps
    profile_attempts = {}
    for arg in args:
        profile_attempts[arg[0]["username"]] = 0
    while True:
        kill = False
        invalidi = []
        # for res in general_purpose_pool.map_async(_create_sesh, args).get():
        for res in [_create_sesh(arg) for arg in args]:
            if isinstance(res, str):
                profile_attempts[res] += 1
                if profile_attempts[res] < 3:
                    kill = True
                    invalidi.append(res)  # appending the path that failed
                else:
                    deactivate_account(res)
            else:
                login_timestamps.setdefault(res.username, []).append(time())
                le = len(lis := login_timestamps[res.username])
                if le > 2 and (lis[-1] - lis[- 3]) < (30 * 60):
                    deactivate_account(res.username)
                    if session_dict.get(res.username):
                        del session_dict[res.username]
                else:
                    session_dict[res.username] = res
        if kill:
            print("KILLING PROCESS OF CHROME.EXE STARTED.")
            try:
                kill_process("chrome.exe")
            except Exception as e:
                print(e)
            new_args = []

            for i in range(len(args)):
                if args[i][0]["username"] in invalidi:
                    new_arg = list(args[i])
                    if proxies is not None:
                        random_proxy = choice(tuple(proxies))
                        new_arg[1] = random_proxy
                        proxies.remove(random_proxy)
                    new_args.append(tuple(new_arg))
            args = new_args
            print(f"LOGIN FALLITO PER GLI ACCOUNT {', '.join([arg[0]['username'] for arg in args])}.")
        else:
            break


def _create_sesh(args):
    settings = args[0]
    proxy = args[1]
    event_bets = None
    play_bets = None
    bet_timestamps = None
    if len(args) > 2:
        event_bets = args[2]
        play_bets = args[3]
        bet_timestamps = args[4]
    try:
        sesh = PokerstarsSession(settings, proxy, event_bets=event_bets, play_bets=play_bets, bet_timestamps=bet_timestamps)
        if sesh.success:
            return sesh
    except Exception as e:
        print(f"login failed for {settings['username']}. Retrying...")
        print(e)
    return settings['username']


def direct_link_handler(direct_link):
    # Splitting the direct_link into key-value pairs
    key_vals = direct_link.split("&")
    params = {}
    #print("params", key_vals)
    
    # Parsing each key-value pair and storing it in the params dictionary
    for kv in key_vals:
        key, value = kv.split("=")
        params[key] = value
    
    # Extracting the required values from the params dictionary
    event_id = params.get("eventId", "")
    codice_classe_esito = params.get("codiceClasseEsito", "")
    selection_id = params.get("selectionId", "")
    quota = params.get("quota", "")
    codice_esito = params.get("codiceEsito", "")
    codice_avvenimento = params.get("codiceAvvenimento", "")
    codice_scommessa = params.get("codiceScommessa", "")
    id_info_aggiuntiva = params.get("idInfoAggiuntiva", "")
    codice_palinsesto = params.get("codicePalinsesto", "")
    market_id = params.get("marketId", "")
    
    return (event_id, codice_classe_esito,  codice_esito, 
            codice_avvenimento, codice_scommessa, id_info_aggiuntiva, codice_palinsesto)


def _single_kwg_extraction(args):
    bet_dto = args[0]
    profile_names = args[1]
    past_pl = args[2]
    past_ev = args[3]
    alberatura = args[4]
    filter_id = args[5]
    # games_dict = args[6]
    cnt = 0
    bet_info = {}
    try:
        if not bet_dto["direct_link"]:
            print("BETBURGER NON HA INVIATO UN DIRECT-LINK VALIDO PER LA SCOMMESSA.")
            return False
        book_dir_link = bet_dto["bookmaker_event_direct_link"]
        bet_info["BET_URL"] = f"{DOMAIN}/scommesse-live{book_dir_link}"
        (event_id, codice_classe_esito, codice_esito, codice_avvenimento,
         codice_scommessa, id_info_aggiuntiva, codice_palinsesto) = direct_link_handler(bet_dto["direct_link"])
        bet_info["INFO_AGGIUNTIVA_MAP_KEY"] = (f"{codice_palinsesto}-{codice_avvenimento}-"
                                               f"{codice_classe_esito}-{id_info_aggiuntiva}")
        match_key = f"{codice_palinsesto}-{codice_avvenimento}"
        for name in profile_names:
            if f"{bet_info['INFO_AGGIUNTIVA_MAP_KEY']}-{name}" in past_pl:
                cnt += 1
        if cnt == len(profile_names):
            print("TUTTI I PROFILI HANNO SCOMMESSO SU UNA GIOCATA RIPROPOSTA DA BETBURGER.")
            return False
        cnt = 0
        for name in profile_names:
            if f"{match_key}-{name}" in past_ev:
                cnt += 1
        if cnt == len(profile_names):
            print("TUTTI I PROFILI HANNO SCOMMESSO SU UN EVENTO RIPROPOSTO DA BETBURGER.")
            return False
        # infoAggiuntivaMap[2-3-4-1][0] to extract content about that specific bet
        # bet_info["CODICE_ESITO_INDEX"] = splt_link[0]
        bet_info["ID_INFO_AGGIUNTIVA"] = id_info_aggiuntiva
        bet_info["CODICE_PALINSESTO"] = codice_palinsesto
        bet_info["CODICE_AVVENIMENTO"] = codice_avvenimento
        bet_info["CODICE_SCOMMESSA"] = codice_scommessa
        bet_info["CODICE_CLASSE_ESITO"] = codice_classe_esito
        bet_info["CODICE_ESITO_INDEX"] = codice_esito
        bet_info["KOEF"] = bet_dto["koef"]

        try:
            #print("Fetching top match for:", match_key)
            top_resp = get_top_match(match_key, clt)
            top_json = loads(top_resp.text)
            #print("direct_link:", bet_dto["direct_link"])
            #print("parsed_from_direct_link:", event_id, codice_classe_esito, codice_esito,
            #    codice_avvenimento, codice_scommessa, id_info_aggiuntiva, codice_palinsesto)
            #print("CODICE_ESITO_INDEX raw:", repr(bet_info["CODICE_ESITO_INDEX"]))
            kwg = get_checkout_dict_from_page(alberatura, top_json, bet_info)
            if kwg:
                kwg["KOEF"] = bet_info["KOEF"]
                kwg["FILTER"] = filter_id
                #print("KWG è PASSATO:")
                return kwg
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            print("get_top_match error DALLA GET:", e)
            print("ERRORE/TIMEOUT DA PARTE DI pokerstars, "
                  "CONVIENE ATTENDERE PRIMA DELLA PROSSIMA RICHIESTA PER MOTIVI PRECAUZIONALI.")
            return False
    except Exception as e:
        print("SU SINGLE_KWG_EXTRACTION:", e)
        traceback.print_exc()
        return False


def new_multi_match_info(dtos_map, alb, past_pl, past_ev, prof_names, games_dict):
    args = []

    for filter_key in dtos_map:
        args += [(dtos_map[filter_key][i], prof_names, past_pl, past_ev, alb, filter_key, games_dict)
                 for i in range(len(dtos_map[filter_key]))]
    return args


def new_bet_process(kwg_dict: dict, sessions: dict[str: PokerstarsSession], bet_pool):
    #print(f"NUOVA SCOMMESSA RICEVUTA DA BETBURGER: {kwg_dict}")
    #print(f"sessions: {sessions.keys()}")
    success = False
    args = [(profile, kwg_dict, kwg_dict["FILTER"], lock)
            for name, profile in sessions.items()
            if (kwg_dict["FILTER"] in profile.settings["filters"]
                and profile.event_bets.get(kwg_dict["regulatorEventId"]) is None
                and profile.play_bets.get(kwg_dict["KEY_AGGIUNTIVA"]) is None
                and profile.bet_on_sport(kwg_dict["sportDescription"])
                and profile.should_bet(kwg_dict["sportDescription"]))]
    #print(f"ARGS: {args}")
    if args:
        for pool_res in bet_pool.map_async(buy_bet_by_filter, args).get():
            name = pool_res[0]
            result = pool_res[1]
            key_agg = pool_res[2]
    else:
        print("NESSUN PROFILO PER CUI GIOCARE.")
    return success


def deactivate_account(username):
    with open(f"{os.getcwd()}\\config\\pokerstars\\accounts.json", "r", encoding="utf-8") as json_file:
        settings = load(json_file)
    for profile in settings["profiles"]:
        if profile["username"] == username:
            profile["enabled"] = False
            with open(f"{os.getcwd()}\\config\\pokerstars\\accounts.json", "w", encoding="utf-8") as json_file:
                dump(settings, json_file, indent=3)
                print(f"{username}: PROFILO DISATTIVATO")
                return


def buy_bet_by_filter(args):
    pokerstars_profile = args[0]
    kwg = args[1]
    #print(f"{pokerstars_profile.username}: TENTATIVO DI SCOMMETTERE SU FILTRO {args[2]}...")
    filter_id = args[2]
    pool_lock = args[3]
    success = False
    try:
        bet_response = pokerstars_profile.place_bet(kwg, filter_id, pool_lock)
        #print("bet_response:", bet_response.text)
        if bet_response is False:
            raise AttributeError
        elif bet_response is True:
            success = True
            pokerstars_profile.event_bets[kwg["regulatorEventId"]] = time()
            pokerstars_profile.play_bets[f"{kwg['KEY_AGGIUNTIVA']}"] = time()
            raise AttributeError
        content = loads(bet_response.text)
        if 200 <= bet_response.status_code < 300:
            with open(f"{pokerstars_profile.username}_esiti.txt", "a") as file:
                file.write(f"FILTRO: {filter_id}\n"
                           f"STAKE: {pokerstars_profile.settings['stake']}\n"
                           f"QUOTA BETBURGER: {int(kwg['KOEF'] * 100)}\n")
                file.write(dumps(content))
            print("RISPOSTA:")
            #print(dumps(content, indent=3))
            to_be_blocked = pokerstars_profile.check_for_anomalies(code := int(content["code"]))
            if content["code"] == 0:
                success = True
                string_to_print = (f"\nSCOMMESSA PIAZZATA:\n"
                                   f"ACCOUNT: {pokerstars_profile.username}\n"
                                   f"FILTRO: {filter_id}\n"
                                   f"ORA: {datetime.fromtimestamp(time()).strftime('%m/%d/%Y, %H:%M:%S')}\n"
                                   f"STAKE: {pokerstars_profile.settings['stake']}\n"
                                   f"QUOTA BETBURGER: {int(kwg['KOEF'] * 100)}\n"
                                   f"QUOTA pokerstars: {content['sportAccumulatorBetslip']['legList'][0]['odd']} "
                                   f"(CONFERMA SU pokerstars.IT, CONTATTARE SUPPORTO IN CASO DI DISCREPANZE)\n"
                                   f"POTENZIALE VINCITA: {content['sportAccumulatorBetslip']['newPayoutAmount']}\n"
                                   f"AVVENIMENTO: {kwg['descrizioneAvvenimento']}\n"
                                   f"SCOMMESSA: {kwg['descrizioneScommessa']}\n"
                                   f"ESITO: {kwg['descrizioneEsito']}\n"
                                   f"TEMPO DI ELABORAZIONE pokerstars: {bet_response.elapsed}\n")
                print(string_to_print)
                # Generate a random number of seconds between 20 and 30
                random_seconds = random.randint(12, 18)
                #print("Sleeping for", random_seconds, "seconds")

                # Sleep for the randomly generated seconds
                sleep(random_seconds)

                
                print("SLEEPING IS OVER MOTHERFUCKER")
                minutes = 180 if kwg["codiceDisciplina"] == CODICE_DISCIPLINA_TENNIS else 0
                pokerstars_profile.event_bets[kwg["regulatorEventId"]] = time() + minutes * 60
                pokerstars_profile.play_bets[kwg["KEY_AGGIUNTIVA"]] = time()
            elif code == -1050810:
                #to_be_blocked = True
                string_to_print = (f"\nSCOMMESSA IN FASE DI ELABORAZIONE, ERRORE!:\n"
                                   f"ACCOUNT: {pokerstars_profile.username}\n"
                                   f"FILTRO: {filter_id}\n"
                                   f"ORA: {datetime.fromtimestamp(time()).strftime('%m/%d/%Y, %H:%M:%S')}\n"
                                   f"MESSAGGIO: {content['message']}"
                                   f"TEMPO DI ELABORAZIONE pokerstars: {bet_response.elapsed}\n")
                print(string_to_print)
                minutes = 180 if kwg["codiceDisciplina"] == CODICE_DISCIPLINA_TENNIS else 0
                pokerstars_profile.event_bets[kwg["regulatorEventId"]] = time() + minutes * 60
                pokerstars_profile.play_bets[kwg["KEY_AGGIUNTIVA"]] = time()
                print("sleeping")
                sleep(30)
            else:
                to_print = (f"{pokerstars_profile.username}: SCOMMESSA RIFIUTATA SU FILTRO {filter_id}: "
                            f"{code}: {content['message']} ")
                if code == -1020101:
                    to_print += f"({content['info'][1]} -> {content['info'][2]})"
                print(to_print)
            if to_be_blocked:
                deactivate_account(pokerstars_profile.username)

    except Exception as e:
        if not isinstance(e, AttributeError):
            print_exc()
        # print(e)
    # if not success:
    # print(f"SCOMMESSA FALLITA PER {pokerstars_profile.username} SU FILTRO {filter_id}")
    return pokerstars_profile.username, success, kwg["KEY_AGGIUNTIVA"]



def alberatura_and_games(clt):
    alb = get_alberatura(clt)
    games_dict = get_every_live_game(alb, general_purpose_pool, clt)
    return alb, games_dict


def betbot_pipeline():
    global clt

    with open(f"{os.getcwd()}\\utils\\app_settings.json", "r", encoding="utf-8") as json_file:
        app_settings = load(json_file)

    start = perf_counter() - app_settings["secs_diff"]
    minute = perf_counter()
    past_ev = set()
    past_pl = set()
    sessions: dict[str: PokerstarsSession] = {}
    alb_json = None
    already_received = {}
    bet_seconds =  60 * 1  # each bet profile gets to access the betting pool for this amount of seconds (secs * mins)
    last_change_time = perf_counter() - 60
    profile_names = set()
    active = None
    success = True
    while True:
        to_wait = perf_counter() - start
        if to_wait < app_settings["secs_diff"]:
            sleep(app_settings["secs_diff"] - to_wait)
        start = perf_counter()
        if sessions:
            past_pl = set()
            past_ev = set()
            for sesh in sessions:
                sessions[sesh].update_bet_dicts()
                for key in sessions[sesh].event_bets:
                    past_ev.add(f"{key}-{sesh}")
                for key in sessions[sesh].play_bets:
                    past_pl.add(f"{key}-{sesh}")
        if perf_counter() - minute > 60 * 1 or not alb_json:
            with open(f"{os.getcwd()}\\utils\\app_settings.json", "r", encoding="utf-8") as json_file:
                app_settings = load(json_file)
            clt = httpx.Client(http2=True)
            minute = perf_counter()
            print(datetime.fromtimestamp(time()).strftime("%m/%d/%Y, %H:%M:%S"))
        try:
            alb_json = get_alberatura(clt)
            games_dict = None
            # alb_json, games_dict = alberatura_and_games(clt)
        except Exception as e:
            print("get_alberatura error:", e)
            print("ERRORE/TIMEOUT DA PARTE DI pokerstars, ATTENDERE PRIMA DELLA PROSSIMA RICHIESTA, PRECAUZIONALMENTE.")
            clt = httpx.Client(http2=True)
            sleep(3)
            continue
        try:
            post_proxy_ip_auth(use_proxies := app_settings["use_proxies"])
            profile_handler(sessions, use_proxies)
            how_many_out = 0
            if how_many_out >= len(sessions):
                how_many_out = 1
            if sessions:
                profile_names = [names for names in sessions]
                if perf_counter() - last_change_time > bet_seconds and success:
                    shuffle(profile_names)
                    active = set(profile_names[:-how_many_out]) if how_many_out > 0 and len(profile_names) > 1 \
                        else set(profile_names)
                    last_change_time = perf_counter()
            else:
                active = set()
        except Exception as e:
            print("ip and login error error:")
            if isinstance(e, ReadTimeout):
                print(e, type(e))
            else:
                print_exc()
            continue
        start = perf_counter()

        filter_dtos_map = get_bets(general_purpose_pool)
        #print(filter_dtos_map)
        for filt in filter_dtos_map:
            new_list = []
            for dto in filter_dtos_map[filt]:
                (_, codice_classe_esito, codice_esito, codice_avvenimento,
                 _, id_info_aggiuntiva, codice_palinsesto) = direct_link_handler(dto["direct_link"])
                bet_key = (f"{codice_palinsesto}-{codice_avvenimento}-"
                           f"{codice_classe_esito}-{id_info_aggiuntiva}")
                if already_received.setdefault(bet_key, 0) < (n_reps := app_settings["n_reps"]):
                    new_list.append(dto)
                    already_received[bet_key] += 1
                else:
                    print(f"UNA SCOMMESSA È STATA SUGGERITA DA BETBURGER PER {n_reps} VOLTE, "
                          "PER PRECAUZIONE VERRÀ SCARTATA.")
            filter_dtos_map[filt] = new_list

        args = new_multi_match_info(filter_dtos_map, alb_json, past_pl, past_ev, active, games_dict)
        try:
            if args:
                result = match_pool.map_async(_single_kwg_extraction, args)
                for kwg_match in result.get():
                    if not isinstance(kwg_match, bool):
                        new_bet_process(kwg_match, {k: v for k, v in sessions.items() if k in active},
                                        general_purpose_pool)
            else:
                if len(filter_dtos_map) > 0:
                    print(f"NESSUN PROFILO GIOCA QUESTE {len(filter_dtos_map)} SCOMMESSE.")
        except Exception:
            print_exc()


if __name__ == "__main__":
    try:
        betbot_pipeline()
    except Exception as e:
        print_exc()
    finally:
        kill_process("chrome.exe")
