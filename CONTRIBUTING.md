# Contributing to Forge

Thank you for your interest in contributing. Forge is a personal deploy platform with a CLI (`forge`) and a builder API (`forge-server`).

## Getting started

### Requirements

- Python 3.11+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for deploy/build features)
- Git

### Local setup

```bash
git clone <repository-url> forge
cd forge

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e cli/
pip install -e server/
```

Or use Make:

```bash
make setup
source .venv/bin/activate
```

### Configure the CLI and run the builder

```bash
# Terminal 1 — builder
cp server/.env.example server/.env   # optional local file; never commit server/.env
export FORGE_API_KEY=your-dev-key-here
forge-server

# Terminal 2 — CLI
forge setup --host http://localhost:8000 --api-key your-dev-key-here
forge ping
```

See [README.md](README.md) for full usage, examples under `examples/`, and framework conventions.

## Project layout

| Path | Package | Description |
|------|---------|-------------|
| `cli/` | `forge-cli` | Typer CLI (`forge` command) |
| `server/` | `forge-server` | FastAPI builder (`forge-server` command) |
| `examples/` | — | Sample apps for manual testing |

Runtime data (`server/data/`) and virtualenv (`.venv/`) are gitignored.

## Making changes

1. Create a branch from the default branch.
2. Keep changes focused; match existing code style (plain Python, minimal dependencies).
3. Test locally:
   - `forge validate` / `forge deploy` against an example app
   - Restart `forge-server` after server code changes (or rely on uvicorn reload in dev)
4. Update [README.md](README.md) if behavior or commands change.
5. Add a note to [CHANGELOG.md](CHANGELOG.md) under **Unreleased** for user-visible changes.

## Pull requests

- Describe what changed and why.
- Link related issues if applicable.
- Confirm you did not commit secrets (`.env`, `server/data/`, API keys).
- PRs may be reviewed for security implications (Docker access, auth, archive handling).

Use the pull request template when opening a PR on GitHub.

## Code of conduct

Be respectful and constructive. Maintainers may close issues or PRs that are out of scope or duplicate existing work.

## Questions

Open a GitHub Discussion or Issue for bugs and feature requests. For security concerns, see [SECURITY.md](SECURITY.md).
