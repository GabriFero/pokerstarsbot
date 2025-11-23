import uuid
import os
import requests

LOGIN_URL = "https://areaprivata.pokerstars.it/api/authentication-ms/v1/login"

def pokerstars_login(username: str, password: str, pvd: str = "BO9999"):
    # Genera sessionId UUID
    session_id = str(uuid.uuid4())

    # User-Agent simile a quello del browser
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )

    payload = {
        "username": username,
        "password": password,
        "pvd": pvd,
        "flagConto": 0,
        "sessionId": session_id,
        # come richiesto lo mandiamo vuoto
        "recaptchaToken": "",
        "userAgent": user_agent,
    }

    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://areaprivata.pokerstars.it",
        "Referer": (
            "https://areaprivata.pokerstars.it/loginJwt"
            "?endcallbackurl=https%3A%2F%2Fwww.pokerstars.it%2F"
            "&cancelcallbackurl=https%3A%2F%2Fwww.pokerstars.it%2F"
            "&intcmp=home%7Cheader%7Caccedi"
        ),
        "User-Agent": user_agent,
        # header custom (session/call/channel); sessionId lo riutilizziamo
        "x-session-id": session_id,
        "x-call-id": str(uuid.uuid4()),
        "x-channel-id": "62",
        "x-channel-info": user_agent,
    }

    # NB: qui NON stiamo mandando i cookie del browser;
    # se il backend li richiede, questa chiamata fallirà.
    resp = requests.post(LOGIN_URL, json=payload, headers=headers)

    print("Status:", resp.status_code)
    try:
        print("Response JSON:", resp.json())
        return resp.json()
    except ValueError:
        print("Response text:", resp.text)
        return resp.text


if __name__ == "__main__":
    # Meglio usare variabili d'ambiente invece di hardcodare
    username = "IlPazzoide"
    password = "Tango.gay15"

    result = pokerstars_login(username, password)
