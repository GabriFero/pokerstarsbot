# PokerStars Betting Bot

Sistema automatizzato per scommesse sportive su PokerStars con gestione intelligente delle sessioni e rotazione automatica.

## 🚀 Novità: Sistema di Rotazione Automatica delle Sessioni

**Implementato il 22 Novembre 2025** ✅

Il bot ora include un sistema avanzato di gestione automatica delle sessioni browser che:

- ✅ Mantiene **2 sessioni browser simultanee** (attiva + backup)
- ✅ **Rotazione automatica** dopo 5 richieste HTTP
- ✅ **Recovery immediato** su errore 403
- ✅ **Cookie aggiornati dinamicamente** dopo ogni richiesta
- ✅ **Chiusura automatica** browser non utilizzati (gestione RAM)
- ✅ **Zero downtime** durante la rotazione

### Quick Start (5 minuti)

```bash
# 1. Configura account
notepad config\pokerstars\accounts.json

# 2. Aggiungi "use_session_rotation": true
# 3. Esegui test
python tmp_rovodev_test_session_rotation.py

# 4. Se OK, avvia bot
python app.py
```

📖 **Documentazione Completa**: Vedi [`QUICK_START.md`](QUICK_START.md)

---

## 📋 Caratteristiche Principali

### Core Features
- 🎰 Betting automatico su eventi live PokerStars
- 🔄 Integrazione con Betburger API per odds comparison
- 🌐 Supporto proxy (WebShare, ProxyShare)
- 📧 Report automatici via email
- 🎯 Filtri personalizzabili per sport e quote
- 💰 Stake dinamico basato su quantili di quota

### Sistema di Rotazione Sessioni (NUOVO!)
- 🔐 Gestione automatica cookie e token JWT
- 🔄 Rotazione sessioni ogni 5 richieste
- 🛡️ Protezione anti-ban con rotazione preventiva
- 🚀 Backup session sempre pronta per zero downtime
- 📊 Monitoring in tempo reale con statistiche

---

## 📁 Struttura Progetto

```
.
├── app.py                          # Entry point principale
├── pokerstars/
│   ├── PokerstarsSession.py        # Gestione sessioni account
│   ├── session_manager.py          # Sistema rotazione (NUOVO!)
│   ├── pokerstars_utils.py         # Utility API calls
│   ├── pokerstars_constants.py     # Costanti configurazione
│   └── request_jsons/              # Payload richieste
├── betburger/
│   └── betburger_api.py            # API client Betburger
├── webshare/
│   └── webshare_api.py             # API client WebShare
├── proxyshare/
│   └── proxy_api.py                # API client ProxyShare
├── config/
│   ├── pokerstars/
│   │   └── accounts.json           # Configurazione account
│   ├── proxy.env                   # Credenziali proxy
│   └── gmail.env                   # Credenziali email
├── utils/
│   └── app_settings.json           # Impostazioni applicazione
└── reports/                        # Log e report scommesse
```

---

## 🔧 Installazione

### Requisiti
- Python 3.8+
- Chrome Browser (aggiornato)
- Windows OS (consigliato)

### Setup

```bash
# 1. Clona repository
git clone <repository-url>
cd <project-directory>

# 2. Crea virtual environment
python -m venv .venv

# 3. Attiva virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 4. Installa dipendenze
pip install -r requirements.txt

# 5. Configura accounts
copy config\pokerstars\accounts.example.json config\pokerstars\accounts.json
notepad config\pokerstars\accounts.json
```

---

## ⚙️ Configurazione

### Account PokerStars (`config/pokerstars/accounts.json`)

```json
{
   "profiles": [
      {
         "username": "tuoUsername",
         "password": "tuaPassword",
         "stake": 100,
         "quantiles": [],
         "filters": ["790399"],
         "email": ["tua.email@example.com"],
         "sport": ["calcio", "tennis"],
         "bet_chance": {
            "generic": 1.0,
            "calcio": 0.8,
            "tennis": 0.6
         },
         "enabled": true,
         "must_bet": true,
         "use_session_rotation": true
      }
   ]
}
```

### Parametri Principali

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `username` | string | Username PokerStars |
| `password` | string | Password account |
| `stake` | int/array | Importo scommessa (fisso o dinamico) |
| `filters` | array | ID filtri Betburger |
| `enabled` | bool | Abilita/disabilita profilo |
| `must_bet` | bool | `true` = scommetti, `false` = test |
| `use_session_rotation` | bool | **NUOVO!** Abilita rotazione sessioni |

### Proxy (`config/proxy.env`)

```env
WEBSHARE_API_KEY=your_api_key
PROXYSHARE_API_KEY=your_api_key
```

### Email (`config/gmail.env`)

```env
EMAIL=your_email@gmail.com
PASSWORD=your_app_password
```

---

## 🎮 Utilizzo

### Avvio Normale

```bash
python app.py
```

### Test Sistema Rotazione

```bash
python tmp_rovodev_test_session_rotation.py
```

### Test Senza Scommettere

Imposta in `accounts.json`:
```json
{
   "must_bet": false
}
```

---

## 📊 Sistema di Rotazione Sessioni

### Come Funziona

```
Avvio → Sessione Attiva (login) + Sessione Backup (credenziali)
         ↓
    Richiesta 1 → Aggiorna cookie
    Richiesta 2 → Aggiorna cookie  
    Richiesta 3 → Aggiorna cookie
    Richiesta 4 → Aggiorna cookie
    Richiesta 5 → Aggiorna cookie
         ↓
    [ROTAZIONE AUTOMATICA]
         ↓
    Backup → Attiva (login rapido)
    Crea nuovo Backup
    Chiude vecchia Attiva
         ↓
    Ricomincia ciclo...
```

### Vantaggi

- 🛡️ **Prevenzione Ban**: Rotazione preventiva prima di limiti server
- 🔄 **Cookie Freschi**: Sempre aggiornati dopo ogni richiesta
- ⚡ **Zero Downtime**: Backup pronto per switch istantaneo
- 💾 **RAM Gestita**: Vecchie sessioni chiuse automaticamente
- 🚨 **Auto-Recovery**: Gestione automatica errori 403

### Configurazione

```json
{
   "use_session_rotation": true   // Abilita (consigliato)
}
```

oppure

```json
{
   "use_session_rotation": false  // Disabilita (sistema tradizionale)
}
```

---

## 📖 Documentazione

### Guide Utente
- 📘 [`QUICK_START.md`](QUICK_START.md) - Avvio rapido in 5 minuti
- 📗 [`pokerstars/SESSION_ROTATION_README.md`](pokerstars/SESSION_ROTATION_README.md) - Guida completa sistema rotazione
- 📙 [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md) - Migrazione da sistema esistente

### Guide Tecniche
- 📕 [`SESSION_ROTATION_SUMMARY.md`](SESSION_ROTATION_SUMMARY.md) - Dettagli implementazione
- 📔 [`IMPLEMENTATION_COMPLETE.md`](IMPLEMENTATION_COMPLETE.md) - Riepilogo implementazione

---

## 🧪 Testing

### Test Completo Sistema Rotazione

```bash
python tmp_rovodev_test_session_rotation.py
```

**Output atteso:**
```
🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!
```

### Test Manuale

```python
from pokerstars.session_manager import SessionRotationManager

manager = SessionRotationManager(
    username="tuoUsername",
    password="tuaPassword"
)

# Effettua richiesta
response = manager.make_request('GET', 'https://...')

# Verifica statistiche
stats = manager.get_stats()
print(stats)

# Cleanup
manager.cleanup()
```

---

## 📈 Monitoring e Log

### Log Console

Il sistema produce log dettagliati:

```
============================================================
INIZIALIZZAZIONE SISTEMA ROTAZIONE SESSIONI PER: username
============================================================

[username_active_1] Login completato con successo!
[username_backup_1] Sessione backup pronta

[username] Statistiche: Richieste totali: 3, Rotazioni: 0

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
ROTAZIONE SESSIONE IN CORSO - Motivo: Limite richieste
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

ROTAZIONE COMPLETATA
```

### File Report

Report salvati in `reports/`:
- `{username}.txt` - Scommesse effettuate
- `{username}_esiti.txt` - Esiti dettagliati

---

## 🔒 Sicurezza

- 🔐 Cookie gestiti solo in memoria (mai salvati su disco)
- 🔒 Credenziali in file `.env` (esclusi da git)
- 🛡️ User-Agent realistico e fingerprinting prevention
- 🌐 Supporto proxy per IP rotation
- 🚫 Estensioni anti-tracking (uBlock, NoRTC)

---

## ⚠️ Risoluzione Problemi

### Problema: Login Fallito

**Soluzione:**
1. Verifica username/password in `accounts.json`
2. Controlla che account non sia bloccato
3. Verifica connessione internet

### Problema: Errore 403 Continui

**Soluzione:**
Il sistema ruoterà automaticamente. Se persiste:
1. Verifica proxy funzionante
2. Controlla che account non sia limitato
3. Disabilita temporaneamente rotazione

### Problema: RAM Elevata

**Soluzione:**
1. Verifica che vecchie sessioni si chiudano (check log)
2. Riduci numero account attivi
3. Aumenta RAM disponibile

### Problema: Chrome Non Si Avvia

**Soluzione:**
```bash
# Aggiorna chromedriver
pip install --upgrade undetected-chromedriver
pip install --upgrade selenium
```

---

## 🛠️ Sviluppo

### Codice Principale

- `app.py` - Loop principale e orchestrazione
- `pokerstars/PokerstarsSession.py` - Gestione account e betting
- `pokerstars/session_manager.py` - Sistema rotazione sessioni

### Estendere Sistema

Per modificare limite richieste per sessione:

```python
# In session_manager.py, classe BrowserSession
self.max_requests = 5  # Cambia questo valore
```

Per aggiungere nuovi trigger di rotazione:

```python
# In session_manager.py, metodo make_request()
if response.status_code == 429:  # Rate limit
    self.rotate_sessions(reason="Rate limit")
```

---

## 📝 Best Practices

1. ✅ **Test Prima di Produzione**: Usa `must_bet: false` per testare
2. ✅ **Monitora Log**: Controlla rotazioni e errori
3. ✅ **Backup Configurazione**: Salva `accounts.json` regolarmente
4. ✅ **Usa Proxy Affidabili**: Per stabilità connessioni
5. ✅ **Aggiorna Chrome**: Mantieni browser aggiornato
6. ✅ **RAM Sufficiente**: ~400MB per account con rotazione

---

## 📊 Performance

### Metriche Tipiche

| Metrica | Valore |
|---------|--------|
| Inizializzazione | ~15-20 sec |
| Rotazione sessione | ~5-8 sec |
| Richiesta HTTP | < 1 sec |
| RAM per account | ~400 MB |
| CPU | Minimo |

---

## 🤝 Supporto

### Documentazione
- Consulta guide nella cartella principale
- Leggi codice sorgente (ben commentato)

### Debug
- Controlla log console per errori
- Esegui script di test per diagnostica
- Verifica configurazione in `accounts.json`

---

## 📜 License

Questo progetto è fornito "as-is" per uso personale.

---

## 🎯 Roadmap

### Implementato ✅
- [x] Sistema rotazione automatica sessioni
- [x] Gestione cookie dinamica
- [x] Recovery automatico errori 403
- [x] Documentazione completa
- [x] Script di test

### Pianificato 📋
- [ ] Dashboard web per monitoring
- [ ] Configurazione dinamica limite richieste
- [ ] Pool di sessioni per account multipli
- [ ] Metriche avanzate (latenza, success rate)
- [ ] Export statistiche JSON/CSV

---

## 🙏 Credits

Sistema di rotazione sessioni implementato nel Novembre 2025.

---

## 📞 Quick Links

- 🚀 [Quick Start](QUICK_START.md) - Avvio rapido
- 📖 [Guida Completa](pokerstars/SESSION_ROTATION_README.md) - Documentazione dettagliata
- 🔄 [Guida Migrazione](MIGRATION_GUIDE.md) - Upgrade da sistema precedente
- ✅ [Implementazione](IMPLEMENTATION_COMPLETE.md) - Stato implementazione

---

**Versione**: 2.0 (con Session Rotation)  
**Ultimo Aggiornamento**: Novembre 2025  
**Stato**: Production Ready ✅
