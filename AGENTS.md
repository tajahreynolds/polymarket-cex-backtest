# Repository Guidelines

## Project Structure & Module Organization
- `src/`: core strategy logic (`proxy.py`, `edge.py`) used for probability mapping and edge computation.
- `data/`: ingestion and export scripts (`pull_binance.py`, `pull_polymarket.py`, `export_signals.py`) plus raw datasets under `data/raw/`.
- `notebooks/`: research and backtest workflow (`01_data_loading.ipynb` through `04_equity_curve.ipynb`).
- `landing/`: Next.js 14 TypeScript marketing/API app (`app/`, `lib/`, `package.json`, `vercel.json`).
- `README.md`: strategy assumptions, limitations, and high-level architecture.

## Build, Test, and Development Commands
- Python environment (recommended): `python -m venv .venv && source .venv/bin/activate`
- Install Python deps (if needed for scripts/notebooks): `pip install pandas numpy jupyter requests`
- Pull market data: `python data/pull_binance.py` and `python data/pull_polymarket.py`
- Export strategy signals: `python data/export_signals.py`
- Run landing app locally:
  - `cd landing && npm install`
  - `npm run dev` (local dev server)
  - `npm run build` (production build)
  - `npm run start` (serve built app)

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indentation, `snake_case` for functions/variables, module names lowercase.
- TypeScript/React: 2-space indentation in existing files, `camelCase` for variables/functions, `PascalCase` for components.
- Keep strategy math deterministic and side-effect-light in `src/`; isolate I/O in `data/` scripts and API routes.

## Testing Guidelines
- Current status: no formal automated test suite is checked in.
- When adding Python logic, include `pytest` tests under a new `tests/` directory (`test_<module>.py`).
- For `landing/`, add unit/integration tests before major API or pricing-flow changes (suggested: Vitest + React Testing Library).
- Validate changes by running affected scripts and `npm run build` in `landing` before opening a PR.

## Commit & Pull Request Guidelines
- Follow existing commit style from history: conventional prefixes like `feat(scope): ...`, `fix(scope): ...`, `chore(scope): ...`.
- Keep commits focused; avoid mixing strategy logic, data snapshots, and landing-page refactors in one commit.
- PRs should include:
  - concise problem/solution summary,
  - local validation steps run,
  - screenshots for `landing/` UI changes,
  - linked issue/context when applicable.

## Security & Configuration Tips
- Do not commit secrets or API keys; keep runtime secrets in local env files (for `landing`, use `.env.local`).
- Treat files in `data/raw/` as large/generated artifacts; commit only when necessary for reproducibility.
