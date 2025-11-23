# Guida alla Migrazione - Sistema di Rotazione Sessioni

## Panoramica

Questa guida spiega come migrare dal sistema tradizionale al nuovo sistema di rotazione automatica delle sessioni.

## ⚠️ Importante: Backup Prima della Migrazione

Prima di procedere, fai un backup di:
- `config/pokerstars/accounts.json`
- Qualsiasi personalizzazione del codice

## Passaggi di Migrazione

### 1. Verifica Requisiti

Assicurati di avere:
- Python 3.8+
- Tutte le dipendenze installate: `pip install -r requirements.txt`
- Chrome installato e aggiornato
- Spazio RAM sufficiente (~400MB per account)

### 2. Aggiorna il File di Configurazione

Apri `config/pokerstars/accounts.json` e aggiungi il parametro `use_session_rotation` a ogni profilo:

**Prima:**
```json
{
   "profiles": [
      {
         "username": "tuoUsername",
         "password": "tuaPassword",
         "stake": 100,
         "enabled": true,
         "must_bet": true
      }
   ]
}
```

**Dopo:**
```json
{
   "profiles": [
      {
         "username": "tuoUsername",
         "password": "tuaPassword",
         "stake": 100,
         "enabled": true,
         "must_bet": true,
         "use_session_rotation": true
      }
   ]
}
```

### 3. Test in Modalità Sicura

Prima di attivare le scommesse reali, testa il sistema:

1. Imposta `"must_bet": false` nel profilo
2. Imposta `"use_session_rotation": true`
3. Esegui: `python app.py`
4. Verifica i log per confermare che tutto funzioni

**Output atteso:**
```
============================================================
INIZIALIZZAZIONE SISTEMA ROTAZIONE SESSIONI PER: tuoUsername
============================================================

[tuoUsername_active_1] Inizializzazione browser per login...
[tuoUsername_active_1] Login completato con successo!
[tuoUsername_backup_1] Sessione backup pronta (credenziali inserite)

============================================================
SISTEMA PRONTO - Sessione attiva: tuoUsername_active_1
SISTEMA PRONTO - Sessione backup: tuoUsername_backup_1
============================================================
```

### 4. Test delle Richieste

Esegui lo script di test per verificare il funzionamento:

```bash
python tmp_rovodev_test_session_rotation.py
```

**Cosa fa il test:**
- Inizializza il sistema di rotazione
- Verifica i token di autenticazione
- Effettua 7 richieste HTTP reali
- Verifica che la rotazione avvenga dopo 5 richieste
- Pulisce tutte le risorse

**Output atteso finale:**
```
🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!
```

### 5. Attivazione Produzione

Quando sei sicuro che tutto funzioni:

1. Imposta `"must_bet": true` nel profilo
2. Rimuovi il file di test: `del tmp_rovodev_test_session_rotation.py`
3. Esegui normalmente: `python app.py`

## Compatibilità con il Sistema Esistente

### Retrocompatibilità

Il nuovo sistema è **completamente retrocompatibile**:

- Se `use_session_rotation` non è specificato → **Sistema di rotazione ATTIVO** (default)
- Se `use_session_rotation: false` → Sistema tradizionale (vecchio comportamento)
- Se `use_session_rotation: true` → Sistema di rotazione (nuovo comportamento)

### Coesistenza di Profili

Puoi avere profili con diversi sistemi contemporaneamente:

```json
{
   "profiles": [
      {
         "username": "profilo1",
         "use_session_rotation": true,
         "enabled": true
      },
      {
         "username": "profilo2",
         "use_session_rotation": false,
         "enabled": true
      }
   ]
}
```

## Differenze Principali

| Aspetto | Sistema Tradizionale | Sistema Rotazione |
|---------|---------------------|-------------------|
| Sessioni Browser | 1 (solo durante login) | 2 (sempre attive) |
| Cookie | Statici | Aggiornati dinamicamente |
| Limite Richieste | Nessuno | 5 per sessione |
| Gestione 403 | Manuale | Automatica |
| Uso RAM | ~150 MB | ~400 MB |
| Affidabilità | Media | Alta |

## Risoluzione Problemi Comuni

### Problema: "Impossibile inizializzare sistema rotazione"

**Sintomo:** Errore durante l'avvio del sistema

**Causa:** Login fallito

**Soluzione:**
```json
{
   "use_session_rotation": false
}
```
Temporaneamente, fino a risolvere il problema di login

### Problema: RAM insufficiente

**Sintomo:** Sistema lento o crash

**Causa:** Troppi profili attivi con rotazione

**Soluzione:**
- Disabilita rotazione su alcuni profili
- Aumenta RAM disponibile
- Riduci numero di profili attivi

### Problema: Browser non si chiudono

**Sintomo:** Processi Chrome rimangono attivi

**Soluzione:**
```bash
# Windows
taskkill /F /IM chrome.exe /T

# Il sistema include già gestione automatica
```

### Problema: Rotazioni troppo frequenti

**Sintomo:** Rotazione dopo ogni richiesta

**Causa:** Errori 403 continui

**Soluzione:**
1. Verifica che l'account non sia limitato
2. Controlla proxy
3. Aumenta timeout nelle richieste

## Rollback al Sistema Tradizionale

Se desideri tornare al sistema precedente:

1. Imposta `"use_session_rotation": false` in tutti i profili
2. Riavvia l'applicazione
3. Il sistema userà il metodo tradizionale

**OPPURE**

Rimuovi completamente il parametro dal file di configurazione (sconsigliato).

## Monitoraggio Post-Migrazione

### Log da Controllare

Cerca nei log:
- ✅ "Sistema rotazione sessioni attivo"
- ✅ "ROTAZIONE COMPLETATA"
- ⚠️ "Impossibile inizializzare sistema rotazione"
- ❌ Errori 403 ripetuti

### Metriche da Verificare

Dopo 1 ora di funzionamento:
- Numero di rotazioni (atteso: ~1 ogni 5 richieste)
- Numero di errori 403 (atteso: 0)
- Uso RAM (atteso: ~400MB per account)
- Scommesse piazzate con successo

### Dashboard Temporanea

Puoi monitorare le statistiche aggiungendo questo al tuo codice:

```python
if session.session_rotation_manager:
    stats = session.session_rotation_manager.get_stats()
    print(f"Stats {session.username}: {stats}")
```

## Best Practices Post-Migrazione

1. **Monitora i primi giorni**: Controlla log attentamente
2. **Inizia con un solo account**: Testa su un profilo prima di attivare tutti
3. **Usa proxy affidabili**: Il sistema funziona meglio con proxy stabili
4. **Backup regolari**: Salva `accounts.json` dopo ogni login riuscito
5. **Aggiorna Chrome**: Mantieni Chrome aggiornato per compatibilità

## FAQ Migrazione

**Q: Devo reinstallare le dipendenze?**  
A: No, se hai già `requirements.txt` installato, non serve altro.

**Q: I miei token esistenti funzioneranno?**  
A: Sì, ma verranno sostituiti con quelli del rotation manager al primo login.

**Q: Posso migrare account per account?**  
A: Sì, imposta `use_session_rotation: true` solo su alcuni profili.

**Q: Cosa succede ai token salvati in accounts.json?**  
A: Vengono aggiornati automaticamente dopo ogni login.

**Q: Il sistema funziona su Linux/Mac?**  
A: Sì, ma potrebbe richiedere piccole modifiche ai percorsi (usa `/` invece di `\\`).

**Q: Serve configurazione aggiuntiva?**  
A: No, il sistema funziona out-of-the-box con il solo parametro `use_session_rotation`.

## Supporto

Se riscontri problemi durante la migrazione:

1. Controlla i log per errori specifici
2. Verifica che Chrome sia aggiornato
3. Testa con `tmp_rovodev_test_session_rotation.py`
4. Consulta `pokerstars/SESSION_ROTATION_README.md`
5. Crea un report con i log completi

## Checklist Migrazione

- [ ] Backup di `accounts.json`
- [ ] Aggiunto parametro `use_session_rotation` ai profili
- [ ] Eseguito test con `must_bet: false`
- [ ] Eseguito script di test
- [ ] Verificati log di inizializzazione
- [ ] Verificata prima rotazione
- [ ] Monitorato uso RAM
- [ ] Testato in produzione con `must_bet: true`
- [ ] Rimossi file di test temporanei

---

**Versione Guida**: 1.0  
**Data**: Novembre 2025  
**Ultima Revisione**: Novembre 2025
