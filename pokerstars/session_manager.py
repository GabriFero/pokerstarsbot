"""
Sistema di gestione automatica delle sessioni browser con rotazione cookie.
Gestisce due sessioni browser: una attiva e una di backup, con rotazione automatica
dopo 5 richieste o errore 403.
"""

import os
import httpx
import traceback
from time import sleep, time
from copy import deepcopy
from random import uniform, randint
from datetime import datetime
from threading import RLock, Thread
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchWindowException, WebDriverException
from selenium.webdriver.common.keys import Keys
from pokerstars.pokerstars_constants import CHROME_VERSION
from webdriver_manager.chrome import ChromeDriverManager
import pyautogui

latestchromedriver = ChromeDriverManager().install()

MAIN_PAGE = "https://www.pokerstars.it/"
LOGIN_PAGE = "https://areaprivata.pokerstars.it/loginJwt"
USER_AGENT = (f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              f"Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36")
pyautogui.FAILSAFE = False


class BrowserSession:
    """
    Rappresenta una singola sessione browser con i suoi cookie e token.
    """
    
    def __init__(self, username, password, proxy=None, session_id=None):
        self.username = username
        self.password = password
        self.proxy = proxy
        self.session_id = session_id or f"{username}_{int(time())}"
        self.driver = None
        self.cookies = {}
        self.jwt_token = None
        self.token = None
        self.account_id = None
        self.httpx_client = None
        self.request_count = 0
        self.max_requests = 5
        self.is_active = False
        self.is_logged_in = False
        self.creation_time = time()
        self.last_request_time = None
        
    def init_driver(self, headless=False):
        """Inizializza il driver Chrome con le estensioni."""
        # Check if driver is already active
        if self.driver:
            try:
                _ = self.driver.current_window_handle
                return
            except Exception:
                print(f"[{self.session_id}] Driver esistente non risponde, riavvio...")
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-gpu")
        
        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")
        
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
        self.driver.set_page_load_timeout(30)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": USER_AGENT})
        self.driver.maximize_window()
        
    def prepare_login_state(self):
        """
        Prepara lo stato di login: apre il browser, va sulla home, apre il modale
        e pre-compila i campi, ma NON invia il form.
        """
        try:
            print(f"[{self.session_id}] Preparazione stato login (pre-fill)...")
            self.init_driver()
            
            # Navigazione home
            self.driver.get(MAIN_PAGE)
            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            
            # Click pulsante Accedi per aprire modale
            try:
                access_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Accedi"))
                )
                sleep(0.5 + uniform(0, 0.5))
                ActionChains(self.driver).click(access_button).perform()
            except Exception:
                print(f"[{self.session_id}] Pulsante Accedi non trovato o gia aperto")

            WebDriverWait(self.driver, 30).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            
            # Pre-compilazione campi
            try:
                usr_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "usernameEtc"))
                )
                pass_field = self.driver.find_element(by=By.NAME, value="password")
                
                ActionChains(self.driver).click(usr_field).perform()
                usr_field.clear()
                usr_field.send_keys(self.username)
                sleep(0.5)
                
                ActionChains(self.driver).click(pass_field).perform()
                pass_field.clear()
                pass_field.send_keys(self.password)
                
                print(f"[{self.session_id}] Stato login preparato e campi pre-compilati.")
                return True
            except Exception as e:
                print(f"[{self.session_id}] Errore pre-compilazione campi: {e}")
                return False # Se fallisce la pre-compilazione, va bene lo stesso, il driver e comunque aperto
            
        except Exception as e:
            print(f"[{self.session_id}] Errore preparazione stato login: {e}")
            return False

    def perform_login(self):
        """Esegue il login completo. Se il browser e gia aperto e pre-fillato, completa solo il click."""
        try:
            print(f"[{self.session_id}] Esecuzione login...")
            
            # Se il driver non esiste, inizializza tutto da zero
            if not self.driver:
                 self.init_driver()
                 self.driver.get(MAIN_PAGE)
            
            # Controlla se siamo gia pronti per cliccare Accedi (stato pre-fillato)
            auth_button = None
            try:
                # Cerca bottone di submit
                auth_button = self.driver.find_element(By.XPATH, "//button[normalize-space()='Accedi']")
                
                # Verifica se i campi sono compilati
                usr_val = self.driver.find_element(By.NAME, "usernameEtc").get_attribute('value')
                if not usr_val:
                    raise Exception("Campi vuoti")
                
                print(f"[{self.session_id}] Rilevato stato pre-fillato, procedo al click...")
                
            except Exception:
                print(f"[{self.session_id}] Stato pre-fillato non valido/trovato, rieseguo procedura standard...")
                # Procedura standard di riempimento (uguale a prima)
                self.driver.get(MAIN_PAGE)
                WebDriverWait(self.driver, 30).until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )
                try:
                    access_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.LINK_TEXT, "Accedi"))
                    )
                    ActionChains(self.driver).click(access_button).perform()
                except:
                    pass
                
                sleep(1)
                usr_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.NAME, "usernameEtc"))
                )
                pass_field = self.driver.find_element(by=By.NAME, value="password")
                auth_button = self.driver.find_element(By.XPATH, "//button[normalize-space()='Accedi']")
                
                usr_field.clear()
                usr_field.send_keys(self.username)
                sleep(0.5)
                pass_field.clear()
                pass_field.send_keys(self.password)
                sleep(0.5)

            # Click finale su Accedi
            try:
                # Scroll e move per simulare utente
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", auth_button)
                sleep(0.5)
                ActionChains(self.driver).move_to_element(auth_button).click().perform()
            except:
                # Fallback JS click
                self.driver.execute_script("arguments[0].click();", auth_button)
            
            # Attendi e recupera token
            print(f"[{self.session_id}] Attesa token post-login...")
            for _ in range(15): # Polling esteso
                try:
                    jwt = self.driver.get_cookie("JWT_ar")
                    log = self.driver.get_cookie("login_ar")
                    if jwt and log:
                        self.jwt_token = jwt["value"]
                        login_cookie = log["value"]
                        self._parse_login_cookie(login_cookie)
                        self.cookies = self._get_cookies_dict()
                        self.is_logged_in = True
                        print(f"[{self.session_id}] Login completato con successo!")
                        return True
                except Exception:
                    pass
                sleep(1)
            
            print(f"[{self.session_id}] Timeout attesa token")
            return False
            
        except Exception as e:
            print(f"[{self.session_id}] Errore durante il login: {e}")
            traceback.print_exc()
            return False
    def complete_backup_login(self):
        """Completa il login dalla sessione backup (premendo il pulsante Accedi)."""
        try:
            print(f"[{self.session_id}] Completamento login da sessione backup...")
            print(f"[{self.session_id}] URL corrente: {self.driver.current_url}")
            
            # Se il driver non esiste o la finestra e chiusa, re-inizializza il browser e vai al login
            try:
                if not self.driver or not self.driver.window_handles:
                    raise NoSuchWindowException("Driver non inizializzato o finestre chiuse")
                _ = self.driver.current_window_handle  # forza check finestra
            except (NoSuchWindowException, WebDriverException, AttributeError) as e:
                print(f"[{self.session_id}] Driver non disponibile ({e}), riavvio browser per il login di backup...")
                self.init_driver()
                self.driver.get(LOGIN_PAGE)
                WebDriverWait(self.driver, 30).until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )
                sleep(1)

            print(f"[{self.session_id}] Attendo caricamento pagina...")
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            sleep(1)

            # VERIFICA PRESENZA FORM PRIMA DI NAVIGARE
            # Se prepare_credentials_only ha usato il modale sulla home, non dobbiamo ricaricare la pagina
            form_detected = False
            try:
                # Cerca rapidamente i campi
                if self.driver.find_elements(By.NAME, "usernameEtc") and \
                   self.driver.find_elements(By.NAME, "password"):
                    form_detected = True
                    print(f"[{self.session_id}] Form login rilevato nella pagina corrente (modale o pagina dedicata).")
            except Exception:
                pass

            if not form_detected and "login" not in self.driver.current_url.lower():
                print(f"[{self.session_id}] Form non trovato e URL non di login. Vado a {LOGIN_PAGE}")
                self.driver.get(LOGIN_PAGE)
                WebDriverWait(self.driver, 20).until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )
                sleep(1)

            def fill_credentials():
                username_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.NAME, "usernameEtc"))
                )
                password_field = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )

                # Se i campi sono gia compilati (da prepare_credentials_only), non cancellarli se corrispondono
                curr_user = username_field.get_attribute('value')
                if curr_user != self.username:
                    username_field.clear()
                    username_field.send_keys(self.username)

                # La password non la possiamo leggere, la rimettiamo per sicurezza
                password_field.clear()
                password_field.send_keys(self.password)

                return username_field, password_field

            def find_auth_button():
                selectors = [
                    "//button[normalize-space()='Accedi']",
                    "//button[contains(text(), 'Accedi')]",
                    "//button[@type='submit']",
                    "//button[contains(@class, 'submit')]",
                    "//button[contains(@class, 'login')]" 
                ]

                for selector in selectors:
                    try:
                        # Timeout ridotto per velocizzare la ricerca
                        return WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    except Exception:
                        continue
                return None

            def collect_tokens():
                max_retries = 5
                for retry in range(max_retries):
                    jwt_cookie = self.driver.get_cookie("JWT_ar")
                    login_cookie_obj = self.driver.get_cookie("login_ar")

                    if jwt_cookie and login_cookie_obj:
                        self.jwt_token = jwt_cookie["value"]
                        login_cookie = login_cookie_obj["value"]
                        print(f"[{self.session_id}] Token recuperati al tentativo {retry + 1}")
                        self._parse_login_cookie(login_cookie)
                        self.cookies = self._get_cookies_dict()
                        self.is_logged_in = True
                        return True

                    print(f"[{self.session_id}] Token non disponibili ({retry + 1}/{max_retries}), attendo...")
                    sleep(2)

                return False

            username_field, password_field = fill_credentials()
            print(
                f"[{self.session_id}] Campi login pronti "
                f"(username len: {len(username_field.get_attribute('value'))})"
            )

            auth_button = find_auth_button()
            if not auth_button:
                try:
                    screenshot_path = f"debug_{self.session_id}_login_failed.png"
                    self.driver.save_screenshot(screenshot_path)
                    print(f"[{self.session_id}] Screenshot salvato in: {screenshot_path}")
                except Exception:
                    pass
                raise Exception("Pulsante Accedi non trovato o non cliccabile")

            click_success = False
            for attempt in range(3):
                auth_button = find_auth_button()
                if not auth_button:
                    break

                print(f"[{self.session_id}] Tentativo click Accedi {attempt + 1}/3...")

                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", auth_button)
                    sleep(0.5)
                except Exception:
                    pass

                try:
                    ActionChains(self.driver).move_to_element(auth_button).pause(
                        uniform(0.1, 0.3)
                    ).click().perform()
                    click_success = True
                except Exception as e1:
                    print(f"[{self.session_id}] Click standard fallito: {e1}")
                    try:
                        self.driver.execute_script("arguments[0].click();", auth_button)
                        click_success = True
                    except Exception as e2:
                        print(f"[{self.session_id}] Click JavaScript fallito: {e2}")
                        try:
                            password_field = self.driver.find_element(By.NAME, "password")
                            password_field.send_keys(Keys.ENTER)
                            click_success = True
                        except Exception as e3:
                            print(f"[{self.session_id}] Invio ENTER fallito: {e3}")

                if click_success:
                    # Attendi un attimo post-click per vedere se succede qualcosa
                    sleep(2)
                    if collect_tokens():
                        break

                    click_success = False
                    print(f"[{self.session_id}] Nessun token dopo il click, possibile fallimento click.")
                    # Se siamo al terzo tentativo, ricarichiamo la pagina
                    if attempt == 2:
                        print(f"[{self.session_id}] Ultimo tentativo fallito, ricarico pagina...")
                        self.driver.refresh()
                        WebDriverWait(self.driver, 30).until(
                            lambda driver: driver.execute_script('return document.readyState') == 'complete'
                        )
                        sleep(1)
                        username_field, password_field = fill_credentials()
                    else:
                        # Riprova a cercare il bottone e cliccare
                        pass

            if not click_success or not self.is_logged_in:
                try:
                    screenshot_path = f"debug_{self.session_id}_no_tokens.png"
                    self.driver.save_screenshot(screenshot_path)
                    print(f"[{self.session_id}] Screenshot salvato in: {screenshot_path}")
                except Exception:
                    pass
                raise Exception("Login backup non completato: token non recuperati")

            print(f"[{self.session_id}] Login backup completato con successo!")
            print(f"[{self.session_id}] Account ID: {self.account_id}")
            print(f"[{self.session_id}] Totale cookie recuperati: {len(self.cookies)}")

            return True

        except Exception as e:
            print(f"[{self.session_id}] Errore completamento login backup: {e}")
            traceback.print_exc()
            return False

    def _parse_login_cookie(self, login_cookie):
        """Estrae account_id e token dal cookie di login."""
        variables = login_cookie.split("%3B")
        separator = "=" if len(variables[0].split("=")) == 2 else "%3D"

        for var_str in variables:
            try:
                key, value = var_str.split(separator)
                if key == "codiceConto":
                    self.account_id = value
                elif key == "token":
                    self.token = value
            except Exception:
                continue

    def _get_cookies_dict(self):
        """Converte i cookie del browser in un dizionario."""
        cookies_dict = {}
        for cookie in self.driver.get_cookies():
            cookies_dict[cookie['name']] = cookie['value']
        return cookies_dict

    def update_cookies_from_response(self, response):
        """Aggiorna i cookie dalla risposta HTTP."""
        if hasattr(response, 'cookies'):
            for cookie_name, cookie_value in response.cookies.items():
                self.cookies[cookie_name] = cookie_value

    def get_httpx_client(self):
        """Crea o ritorna il client httpx configurato con i cookie attuali."""
        proxies = None
        if self.proxy:
            proxies = {
                "http://": f"http://{self.proxy}",
                "https://": f"http://{self.proxy}",
            }

        if not self.httpx_client:
            self.httpx_client = httpx.Client(http2=True, proxies=proxies)

        self.httpx_client.cookies.clear()
        for name, value in self.cookies.items():
            self.httpx_client.cookies.set(name, value)

        return self.httpx_client

    def increment_request_count(self):
        """Incrementa il contatore delle richieste."""
        self.request_count += 1
        self.last_request_time = time()
        print(f"[{self.session_id}] Richieste effettuate: {self.request_count}/{self.max_requests}")

    def should_rotate(self):
        """Verifica se la sessione deve essere ruotata."""
        return self.request_count >= self.max_requests

    def close(self):
        """Chiude il browser e pulisce le risorse."""
        try:
            if self.driver:
                print(f"[{self.session_id}] Chiusura browser...")
                self.driver.quit()
                del self.driver
                self.driver = None
        except Exception as e:
            print(f"[{self.session_id}] Errore durante chiusura: {e}")

        try:
            if self.httpx_client:
                self.httpx_client.close()
                self.httpx_client = None
        except Exception:
            pass

    def __del__(self):
        """Assicura la chiusura delle risorse."""
        self.close()

class SessionRotationManager:
    """
    Gestisce la rotazione automatica delle sessioni browser.
    Mantiene una sessione attiva e una di backup, ruotando dopo 5 richieste o errore 403.
    """
    
    def __init__(self, username, password, proxy=None, pokerstars_header=None, 
                 skip_initial_login=False, initial_tokens=None, initial_cookies=None):
        self.username = username
        self.password = password
        self.proxy = proxy
        self.pokerstars_header = pokerstars_header or {}
        self.skip_initial_login = skip_initial_login
        self.initial_tokens = initial_tokens or {}
        self.initial_cookies = initial_cookies or {}
        
        self.active_session = None
        self.backup_session = None
        self.lock = RLock()
        
        self.total_rotations = 0
        self.total_requests = 0
        
        # Inizializzazione
        self._initialize_sessions()
    
    def update_header_with_tokens(self, headers):
        """Aggiorna gli header con i token correnti della sessione attiva."""
        import json
        
        updated_headers = headers.copy()
        
        # Se esiste user_data, aggiornalo con i token correnti
        if 'user_data' in updated_headers:
            try:
                user_data = json.loads(updated_headers['user_data'])
                user_data['accountId'] = str(self.active_session.account_id)
                user_data['token'] = str(self.active_session.token)
                user_data['tokenJWT'] = str(self.active_session.jwt_token)
                updated_headers['user_data'] = json.dumps(user_data)
            except Exception as e:
                print(f"[{self.username}] Errore aggiornamento user_data: {e}")
        
        return updated_headers

    def _prepare_backup_async(self, session: BrowserSession):
        """Prepara una nuova sessione di backup in un thread separato."""
        try:
            print(f"[ROTAZIONE] Avvio preparazione asincrona per {session.session_id}...")
            if not session.prepare_login_state():
                print(f"[ROTAZIONE] ATTENZIONE: preparazione backup {session.session_id} fallita")
            else:
                print(f"[ROTAZIONE] Nuova sessione backup pronta (driver caldo): {session.session_id}")
        except Exception as e:
            print(f"[ROTAZIONE] Errore preparazione asincrona backup ({session.session_id}): {e}")
            traceback.print_exc()
    
    def _initialize_sessions(self):
        """Inizializza la sessione attiva e quella di backup."""
        print(f"\n{'='*60}")
        print(f"INIZIALIZZAZIONE SISTEMA DI ROTAZIONE PER: {self.username}")
        print(f"{'='*60}\n")
        
        # Se skip_initial_login è True, usiamo i token già esistenti
        if self.skip_initial_login and self.initial_tokens:
            print(f"[{self.username}] Utilizzo token esistenti, salto login iniziale...")
            
            # Crea sessione "virtuale" che usa solo httpx senza browser
            self.active_session = BrowserSession(
                self.username, self.password, self.proxy, 
                session_id=f"{self.username}_active_1"
            )
            
            # Imposta i token direttamente
            self.active_session.jwt_token = self.initial_tokens.get('jwt_token')
            self.active_session.token = self.initial_tokens.get('token')
            self.active_session.account_id = self.initial_tokens.get('account_id')
            self.active_session.is_logged_in = True
            self.active_session.is_active = True
            
            # Imposta i cookie se disponibili
            if self.initial_cookies:
                self.active_session.cookies = self.initial_cookies.copy()
                print(f"[{self.username}] Cookie importati: {len(self.initial_cookies)} cookie")
            
            # Non serve driver per questa sessione, usa solo httpx
            print(f"[{self.username}] Token impostati: Account ID={self.active_session.account_id}")
        else:
            # Comportamento normale: login completo
            self.active_session = BrowserSession(
                self.username, self.password, self.proxy, 
                session_id=f"{self.username}_active_1"
            )
            
            if not self.active_session.perform_login():
                raise Exception(f"Impossibile effettuare il login per {self.username}")
            
            self.active_session.is_active = True
        
        # Crea sessione di backup (con pre-fill login)
        self.backup_session = BrowserSession(
            self.username, self.password, self.proxy,
            session_id=f"{self.username}_backup_1"
        )
        
        # Avvia driver e pre-compila form per averlo pronto ("caldo e compilato")
        print(f"[{self.username}] Pre-riscaldamento driver backup e form...")
        if self.backup_session.prepare_login_state():
            print(f"[{self.username}] Driver backup pronto e form compilato.")
        else:
            print(f"ATTENZIONE: Fallito pre-fill backup per {self.username}, driver comunque attivo.")
        
        print(f"\n{'='*60}")
        print(f"SISTEMA PRONTO - Sessione attiva: {self.active_session.session_id}")
        print(f"SISTEMA PRONTO - Sessione backup: {self.backup_session.session_id}")
        print(f"{'='*60}\n")
    
    def rotate_sessions(self, reason="Limite richieste raggiunto"):
        """Ruota le sessioni: backup diventa attiva, crea nuovo backup."""
        with self.lock:
            print(f"\n{'!'*60}")
            print(f"ROTAZIONE SESSIONE IN CORSO - Motivo: {reason}")
            print(f"{'!'*60}\n")
            
            self.total_rotations += 1
            
            # Verifica disponibilità backup
            if self.backup_session is None:
                print("[ROTAZIONE] ATTENZIONE: Sessione backup non ancora pronta! Creazione d'emergenza...")
                # Creazione sincrona d'emergenza
                self.backup_session = BrowserSession(
                    self.username, self.password, self.proxy,
                    session_id=f"{self.username}_backup_EMERGENCY_{int(time())}"
                )

            # Chiudi la vecchia sessione attiva
            old_active = self.active_session
            old_active_id = old_active.session_id
            
            print(f"[ROTAZIONE] Step 1: Promozione backup a sessione attiva...")
            # Backup diventa attiva
            self.active_session = self.backup_session
            # IMPORTANTE: Resetta il puntatore al backup per evitare di riusare la sessione appena promossa
            self.backup_session = None
            
            print(f"[ROTAZIONE] Nuova sessione attiva: {self.active_session.session_id}")
            
            # Chiudiamo subito la vecchia sessione per liberare risorse (riduce carico CPU/RAM)
            print(f"[ROTAZIONE] Step 1.1: Chiusura vecchia sessione attiva ({old_active_id})...")
            try:
                old_active.close()
                print(f"[ROTAZIONE] Vecchia sessione attiva chiusa con successo")
            except Exception as e:
                print(f"[ROTAZIONE] Errore durante chiusura vecchia sessione: {e}")
            
            # Esegui il login completo sulla nuova sessione attiva (driver gia aperto e form pre-fillato)
            print(f"[ROTAZIONE] Step 2: Esecuzione login su nuova sessione (Pre-filled)...")
            
            # Qui usiamo perform_login che rileva se il form e' gia compilato
            if not self.active_session.perform_login():
                print(f"[ROTAZIONE] Login fallito, riprovo chiudendo e riaprendo...")
                self.active_session.close()
                if not self.active_session.perform_login():
                    raise Exception(f"CRITICO: Impossibile effettuare login rotazione per {self.username}")
            
            print(f"[ROTAZIONE] Login completato per {self.active_session.session_id}")
            self.active_session.is_active = True
            self.active_session.request_count = 0
            
            # Crea nuovo backup IN BACKGROUND
            # Spostiamo TUTTA la logica di creazione (Step 3 e 4) in un thread separato
            # per permettere al bot di ricominciare subito a scommettere
            print(f"[ROTAZIONE] Avvio thread per creazione prossima sessione di backup...")
            Thread(
                target=self._create_backup_background,
                args=(self.total_rotations + 1,),
                daemon=True
            ).start()
            
            print(f"\n{'!'*60}")
            print(f"ROTAZIONE COMPLETATA (Sessione operativa, backup in preparazione)")
            print(f"Nuova sessione attiva: {self.active_session.session_id}")
            print(f"{'!'*60}\n")

    def _create_backup_background(self, rotation_num):
        """Crea e prepara la sessione di backup in background."""
        try:
            print(f"[BACKGROUND] Step 3: Creazione oggetto sessione backup {rotation_num}...")
            new_backup = BrowserSession(
                self.username, self.password, self.proxy,
                session_id=f"{self.username}_backup_{rotation_num}"
            )
            
            # Assegna subito l'oggetto
            # Nota: se rotate_sessions viene chiamato ORA, troverà questo oggetto.
            # Se il driver non è ancora pronto, perform_login gestirà l'apertura.
            self.backup_session = new_backup
            
            print(f"[BACKGROUND] Step 4: Pre-riscaldamento driver backup...")
            if new_backup.prepare_login_state():
                print(f"[BACKGROUND] Nuova sessione backup pronta: {new_backup.session_id}")
            else:
                print(f"[BACKGROUND] ATTENZIONE: Pre-fill backup fallito per {new_backup.session_id}")
                
        except Exception as e:
            print(f"[BACKGROUND] Errore creazione backup: {e}")
            traceback.print_exc()
    
    def make_request(self, method, url, **kwargs):
        """
        Effettua una richiesta HTTP gestendo automaticamente la rotazione.
        
        Args:
            method: Metodo HTTP (GET, POST, etc.)
            url: URL della richiesta
            **kwargs: Parametri aggiuntivi per la richiesta
        
        Returns:
            Response object o None in caso di errore
        """
        with self.lock:
            # Verifica se serve rotazione
            if self.active_session.should_rotate():
                self.rotate_sessions()
            
            # Ottieni il client httpx configurato
            client = self.active_session.get_httpx_client()
            
            # Aggiorna gli header con i token correnti
            headers = kwargs.get('headers', {})
            if self.pokerstars_header:
                headers.update(self.pokerstars_header)
            
            # Usa il metodo dedicato per aggiornare gli header
            headers = self.update_header_with_tokens(headers)
            kwargs['headers'] = headers
            
            try:
                # Effettua la richiesta
                self.total_requests += 1
                response = client.request(method, url, **kwargs)
                
                # Aggiorna i cookie dalla risposta
                self.active_session.update_cookies_from_response(response)
                
                # Incrementa contatore richieste
                self.active_session.increment_request_count()
                
                # Verifica se c'è errore 403 (rotazione immediata)
                if response.status_code == 403:
                    print(f"\n⚠️  ERRORE 403 RILEVATO - Rotazione immediata necessaria ⚠️\n")
                    self.rotate_sessions(reason="Errore 403")
                
                return response
                
            except Exception as e:
                print(f"Errore durante la richiesta: {e}")
                traceback.print_exc()
                
                # In caso di errore, prova a ruotare
                try:
                    self.rotate_sessions(reason=f"Errore: {str(e)}")
                    # Riprova con la nuova sessione
                    client = self.active_session.get_httpx_client()
                    response = client.request(method, url, **kwargs)
                    self.active_session.update_cookies_from_response(response)
                    self.active_session.increment_request_count()
                    return response
                except Exception as retry_error:
                    print(f"Errore anche dopo rotazione: {retry_error}")
                    return None
    
    def get_current_tokens(self):
        """Ritorna i token correnti della sessione attiva."""
        return {
            'jwt_token': self.active_session.jwt_token,
            'token': self.active_session.token,
            'account_id': self.active_session.account_id
        }
    
    def get_stats(self):
        """Ritorna statistiche sulle sessioni."""
        return {
            'total_requests': self.total_requests,
            'total_rotations': self.total_rotations,
            'active_session_requests': self.active_session.request_count,
            'active_session_id': self.active_session.session_id,
            'backup_session_id': self.backup_session.session_id if self.backup_session else None
        }
    
    def cleanup(self):
        """Pulisce tutte le risorse."""
        print(f"\nPulizia risorse per {self.username}...")
        if self.active_session:
            self.active_session.close()
        if self.backup_session:
            self.backup_session.close()
        print(f"Pulizia completata per {self.username}")
    
    def __del__(self):
        """Assicura la pulizia delle risorse."""
        self.cleanup()
