# Sistema di Rotazione Automatica delle Sessioni

## Panoramica

Il sistema di rotazione automatica delle sessioni è stato implementato per gestire in modo intelligente i cookie e i token di autenticazione, evitando blocchi e limitazioni imposte dal server.

## Come Funziona

### Architettura

Il sistema mantiene **due sessioni browser simultanee**:

1. **Sessione Attiva**: Esegue le richieste HTTP effettive tramite `httpx`
2. **Sessione Backup**: Rimane pronta con credenziali già inserite per un login rapido

### Flusso Operativo

```
Avvio Bot
    ↓
Crea Sessione Attiva (login completo)
    ↓
Crea Sessione Backup (solo credenziali inserite)
    ↓
Sessione Attiva: Richiesta 1 ──→ Aggiorna cookie
    ↓
Sessione Attiva: Richiesta 2 ──→ Aggiorna cookie
    ↓
Sessione Attiva: Richiesta 3 ──→ Aggiorna cookie
    ↓
Sessione Attiva: Richiesta 4 ──→ Aggiorna cookie
    ↓
Sessione Attiva: Richiesta 5 ──→ Aggiorna cookie
    ↓
[ROTAZIONE AUTOMATICA]
    ↓
Backup diventa Attiva (completa login)
    ↓
Crea nuova Sessione Backup
    ↓
Chiude vecchia Sessione Attiva (libera RAM)
    ↓
Ricomincia ciclo...
```

### Trigger di Rotazione

La rotazione avviene automaticamente quando:

1. **Limite Richieste**: Dopo 5 richieste HTTP
2. **Errore 403**: Rilevamento immediato di errore di autenticazione
3. **Errore Generico**: Tentativo di recupero tramite rotazione

## Configurazione

### Abilitare/Disabilitare il Sistema

Nel file `config/pokerstars/accounts.json`, aggiungi il parametro `use_session_rotation`:

```json
{
   "profiles": [
      {
         "username": "tuoUsername",
         "password": "tuaPassword",
         "use_session_rotation": true,
         "stake": 100,
         "filters": ["790399"],
         "enabled": true,
         "must_bet": true
      }
   ]
}
```

- `"use_session_rotation": true` → Sistema di rotazione **ATTIVO** (consigliato)
- `"use_session_rotation": false` → Sistema tradizionale (una sola sessione)
- Se non specificato → **ATTIVO di default**

## Vantaggi

✅ **Prevenzione Blocchi**: Rotazione automatica prima che il server rilevi comportamenti anomali

✅ **Gestione Cookie Dinamica**: Cookie aggiornati automaticamente dopo ogni richiesta

✅ **Zero Downtime**: La sessione backup è sempre pronta, login quasi istantaneo

✅ **Gestione RAM Efficiente**: Chiusura automatica delle sessioni non più utilizzate

✅ **Recovery Automatico**: In caso di errore 403, rotazione immediata senza interruzioni

✅ **Monitoraggio Completo**: Log dettagliati di ogni operazione e statistiche in tempo reale

## Statistiche e Monitoraggio

Il sistema fornisce statistiche in tempo reale:

```
[username] Statistiche: 
  Richieste totali: 23
  Rotazioni: 4
  Richieste sessione attiva: 3/5
```

### Output di Log

Il sistema produce log dettagliati durante l'operazione:

```
============================================================
INIZIALIZZAZIONE SISTEMA ROTAZIONE SESSIONI PER: username
============================================================

[username_active_1] Inizializzazione browser per login...
[username_active_1] Login completato con successo!
[username_active_1] Account ID: 21852175641454373375
[username_active_1] JWT Token recuperato

[username_backup_1] Preparazione sessione backup (solo credenziali)...
[username_backup_1] Sessione backup pronta (credenziali inserite)

============================================================
SISTEMA PRONTO - Sessione attiva: username_active_1
SISTEMA PRONTO - Sessione backup: username_backup_1
============================================================

[username] Invio richiesta tramite SessionRotationManager...
[username] Statistiche: Richieste totali: 1, Rotazioni: 0, Richieste sessione attiva: 0/5
[username_active_1] Richieste effettuate: 1/5

[username] Invio richiesta tramite SessionRotationManager...
[username] Statistiche: Richieste totali: 2, Rotazioni: 0, Richieste sessione attiva: 1/5
[username_active_1] Richieste effettuate: 2/5

... [richieste 3, 4, 5] ...

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
ROTAZIONE SESSIONE IN CORSO - Motivo: Limite richieste raggiunto
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

[username_backup_1] Completamento login da sessione backup...
[username_backup_1] Login backup completato!
[username_backup_1] Account ID: 21852175641454373375

[username_backup_2] Preparazione sessione backup (solo credenziali)...
[username_backup_2] Sessione backup pronta (credenziali inserite)

[username_active_1] Chiusura vecchia sessione attiva in corso...
[username_active_1] Chiusura browser...

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
ROTAZIONE COMPLETATA
Nuova sessione attiva: username_backup_1
Nuova sessione backup: username_backup_2
Rotazioni totali: 1
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

## Dettagli Tecnici

### Componenti Principali

#### `BrowserSession`
Gestisce una singola sessione browser:
- Inizializzazione driver Chrome
- Login completo o preparazione backup
- Gestione cookie e token
- Client `httpx` configurato
- Contatore richieste

#### `SessionRotationManager`
Orchestratore delle sessioni:
- Mantiene riferimenti a sessione attiva e backup
- Gestisce la rotazione
- Intercetta richieste HTTP
- Aggiorna cookie automaticamente
- Monitora errori 403

### Cookie Gestiti

Il sistema gestisce automaticamente tutti i cookie necessari:
- `JWT_ar` - Token JWT di autenticazione
- `login_ar` - Cookie di sessione login
- `_abck` - Anti-bot cookie
- `bm_sv`, `bm_sz`, `bm_mi` - Bot management
- `akaalb_betting_pokerstars` - Load balancer
- E tutti gli altri cookie di sessione

### Gestione Memoria

- **Chiusura Automatica**: Vecchie sessioni chiuse immediatamente dopo rotazione
- **Garbage Collection**: Metodo `__del__` assicura pulizia risorse
- **Browser Cleanup**: Driver Chrome terminati correttamente
- **Client HTTP**: Client `httpx` chiusi e liberati

## Risoluzione Problemi

### Problema: "Impossibile inizializzare sistema rotazione"

**Causa**: Errore durante il login della sessione attiva o backup

**Soluzione**: 
- Verifica credenziali in `accounts.json`
- Controlla proxy se configurato
- Verifica connessione internet
- Il sistema utilizzerà automaticamente il metodo tradizionale

### Problema: Rotazioni troppo frequenti

**Causa**: Errori 403 ripetuti o problemi di autenticazione

**Soluzione**:
- Verifica che l'account non sia bannato/limitato
- Controlla che il proxy funzioni correttamente
- Considera di aumentare il limite da 5 a un valore superiore (modifica `max_requests` in `session_manager.py`)

### Problema: Browser non si chiudono

**Causa**: Processo Chrome rimasto in esecuzione

**Soluzione**:
- Il sistema include gestione automatica
- In caso di problemi: `taskkill /F /IM chrome.exe /T` (Windows)
- Verifica che `cleanup_rotation_manager()` venga chiamato

## Performance

### Tempi Tipici

- **Inizializzazione sistema**: ~15-20 secondi
- **Rotazione sessione**: ~5-8 secondi
- **Richiesta HTTP**: < 1 secondo
- **Aggiornamento cookie**: < 100ms

### Utilizzo Risorse

- **RAM per sessione**: ~150-200 MB
- **RAM totale (2 sessioni)**: ~300-400 MB
- **CPU**: Minimo (picchi durante rotazione)

## Best Practices

1. **Mantieni il sistema abilitato** per massima affidabilità
2. **Monitora i log** per identificare eventuali problemi
3. **Non modificare manualmente** i cookie durante l'esecuzione
4. **Usa proxy affidabili** per evitare blocchi IP
5. **Evita stake troppo alti** nelle prime rotazioni (test sistema)

## FAQ

**Q: Posso usare più di 2 sessioni contemporaneamente?**  
A: Il sistema è progettato per 2 sessioni (attiva + backup). Più sessioni aumenterebbero complessità e utilizzo RAM senza vantaggi significativi.

**Q: Cosa succede se entrambe le sessioni falliscono?**  
A: Il sistema tenterà di ricreare una nuova sessione. Se continua a fallire, l'account verrà disabilitato per evitare ban.

**Q: I cookie vengono salvati su disco?**  
A: No, i cookie sono gestiti solo in memoria per motivi di sicurezza e performance.

**Q: Posso vedere le statistiche in tempo reale?**  
A: Sì, le statistiche sono stampate nei log prima di ogni richiesta. Puoi anche chiamare `session_rotation_manager.get_stats()`.

**Q: Il sistema funziona con proxy?**  
A: Sì, configurando il proxy in `accounts.json` verrà utilizzato per tutte le sessioni.

## Aggiornamenti Futuri

Possibili miglioramenti pianificati:

- [ ] Dashboard web per monitoraggio in tempo reale
- [ ] Configurazione dinamica del limite richieste
- [ ] Pool di sessioni per account multipli
- [ ] Metriche avanzate (latenza, successo rate)
- [ ] Export statistiche in formato JSON/CSV

## Supporto

Per problemi o domande:
1. Controlla i log dettagliati
2. Verifica la configurazione in `accounts.json`
3. Consulta questa documentazione
4. Contatta il supporto tecnico con i log del problema

---

**Versione**: 1.0  
**Data**: Novembre 2025  
**Autore**: Sistema di Betting Automation
