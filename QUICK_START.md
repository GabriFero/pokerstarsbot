# Quick Start - Sistema di Rotazione Sessioni

## 🚀 Avvio Rapido (5 minuti)

### Passo 1: Verifica Requisiti

```bash
# Verifica Python
python --version
# Output atteso: Python 3.8 o superiore

# Verifica dipendenze
pip list | findstr httpx
pip list | findstr selenium
pip list | findstr undetected-chromedriver
```

Se mancano dipendenze:
```bash
pip install -r requirements.txt
```

### Passo 2: Configura Account

Apri `config/pokerstars/accounts.json` e modifica:

```json
{
   "profiles": [
      {
         "username": "TUO_USERNAME_QUI",
         "password": "TUA_PASSWORD_QUI",
         "stake": 100,
         "filters": ["790399"],
         "enabled": true,
         "must_bet": false,
         "use_session_rotation": true
      }
   ]
}
```

⚠️ **IMPORTANTE**: Imposta `"must_bet": false` per il primo test!

### Passo 3: Test Rapido

```bash
python tmp_rovodev_test_session_rotation.py
```

**Output atteso:**
```
======================================================================
TEST SISTEMA DI ROTAZIONE SESSIONI
======================================================================

🔧 Profilo di test: tuoUsername
🔧 Proxy: Nessuno

TEST 1: Inizializzazione SessionRotationManager
----------------------------------------------------------------------
[tuoUsername_active_1] Inizializzazione browser per login...
[tuoUsername_active_1] Login completato con successo!
✅ Inizializzazione completata

TEST 2: Verifica Token
----------------------------------------------------------------------
JWT Token: eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2R0NNIiwidGFnIjoi...
Token: 5D253F952171050E9708CCF5C85F2599
Account ID: 21852175641454373375
✅ Tutti i token sono presenti

... [continua con altri test] ...

🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!
```

### Passo 4: Verifica Rotazione

Durante il test, cerca nel log:

```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
ROTAZIONE SESSIONE IN CORSO - Motivo: Limite richieste raggiunto
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

Se vedi questo messaggio → **Sistema funzionante! ✅**

### Passo 5: Avvia Bot Completo (Opzionale)

Se il test è OK, puoi avviare il bot completo:

```bash
python app.py
```

## 🔍 Cosa Cercare nei Log

### ✅ Segnali Positivi

```
✓ Sistema rotazione sessioni attivo
✓ Limite richieste per sessione: 5
✓ Rotazione automatica su errore 403
✓ Login completato con successo!
✓ ROTAZIONE COMPLETATA
```

### ⚠️ Segnali di Attenzione

```
⚠️ Impossibile inizializzare sistema rotazione
⚠️ Nessuna rotazione registrata
⚠️ Errore 403 RILEVATO
```

### ❌ Errori Critici

```
❌ File di configurazione non trovato
❌ Nessun profilo abilitato
❌ Impossibile effettuare il login
❌ Alcuni token sono mancanti
```

## 🎯 Test Specifici

### Test 1: Solo Inizializzazione

```python
from pokerstars.session_manager import SessionRotationManager

manager = SessionRotationManager(
    username="tuoUsername",
    password="tuaPassword"
)

# Verifica token
tokens = manager.get_current_tokens()
print(f"JWT: {tokens['jwt_token'][:50]}...")
print(f"Account ID: {tokens['account_id']}")

# Cleanup
manager.cleanup()
```

### Test 2: Una Singola Richiesta

```python
from pokerstars.session_manager import SessionRotationManager

manager = SessionRotationManager(
    username="tuoUsername",
    password="tuaPassword"
)

# Richiesta GET all'API alberatura
response = manager.make_request(
    'GET',
    'https://betting.pokerstars.it/api/lettura-palinsesto-sport/palinsesto/live/alberatura',
    timeout=15
)

print(f"Status: {response.status_code}")
print(f"Richieste: {manager.get_stats()['total_requests']}")

manager.cleanup()
```

### Test 3: Test Rotazione Forzata

```python
from pokerstars.session_manager import SessionRotationManager

manager = SessionRotationManager(
    username="tuoUsername",
    password="tuaPassword"
)

# Effettua 6 richieste per forzare la rotazione
url = 'https://betting.pokerstars.it/api/lettura-palinsesto-sport/palinsesto/live/alberatura'

for i in range(6):
    response = manager.make_request('GET', url, timeout=15)
    stats = manager.get_stats()
    print(f"Richiesta {i+1}: Rotazioni={stats['total_rotations']}")

# Verifica rotazione
stats = manager.get_stats()
assert stats['total_rotations'] >= 1, "Rotazione non avvenuta!"
print("✅ Rotazione verificata!")

manager.cleanup()
```

## 🐛 Risoluzione Problemi Rapida

### Problema: Chrome non si avvia

**Soluzione:**
```bash
# Aggiorna chromedriver
pip install --upgrade undetected-chromedriver
pip install --upgrade selenium
```

### Problema: Errore "Login fallito"

**Verifica:**
1. Username e password corretti in `accounts.json`
2. Account non bloccato su PokerStars
3. Connessione internet funzionante

### Problema: "RAM insufficiente"

**Soluzione:**
Chiudi altri programmi o disabilita rotazione:
```json
{
   "use_session_rotation": false
}
```

### Problema: Processi Chrome rimasti aperti

**Soluzione Windows:**
```bash
taskkill /F /IM chrome.exe /T
```

**Soluzione Linux/Mac:**
```bash
pkill -9 chrome
```

## 📊 Metriche di Successo

Dopo il test, verifica:

| Metrica | Valore Atteso | Tuo Valore |
|---------|---------------|------------|
| Login riusciti | 2 (attiva + backup) | ___ |
| Token recuperati | 3 (JWT, token, account_id) | ___ |
| Richieste HTTP | 7 | ___ |
| Rotazioni | ≥ 1 | ___ |
| Errori | 0 | ___ |

## 🎓 Tutorial Video (Testuale)

### Scenario: Prima Configurazione

```
1. Apri terminale
   > cd /percorso/al/progetto

2. Apri config/pokerstars/accounts.json
   > notepad config\pokerstars\accounts.json

3. Modifica username e password
   {
     "username": "iltuousername",
     "password": "latuapassword",
     "use_session_rotation": true,
     "must_bet": false
   }

4. Salva e chiudi

5. Esegui test
   > python tmp_rovodev_test_session_rotation.py

6. Attendi 2-3 minuti per completamento

7. Verifica output "TUTTI I TEST COMPLETATI CON SUCCESSO!"

8. Se OK, attiva bot completo
   > python app.py
```

## 🔄 Workflow Quotidiano

### Mattina: Avvio Sistema
```bash
# 1. Verifica configurazione
notepad config\pokerstars\accounts.json

# 2. Avvia bot
python app.py

# 3. Monitora log (primi 5 minuti)
# Cerca "Sistema rotazione sessioni attivo"
```

### Durante il Giorno: Monitoraggio
```bash
# Verifica log in console
# Cerca "ROTAZIONE COMPLETATA" ogni ~5 richieste
# Verifica "SCOMMESSA PIAZZATA" per conferma funzionamento
```

### Sera: Statistiche
```bash
# Controlla file report in cartella reports/
dir reports\*.txt

# Verifica email ricevute con report
```

## 📝 Checklist Giornaliera

Prima di avviare il bot ogni giorno:

- [ ] Verifica che Chrome sia aggiornato
- [ ] Controlla `accounts.json` per configurazione corretta
- [ ] Verifica connessione internet
- [ ] Verifica che proxy (se usato) sia attivo
- [ ] Controlla spazio RAM disponibile (>1GB)
- [ ] Chiudi eventuali processi Chrome residui
- [ ] Backup di `accounts.json` (opzionale ma consigliato)

## 🎯 Obiettivi di Apprendimento

Dopo aver completato questo Quick Start, dovresti:

✅ Saper configurare un account in `accounts.json`  
✅ Saper eseguire il test del sistema di rotazione  
✅ Riconoscere log di successo vs errore  
✅ Saper avviare il bot completo  
✅ Saper interpretare le statistiche  
✅ Risolvere problemi comuni  

## 🚀 Prossimi Passi

1. ✅ Completa Quick Start
2. 📖 Leggi `pokerstars/SESSION_ROTATION_README.md` per dettagli
3. 🔧 Consulta `MIGRATION_GUIDE.md` se hai sistema esistente
4. 🎯 Attiva `"must_bet": true` quando sei sicuro
5. 📊 Monitora statistiche e ottimizza configurazione

## ❓ FAQ Rapide

**Q: Quanto tempo richiede il primo avvio?**  
A: ~2-3 minuti (login attivo + backup)

**Q: Posso testare senza scommettere?**  
A: Sì! Imposta `"must_bet": false`

**Q: Quanta RAM serve?**  
A: ~400MB per account con rotazione

**Q: Funziona senza proxy?**  
A: Sì, proxy è opzionale

**Q: Posso usare più account contemporaneamente?**  
A: Sì, aggiungi più profili in `accounts.json`

**Q: Come fermo il bot?**  
A: Premi `Ctrl+C` nel terminale

**Q: I cookie vengono salvati?**  
A: Solo in memoria, non su disco

**Q: Posso vedere le sessioni browser?**  
A: Sì, rimuovi `headless=True` nel codice per vedere le finestre

## 📞 Supporto Rapido

**Errore login**: Verifica credenziali  
**Errore 403**: Sistema ruoterà automaticamente  
**RAM piena**: Chiudi altri programmi  
**Chrome non parte**: Reinstalla chromedriver  
**Test fallito**: Controlla log per dettagli  

---

**Tempo stimato completamento**: 5-10 minuti  
**Difficoltà**: ⭐⭐☆☆☆ (Facile)  
**Supporto**: Consulta documentazione completa per maggiori dettagli
