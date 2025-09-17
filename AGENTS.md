# Repository Guidelines

## Project Structure & Module Organization
- `app.py`: Entry point orchestrating sessions, logins, and bet flows.
- `pokerstars/`: Core domain logic — `PokerstarsSession.py`, `pokerstars_utils.py`, `pokerstars_constants.py`, request payloads under `request_jsons/`, and browser-extension assets under `ublock/` and `nortc/`.
- `webshare/` and `proxyshare/`: Proxy provider API clients and helpers.
- `betburger/`: External odds API integration utilities.
- `config/`: Local configuration and credentials (`proxy.env`, `gmail.env`, `pokerstars/accounts.json`).
- `utils/`: Shared settings (e.g., `app_settings.json`).
- `reports/`: Logs or diagnostic output; safe to ignore in code reviews.

## Build, Test, and Development Commands
- Create venv: `python -m venv .venv`
- Activate (Windows): `.venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt`
- Run locally: `python app.py`
- Optional format: `pip install black && black .` (no formatter enforced yet)

## Coding Style & Naming Conventions
- Python 3.x, follow PEP 8; 4-space indent; aim for ~88-char lines.
- Files/modules: lowercase with underscores. Classes: PascalCase. Functions/vars: snake_case.
- Constants: UPPER_SNAKE (see `pokerstars_constants.py`). Add type hints for new/edited functions.

## Testing Guidelines
- No formal test suite yet. Prefer `pytest` with tests under `tests/` mirroring package layout (e.g., `tests/test_pokerstars_session.py`).
- Name tests `test_*`; keep unit tests deterministic and offline where possible.
- Quick smoke test: configure `config/pokerstars/accounts.json` with an enabled test profile, then run `python app.py` and monitor console output and token updates in `accounts.json`.

## Commit & Pull Request Guidelines
- Commits: imperative mood summaries (≤72 chars), grouped by logical change; avoid committing `.venv/`, vendor assets, or secrets.
- PRs: include a clear description, rationale, any config changes, reproduction steps, and relevant logs/screenshots; link related issues/tasks.

## Security & Configuration Tips
- Never commit credentials or real tokens. Keep `config/*.env` and `config/pokerstars/accounts.json` out of commits; sanitize `reports/` artifacts.
- Proxies: configure via `config/proxy.env`; use `webshare/` and `proxyshare/` utilities rather than hardcoding.
- Selenium/Chrome: ensure Chrome is installed; `undetected-chromedriver` should match the local browser version; avoid hardcoded paths.

