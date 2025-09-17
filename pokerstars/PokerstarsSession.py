import os
import random
import ssl
import traceback

import httpx
import smtplib
import pyautogui
from pprint import pprint
from copy import deepcopy
from time import time, sleep
from json import loads, dumps
from traceback import print_exc
from dotenv import dotenv_values
from multiprocessing import Lock
import undetected_chromedriver as uc
from email.mime.text import MIMEText
from pokerstars.request_jsons.bet import *
from datetime import datetime, timedelta
from time import time, sleep, perf_counter
from random import uniform, randint, choice
from selenium.webdriver.common.by import By
from email.mime.multipart import MIMEMultipart
from pokerstars.pokerstars_constants import CHROME_VERSION
from email.mime.application import MIMEApplication

from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchWindowException, WebDriverException
from traceback import print_exc


latestchromedriver = ChromeDriverManager().install()

MAIN_PAGE = "https://www.pokerstars.it/"
LOGIN_PAGE = "https://areaprivata.pokerstars.it/loginJwt"
USER_AGENT = (f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              f"Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36")
DATETIME_FRMT = "%m/%d/%Y, %H:%M:%S"
SCOMMESSE_LIVE_PAGE = "https://www.pokerstars.it/scommesse-live"
FORMATS = ["tennis", "calcio", "basket", "top"]
pyautogui.FAILSAFE = False
KNOWN_ERRORS = {-1020889, -10142, -10143, -10325, -10043, -10446, -1020101,
                -1020102, -1071, -103001, -1006, -1020053, -1020013, -5, -1050202}


def suppress_exception_in_del(uc):
    old_del = uc.Chrome.__del__

    def new_del(self) -> None:
        try:
            old_del(self)
        except Exception:
            pass

    setattr(uc.Chrome, '__del__', new_del)


suppress_exception_in_del(uc)


class PokerstarsSession:
    def __init__(self, settings: dict, proxy: str, event_bets=None, play_bets=None, bet_timestamps=None):
        if bet_timestamps is None:
            bet_timestamps = []
        self.driver = None
        if play_bets is None:
            play_bets = {}
        if event_bets is None:
            event_bets = {}
        self.req_proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}",
        } if proxy else None
        self.oth_proxies = {
            "http://": f"http://{proxy}",
            "https://": f"http://{proxy}",
        } if proxy else None
        self.settings = settings
        self.username = self.settings["username"]
        self.proxy = proxy
        self.jwt_token = self.settings.get("jwt_token")
        self.token = self.settings.get("token")
        self.account_id = self.settings.get("account_id")
        if log_exp := self.settings.get("login_expiration"):
            self.login_expiration = log_exp
        else:
            self.login_expiration = time()
        self.bet_timestamps = bet_timestamps
        self.cookies = None
        self.event_bets = event_bets
        self.play_bets = play_bets
        self.balance = None
        self.success = False
        self.stake = settings["stake"]
        self.quantiles = settings["quantiles"]
        self.dynamic_bet = self.validate_dynamic_stakes()
        self.rand_activity_timer = time() + (5 * 60)
        self.bet_pyld = deepcopy(bet_payload)
        self.pokerstars_header = {
            'authority': 'betting.pokerstars.it',
            'accept': '*/*',
            'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'connection': 'keep-alive',
            'content-type': 'application/json',
            'origin': 'https://www.pokerstars.it',
            'referer': 'https://www.pokerstars.it/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': USER_AGENT,
            'sec-ch-ua': f'"Google Chrome";v="{CHROME_VERSION}", "Not;A=Brand";v="24", "Chromium";v="{CHROME_VERSION}"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        self.pokerstars_session = httpx.Client(http2=True, proxies=self.oth_proxies)
        self.login()

    def init_driver_and_go_main_page(self, headless=False):
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")
        # options.add_argument("--incognito")
        options.add_argument("--disable-gpu")
        if self.req_proxies:
            # options.add_argument(f'--proxy-server=socks5://{self.req_proxies["http"].split("//")[1]}')
            options.add_argument(f"--proxy-server={self.req_proxies['http']}")
        # driver.maximize_window()
        preferences = {
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2
        }

        options.add_experimental_option("prefs", preferences)
        options.add_argument(f"--load-extension={os.getcwd()}\\pokerstars\\ublock")
        options.add_argument(f"--load-extension={os.getcwd()}\\pokerstars\\nortc")
        self.driver = uc.Chrome(
            options=options,
            headless=headless,
            use_subprocess=True,
            driver_executable_path=latestchromedriver,
            user_multi_procs=False
        )
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": USER_AGENT})
        self.driver.maximize_window()
        self.driver.get(MAIN_PAGE)
        WebDriverWait(self.driver, 100).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete')

    def login(self):
        try:
            if self.expired_jwt:
                self.init_driver_and_go_main_page()
                access_button = self.driver.find_element(By.LINK_TEXT, value="Accedi")
                sleep(0.7 + uniform(0, 1))
                ActionChains(self.driver).click(access_button).perform()
                WebDriverWait(self.driver, 100).until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete')
                sleep(1 + uniform(0, 1))
                usr_field = self.driver.find_element(by=By.NAME, value="usernameEtc")
                pass_field = self.driver.find_element(by=By.NAME, value="password")
                auth_button = self.driver.find_element(By.XPATH, "//button[normalize-space()='Accedi']")

                pyautogui.moveTo(randint(130, 250), randint(600, 1000), uniform(0, 1))
                pyautogui.moveTo(randint(530, 650), randint(600, 1000), uniform(0, 1))

                sleep(0.5)
                ActionChains(self.driver).click(usr_field).perform()
                usr_field.send_keys(self.username)
                sleep(1.5 + uniform(0, 1))
                ActionChains(self.driver).move_to_element_with_offset(pass_field, randint(1, 10),
                                                                      randint(0, 4)).perform()
                ActionChains(self.driver).click(pass_field).perform()
                pass_field.send_keys(self.settings["password"])
                sleep(1.5 + uniform(0, 1))
                ActionChains(self.driver).move_to_element_with_offset(auth_button, randint(1, 10),
                                                                      randint(0, 4)).perform()
                pyautogui.click()
                sleep(10 + uniform(0, 1))
                ActionChains(self.driver).click(auth_button).perform()

                attempts = 2
                while attempts:
                    try:
                        sleep(10)
                        pyautogui.click()
                        sleep(1 + uniform(0, 1))
                        self.jwt_token = self.driver.get_cookie("JWT_ar")["value"]
                        self.get_new_expiration()
                        login_cookie = self.driver.get_cookie("login_ar")["value"]
                        self.parse_login(login_cookie)
                        break
                    except (NoSuchWindowException, WebDriverException) as e:
                        print(f"Errore: {e}. Tentativo di ripetere l'accesso per l'account {self.username}.")
                        print_exc()
                        attempts -= 1
                        self.init_driver_and_go_main_page()
                    except Exception as e:
                        print(f"Errore generico durante il login: {e}.")
                        print_exc()
                        attempts -= 1
                        ActionChains(self.driver).click(auth_button).perform()

                if not attempts:
                    raise Exception("Errore nel recupero della chiave JWT e del login.")

                if self.token and self.jwt_token and self.account_id:
                    self.update_header()
                    WebDriverWait(self.driver, 20).until(
                        lambda driver: driver.execute_script('return document.readyState') == 'complete')
                    for i in range(3):
                        try:
                            sleep(1)
                            self.balance = (
                                self.driver.find_element(by=By.CLASS_NAME, value="js-balance").text.split("€"))[0]
                        except Exception:
                            pass
                    print(f"SUCCESSO. "
                          f"USER: {self.username}, "
                          f"CODICE CONTO: {self.account_id}, "
                          f"PROSSIMO LOGIN: {datetime.fromtimestamp(self.login_expiration).strftime(DATETIME_FRMT)}, ",
                          f"PROXY: {self.proxy}, \n"
                          f"STAKE FISSATO: {self.stake},"
                          f"STAKE DINAMICO: {self.dynamic_bet}, "
                          f"BILANCIO CONTO: {'Non disponibile' if not self.balance else self.balance}€")
                    self.send_email()
                    return
                else:
                    raise Exception("Credenziali o token mancanti.")
            else:
                self.update_header()
                print(f"ACCOUNT RIPRISTINATO CON SUCCESSO. "
                      f"USER: {self.username}, "
                      f"CODICE CONTO: {self.account_id}, "
                      f"PROSSIMO LOGIN: {datetime.fromtimestamp(self.login_expiration).strftime(DATETIME_FRMT)}, ",
                      f"PROXY: {self.proxy}, \n"
                      f"STAKE FISSATO: {self.settings['stake']}, "
                      f"STAKE DINAMICO: {self.dynamic_bet}")
                self.success = True
        except NoSuchWindowException as e:
            print(f"Errore finestra chiusa: {e}")
            self.kill_driver()
            self.init_driver_and_go_main_page()
        except Exception as e:
            print(f"Errore durante il login: {e}")
            print(f"TENTATIVO DI LOGIN FALLITO PER USERNAME: {self.username}")
        finally:
            if self.driver:
                self.kill_driver()

    def update_header(self):
        self.pokerstars_header['user_data'] = dumps({'accountId': str(self.account_id),
                                                'token': str(self.token),
                                                'tokenJWT': str(self.jwt_token),
                                                'locale': "it_IT",
                                                'loggedIn': True,
                                                'channel': 62,
                                                'brandId': 175,
                                                'offerId': 0,
                                                })
        self.pokerstars_session.headers.update(self.pokerstars_header)

    def get_new_expiration(self):

        l, r = 3, 4
        dt = datetime.fromtimestamp(self.driver.get_cookie("JWT_ar")["expiry"])

        dt += timedelta(minutes=randint(l * 60, (r * 60) + 59))
        self.login_expiration = dt.timestamp()

    def random_activity(self):
        if self.success and self.rand_activity_timer < time():
            self.rand_activity_timer = time() + (5 * 60)
            page = choice(FORMATS)
            match page:
                case "top":
                    self.driver.get(SCOMMESSE_LIVE_PAGE)
                case _:
                    self.driver.get(f"{SCOMMESSE_LIVE_PAGE}/sport/{page}")

    def parse_login(self, login_cookie):
        variables = login_cookie.split("%3B")
        separator = "=" if len(variables[0].split("=")) == 2 else "%3D"
        for var_str in variables:
            try:
                key, value = var_str.split(separator)
                if key == "codiceConto":
                    self.account_id = value
                elif key == "token":
                    self.token = value
                elif self.account_id and self.token:
                    self.success = True
                    break
            except Exception as e:
                print(login_cookie)
                raise e

    def calculate_stake(self, odd):
        stake_range = -1
        if not self.dynamic_bet:
            return int(self.stake)
        else:
            if len(self.stake) == 1:
                stake_range = 0
            elif len(self.stake) > 1:
                if odd > self.quantiles[-1]:
                    stake_range = - 1
                elif odd <= self.quantiles[0]:
                    stake_range = 0
                else:
                    for i in range(len(self.quantiles)):
                        if self.quantiles >= odd:
                            stake_range = i - 1
                            break
            return int(self.stake[stake_range]//odd)*100

    def _forge_payload(self, args_dict):
        odd = args_dict["KOEF"]
        stake = self.calculate_stake(round(odd * 100))
        importo_vincita = round(odd * stake)
        leg = "legList"
        # credentials
        self.bet_pyld["credentials"]["token"] = self.token
        self.bet_pyld["credentials"]["accountCode"] = str(self.account_id)

        # sportBetSlip
        self.bet_pyld["sportBetSlip"]["stakeAmount"] = stake
        self.bet_pyld["sportBetSlip"]["payoutAmount"] = importo_vincita

        # legList[0]
        # self.bet_pyld["dataScadenza"] = args_dict["dataScadenza"]
        # self.bet_pyld[sport_k]["importoVendita"] = int(self.settings["stake"])
        self.bet_pyld["sportBetSlip"][leg][0]["competitionDescription"] = args_dict["descrizioneManifestazione"]
        self.bet_pyld["sportBetSlip"][leg][0]["competitionIconUrl"] = args_dict["competitionIconUrl"]
        self.bet_pyld["sportBetSlip"][leg][0]["competitionId"] = str(args_dict["codiceManifestazione"])

        self.bet_pyld["sportBetSlip"][leg][0]["eventDescription"] = args_dict["descrizioneAvvenimento"]
        self.bet_pyld["sportBetSlip"][leg][0]["eventId"] = args_dict["eventId"]
        self.bet_pyld["sportBetSlip"][leg][0]["eventTimestamp"] = args_dict["dataAvvenimento"]
        self.bet_pyld["sportBetSlip"][leg][0]["legMin"] = args_dict["legameMinimo"]
        self.bet_pyld["sportBetSlip"][leg][0]["legMax"] = args_dict["legameMassimo"]
        self.bet_pyld["sportBetSlip"][leg][0]["marketAttributeId"] = args_dict["legameMassimo"]
        self.bet_pyld["sportBetSlip"][leg][0]["marketDescription"] = args_dict["descrizioneScommessa"]
        self.bet_pyld["sportBetSlip"][leg][0]["marketId"] = str(args_dict["marketId"])
        self.bet_pyld["sportBetSlip"][leg][0]["odd"] = round(odd * 100)
        self.bet_pyld["sportBetSlip"][leg][0]["marketTypeId"] = args_dict["codiceClasseEsito"]
        self.bet_pyld["sportBetSlip"][leg][0]["regulatorEventId"] = args_dict["regulatorEventId"]
        self.bet_pyld["sportBetSlip"][leg][0]["selectionDescription"] = args_dict["descrizioneEsito"]
        self.bet_pyld["sportBetSlip"][leg][0]["selectionId"] = args_dict["selectionId"]
        self.bet_pyld["sportBetSlip"][leg][0]["selectionType"] = args_dict["codiceEsito"]
        self.bet_pyld["sportBetSlip"][leg][0]["sportDescription"] = args_dict["sportDescription"]
        self.bet_pyld["sportBetSlip"][leg][0]["sportIconUrl"] = args_dict["sportIconUrl"]
        self.bet_pyld["sportBetSlip"][leg][0]["sportId"] = args_dict["codiceDisciplina"]

    def place_bet(self, args_dict: dict, filter_id: int, lock: Lock):

        if not self.pokerstars_session or self.expired_jwt:
            print(f"{self.username}: SCOMMESSA ANNULLATA PER MANCATO LOGIN. PROCESSO DI LOGIN RIAVVIATO.")
            return False
        try:
            self._forge_payload(args_dict)
            #print(f"PAYLOAD_FORGED: {dumps(self.bet_pyld)}")
            if self.settings["must_bet"]:
                with lock:
                    self.pokerstars_session.headers.update(self.pokerstars_header)
                # print("STO PER SCOMMETTERE:", perf_counter())
                # pprint(self.bet_pyld)
                response = self.pokerstars_session.post(
                    url=bet_url,
                    timeout=15,
                    json=self.bet_pyld
                )
                #print(self.bet_pyld)
                return response
            else:
                print(f"{self.username}: AVREI SCOMMESSO.")
                return True

        except Exception:
            traceback.print_exc()
            print(f"{self.username}: ERRORE GENERICO DURANTE LA FASE DI SCOMMESSA SU FILTRO {filter_id}. "
                  "CONTATTARE IL SUPPORTO CON L'ERRORE SOPRA RIPORTATO.")
            return False

    @property
    def expired_jwt(self):
        return self.login_expiration < time()

    def generate_file(self):
        url = "https://betting.pokerstars.it/api/ticket-info/secure/searchSportTicketList"
        new_header = self.pokerstars_header.copy()
        del new_header["connection"]
        del new_header["content-type"]
        self.pokerstars_session.headers.update(new_header)

        params = {
            'periodo': '99',
            'pageSize': '0',
            'pageNumber': '1',
            'stato': '2',  # 4 chiuse, 2 aperte
            'tipo': '2',
            'channel': '62',
        }

        response = self.pokerstars_session.get(
            url=url,
            params=params)
        cont = loads(response.content)

        n_tickets = cont["result"]["ticketCount"]
        params["pageSize"] = str(n_tickets)

        response = self.pokerstars_session.get(
            url=url,
            params=params)
        cont = loads(response.content)

        aperte = []
        url = "https://betting.pokerstars.it/api/ticket-info/secure/getBetDetails"
        total_at_stake = 0
        for open_bet in cont["result"]["ticketsList"]:
            parametri = {
                "channel": "62",
                "regulatorBetId": str(open_bet["regulatorBetId"]),
                "betId": str(open_bet["betId"])
            }
            response = self.pokerstars_session.get(
                url=url,
                params=parametri)
            content = loads(response.content)
            stringa = (
                f"SPORT: {content['result']['predictions'][0]['sportDescription']}\n"
                f"EVENTO: {content['result']['predictions'][0]['eventDescription']}\n"
                f"GIOCATA: {content['result']['predictions'][0]['marketDescription']}\n"
                f"ORARIO: {content['result']['betTimestamp']}\n"
                f"SCELTA: {content['result']['predictions'][0]['selectionDescription']}\n"
                f"QUOTA: {content['result']['predictions'][0]['selectionPrice']}\n"
                f"STAKE: {content['result']['totalStake']}\n"
                f"POSSIBILE VINCITA: {content['result']['totalReturn']}\n\n"
            )
            aperte.append(stringa)
            total_at_stake += int(content['result']['totalStake'])
        with open(f"reports/{self.username}.txt", "w") as file:
            for op in aperte:
                file.write(op)

        return total_at_stake

    def get_balance(self, for_email=False):
        try:
            if self.driver is None:
                self.init_driver_and_go_main_page(headless=False)

            for cookie in self.cookies:
                self.driver.add_cookie(cookie)

            self.driver.get(MAIN_PAGE)
            WebDriverWait(self.driver, 100).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete')
            self.balance = self.driver.find_element(by=By.CLASS_NAME, value="js-balance").text.split("€")[0]
            self.update_cookies()
        except Exception as e:
            print("DURANTE LA RETRIEVE DEL BALANCE:", e)
            self.balance = "ERRORE"
        finally:

            self.kill_driver()

    def send_email(self):
        if len(self.settings["email"]) > 0:
            try:
                if self.success:
                    total_at_stake = self.generate_file()/100
                    # self.get_balance(for_email=True)
                    email_cred_path = "config/gmail.env"
                    email_config = dotenv_values(email_cred_path)
                    port = 587  # For starttls
                    smtp_server = "smtp.gmail.com"
                    sender_email = email_config["EMAIL"]
                    password = email_config["PASSWORD"]
                    message = MIMEMultipart("mixed")
                    message["Subject"] = f"Report per {self.username}."
                    msg_content = (f"<b>{self.username}</b> ha un saldo di <b>{self.balance}</b> euro sul conto.<br />"
                                   f"Prossimo login alle "
                                   f"{datetime.fromtimestamp(self.login_expiration).strftime(DATETIME_FRMT)}.<br />"
                                   f"In allegato, se disponibili, le scommesse effettuate per un totale di "
                                   f"{total_at_stake} euro (esclusi dal bilancio sopracitato).")
                    body = MIMEText(msg_content, "html")
                    message.attach(body)
                    attachment_path = f"reports/{self.username}.txt"
                    data = datetime.fromtimestamp(time()).strftime("%m/%d/%Y, %H:%M:%S")
                    filename = f"{self.username}_{data}.txt"
                    try:
                        with open(attachment_path, "rb") as attachment:
                            p = MIMEApplication(attachment.read(), _subtype="txt")
                            p.add_header('Content-Disposition',
                                         f"attachment; filename= {filename}")
                            message.attach(p)
                    except Exception as e:
                        print(e)
                    msg_full = message.as_string()
                    context = ssl.create_default_context()
                    with smtplib.SMTP(smtp_server, port) as server:
                        server.ehlo()  # Can be omitted
                        server.starttls(context=context)
                        server.ehlo()  # Can be omitted
                        server.login(sender_email, password)
                        server.sendmail(sender_email, self.settings["email"], msg_full)
                    print("MAIL INVIATA.")
            except Exception as e:
                print(f"{self.username}: RETRIEVE DEL BILANCIO DEL CONTO NON ANDATO A BUON FINE.")
                print(e)

    def update_bet_dicts(self, event_timeout=1, play_timeout=180):
        for key in list(self.event_bets.keys()):
            if self.event_bets[key] + (event_timeout * 60) < time():
                del self.event_bets[key]

        for key in list(self.play_bets.keys()):
            if self.play_bets[key] + (play_timeout * 60) < time():
                del self.play_bets[key]

    def append_bet_to_file(self, bet):
        with open(f"reports/{self.username}.txt", mode="a") as file:
            file.write(bet)

    def update_cookies(self):
        self.cookies = self.driver.get_cookies()
        for cookie in self.cookies:
            if cookie.get("expiry") is not None:
                cookie["expiry"] += (1 * 60 * 60)  # 1hrs is plenty enough

    def kill_driver(self):
        self.driver.quit()
        del self.driver
        self.driver = None

    def check_for_anomalies(self, error_id):
        if error_id not in KNOWN_ERRORS:
            self.bet_timestamps.append(time())
            n = len(self.bet_timestamps)
            if n > 25:
                self.bet_timestamps = self.bet_timestamps[-25:]
                if n >= 20 and (self.bet_timestamps[-1] - self.bet_timestamps[-20] <= 60 * 1):
                    print(f"{self.username}: 20 SCOMMESSE IN MENO DI UN MINUTO. ALLARME.")
                    return True
        elif error_id == -1020889:
            print(f"{self.username}: ACCOUNT BLOCCATO DA PARTE DI POKERSTARS.")
            return True
        elif error_id == -1020013:
            print(f"{self.username}: FONDI INSUFFICIENTI PER SCOMMETTERE.")
            return True
        else:
            return False

    def validate_dynamic_stakes(self):
        if isinstance(self.stake, list):
            if (len_stakes := len(self.stake)) > 0:
                if not self.quantiles and len_stakes == 1:
                    self.quantiles = []
                    return True
                elif isinstance(self.quantiles, list) and len(self.quantiles) == len_stakes + 1:
                    self.quantiles.sort()
                    return True
                else:
                    self.stake = 1000
                    self.quantiles = None
                    print(f"{self.username}: I QUANTILI NON SONO IMPOSTATI CORRETTAMENTE. \n"
                          f"PER UTILIZZARE I QUANTILI, BISOGNA SETTARE 'quantiles' A null O A LISTA VUOTA"
                          f"PER INIZIALIZZARLI AUTOMATICAMENTE, NEL CASO DI UNICO STAKE DINAMICO, "
                          f"ALTRIMENTI IMPOSTARE N+1 BANDE DI QUOTA PER GLI N>1 STAKES DEFINITI DINAMICAMENTE.\n"
                          f"QUANTILI DISATTIVATI E STAKE STATICO IMPOSTATO A 10€.")
                    return False
            else:
                self.stake = [1000]
                print(f" {self.username}: STAKES INIZIALIZZATI A LISTA VUOTA."
                      f"STAKE DINAMICO INIZIALIZZATO AD UN DEFAULT DI 10€.")
                return True
        else:
            return False

    def bet_on_sport(self, sport_description: str):
        return len(self.settings["sport"]) == 0 or sport_description.lower() in self.settings["sport"]

    def should_bet(self, sport_description):
        if not self.settings["sport"]:
            return random.uniform(0, 1) <= self.settings["bet_chance"]["generic"]
        else:
            try:
                return random.uniform(0, 1) <= self.settings["bet_chance"][sport_description.lower()]
            except Exception:
                return random.uniform(0, 1) <= self.settings["bet_chance"]["generic"]
