# Forge

Repositório da plataforma **Forge**. A CLI fica em `cli/`, o builder (API FastAPI) em `server/`.

**Requisitos:** Python 3.11+ · [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para deploy)

| | |
|---|---|
| **License** | [MIT](LICENSE) |
| **Contributing** | [CONTRIBUTING.md](CONTRIBUTING.md) |
| **Security** | [SECURITY.md](SECURITY.md) |
| **Changelog** | [CHANGELOG.md](CHANGELOG.md) |

> **Never commit** `server/.env`, `server/data/`, or real API keys. Use `server/.env.example` and `forge setup` locally. See [SECURITY.md](SECURITY.md).

## Estrutura

```
forge/
├── .venv/          # dependências Python (não versionado)
├── .gitignore
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── Makefile        # atalho: make setup
├── cli/            # pacote forge-cli
├── server/         # API FastAPI do builder
│   ├── forge_server/
│   └── data/       # deploys recebidos (gerado em runtime, não versionado)
└── examples/       # projetos de exemplo para testar deploy
    ├── fastapi-ping/
    ├── nodejs-ping/       # Node.js (JavaScript)
    ├── nodejs-ping-ts/    # Node.js (TypeScript)
    └── react-example/
```

## Setup (CLI global + dependências no venv)

O venv fica na **raiz** do repositório; a instalação aponta para o pacote em `cli/`.

### 1. Clonar e entrar no repositório

```bash
git clone <url-do-repositorio> forge
cd forge
```

Anote o caminho absoluto do clone (ex.: `$HOME/Projects/forge`). Você vai usá-lo no passo 4.

### 2. Criar o venv e instalar a CLI

Na **raiz** do repositório (`forge/`, não dentro de `cli/`):

```bash
make setup
# ou manualmente:
# python3 -m venv .venv && source .venv/bin/activate
# pip install -e cli/ && pip install -e server/
deactivate
```

O `pip install -e cli/` instala o comando `forge`; o `pip install -e server/` instala `forge-server` (API local). Ambos usam o mesmo venv na raiz.

### 3. Verificar a instalação no venv

```bash
.venv/bin/forge version
```

Deve imprimir `forge-cli v0.1.0` (ou a versão atual do projeto).

### 4. Expor `forge` globalmente no shell

Adicione ao final do arquivo de configuração do seu shell (`~/.zshrc` no zsh ou `~/.bashrc` no bash). **Substitua** `/caminho/para/forge` pelo diretório onde você clonou o repositório:

```bash
# Forge CLI — comando global; dependências ficam no venv do projeto
export FORGE_ROOT="/caminho/para/forge"
if [ -d "$FORGE_ROOT/.venv/bin" ]; then
  export PATH="$FORGE_ROOT/.venv/bin:$PATH"
fi
```

Recarregue o shell:

```bash
source ~/.zshrc   # ou: source ~/.bashrc
```

### 5. Confirmar que funciona em qualquer pasta

```bash
which forge
forge version
cd /tmp && forge version
```

`which forge` deve apontar para `.../forge/.venv/bin/forge`.

## Configuração da CLI (`forge setup`)

Configure o builder (host + API key). Os valores são salvos em `~/.forge/config.json`:

```bash
forge setup
# ou modo não interativo:
forge setup --host http://localhost:8000 --api-key sua-chave-secreta
```

Formato do arquivo:

```json
{
  "host": "http://localhost:8000",
  "api_key": "sua-chave-secreta"
}
```

Todos os comandos que falam com o builder (`ping`, `deploy`, `list`) exigem `api_key` configurada.

## `forge.json` (manifesto do projeto)

Cada projeto deployável precisa de um `forge.json` na raiz. A CLI valida o arquivo antes do upload (`forge deploy` e `forge validate`).

### Campos

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `name` | sim | Identificador do app (slug: `a-z`, `0-9`, `-`) |
| `runtime` | sim | `python` ou `node` |
| `framework` | sim | Ver tabela abaixo |
| `port` | não | Porta do app (1–65535) |
| `start` | não | Comando de start (usado na Fase 2) |
| `build` | não | Comando de build (Node/React/Next) |
| `subdomain` | não | Subdomínio futuro (slug; default = `name`) |
| `envFile` | não | Caminho relativo a um arquivo de env (ex.: `.env`) incluído no deploy e injetado no container via `docker run --env-file` |
| `checks` | não | Lista de validações locais (lint, test, etc.) executadas na CLI antes do empacotamento; ver abaixo |

**`checks` (CI/CD local):** array de objetos `{ "name": "<slug>", "run": "<comando shell>" }`, executados em ordem no diretório do projeto. Se algum check falhar, `forge deploy` e `forge validate` abortam antes do upload. Os comandos usam o ambiente local (venv, `node_modules`, etc.) — instale as dependências de test/lint antes do deploy. Use `--skip-checks` para pular.

**`framework` por `runtime`:**

| `runtime` | Valores permitidos |
|-----------|-------------------|
| `python` | `script`, `fastapi` |
| `node` | `react`, `next`, `nodejs` |

### Exemplos

Python (script):

```json
{
  "name": "meu-script",
  "runtime": "python",
  "framework": "script",
  "start": "python main.py"
}
```

Python (FastAPI):

```json
{
  "name": "minha-api",
  "runtime": "python",
  "framework": "fastapi",
  "port": 8000,
  "start": "uvicorn app.main:app --host 0.0.0.0 --port 8000",
  "checks": [
    { "name": "test", "run": "pytest -q" }
  ]
}
```

Node (Next.js):

```json
{
  "name": "meu-front",
  "runtime": "node",
  "framework": "next",
  "port": 3000,
  "build": "npm run build",
  "start": "npm start",
  "subdomain": "meu-front"
}
```

## Comandos

| Comando | Descrição |
|---------|-----------|
| `forge setup` | Configura `host` e `api_key` em `~/.forge/config.json` |
| `forge version` | Versão da CLI |
| `forge validate` | Valida `forge.json` no diretório atual (e roda `checks`, se definidos) |
| `forge validate --skip-checks` | Valida só o manifesto, sem executar `checks` |
| `forge ping` | Verifica conectividade com o builder (autenticado) |
| `forge deploy` | Valida `forge.json`, roda `checks`, empacota e envia para `{host}/deploy` |
| `forge deploy --skip-checks` | Deploy sem executar `checks` |
| `forge deploy -n outro-nome` | Sobrescreve o `name` do `forge.json` |
| `forge list` | Lista apps via `GET {host}/apps` |
| `forge stop <name>` | Para o container (status `stopped`; dados e imagem permanecem) |
| `forge start <name>` | Sobe de novo um app parado (`docker start` ou `docker run` da imagem) |
| `forge delete <name>` | Remove app permanentemente (container, imagem, registry, arquivos em `server/data/`) |
| `forge delete -y <name>` | Delete sem confirmação interativa |

**Status no registry:** `stored`, `building`, `running`, `stopped`, `failed`.

## Rodar o builder local

O builder exige a variável `FORGE_API_KEY` (mesmo valor configurado no `forge setup`):

```bash
export FORGE_API_KEY=sua-chave-secreta
forge-server
```

Referência em [`server/.env.example`](server/.env.example).

A API sobe em `http://localhost:8000`. Os arquivos de deploy são salvos em `server/data/deployments/{id}/`.

**Requisito para deploy com container:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução. O builder usa o Docker do host para build/run.

**Frameworks suportados na POC:** `fastapi` (Python), `nodejs` (Express/servidor Node) e `react` (Vite + build estático com `serve`).

### POC FastAPI — Postman em `/ping`

Projeto de exemplo em [`examples/fastapi-ping/`](examples/fastapi-ping/):

- `app/main.py` com `GET /ping`
- `forge.json` + `requirements.txt`
- `tests/test_ping.py` com pytest (check `test` no `forge.json`)

Convenção para FastAPI:

| Arquivo | Obrigatório | Descrição |
|---------|-------------|-----------|
| `forge.json` | sim | `framework` deve ser `fastapi` |
| `requirements.txt` | recomendado | Se ausente, o builder gera um mínimo com `fastapi` e `uvicorn` |
| `app/main.py` | sim* | App FastAPI (`app` exportado como `app`) |
| `start` em `forge.json` | não | Default: `uvicorn app.main:app --host 0.0.0.0 --port <port>` |
| `checks` em `forge.json` | não | Ex.: `[{"name": "test", "run": "pytest -q"}]` — roda antes do deploy |

Setup local e deploy com checks:

```bash
cd examples/fastapi-ping
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
forge validate   # manifesto + pytest
forge deploy
```

Para ver o deploy bloqueado por teste falhando: altere temporariamente o assert em `tests/test_ping.py` (ex.: espere `"wrong"` em vez de `"pong"`), rode `forge deploy` (aborta antes do upload), corrija o teste e rode `forge deploy` de novo.

Após `forge deploy`, o container expõe uma porta no host (18000–18999). Teste no Postman:

```http
GET http://localhost:<host_port>/ping
```

### POC React (Vite) — browser

Projeto de exemplo em [`examples/react-example/`](examples/react-example/):

- React 19 + Vite 6
- `forge.json` com `"framework": "react"`

Convenção para React:

| Arquivo | Obrigatório | Descrição |
|---------|-------------|-----------|
| `forge.json` | sim | `runtime: "node"`, `framework: "react"` |
| `package.json` | sim | Scripts `build` (default: `npm run build`) |
| `build` em `forge.json` | não | Default: `npm run build` |
| `port` em `forge.json` | não | Porta do container (default: `3000`) |

O builder gera um Dockerfile multi-stage (`npm install` → `npm run build` → `serve -s dist`). O primeiro build pode levar alguns minutos.

Após `forge deploy`, abra no navegador a `url` exibida (porta no host entre 18000–18999).

### POC Node.js — Postman em `/ping` (JavaScript e TypeScript)

Exemplos:

- [`examples/nodejs-ping/`](examples/nodejs-ping/) — Express em **JavaScript** (`index.js`)
- [`examples/nodejs-ping-ts/`](examples/nodejs-ping-ts/) — Express em **TypeScript** (`src/index.ts` → `dist/`)

O builder usa um Dockerfile **multi-stage**: `npm install` → **`npm run build`** (compila TS quando há `tsconfig.json`) → imagem final só com deps de produção + artefatos de runtime.

Convenção para Node.js:

| Arquivo | Obrigatório | Descrição |
|---------|-------------|-----------|
| `forge.json` | sim | `runtime: "node"`, `framework: "nodejs"` |
| `package.json` | sim | Scripts `build` / `start` recomendados |
| `tsconfig.json` | TS | Se existir, Forge trata como projeto TypeScript |
| `build` em `forge.json` | não | **TS:** default `npm run build`. **JS:** default `true` (sem build) |
| `start` em `forge.json` | não | **TS:** default `node dist/index.js`. **JS:** default `node <main>` (`package.json` → `main` ou `index.js`) |
| `port` em `forge.json` | não | Porta do container (default: `3000`; `PORT` no container) |
| `envFile` em `forge.json` | não | Arquivo de variáveis para produção (ex.: `.env`); deve existir localmente antes do `forge deploy` |
| `.env` | se `envFile` | Criar a partir de `.env.example` (`cp .env.example .env`); não versionado |

Com `envFile: ".env"`, o endpoint `/ping` retorna `process.env.PING_MESSAGE` (ex.: `hello-from-forge`).

```http
GET http://localhost:<host_port>/ping
```

### Rodar vários apps ao mesmo tempo

Cada app usa um **nome** diferente no `forge.json` e recebe sua **própria porta** no host:

```bash
# Com o builder rodando (forge-server)
cd examples/fastapi-ping && forge deploy    # ex.: http://localhost:18000
cd examples/nodejs-ping && forge deploy       # Node.js (JS)
cd examples/nodejs-ping-ts && forge deploy    # Node.js (TS)
cd examples/react-example && forge deploy     # React
forge list
```

- **FastAPI:** `GET http://localhost:<porta-ping-api>/ping` (Postman)
- **Node.js (JS/TS):** `GET http://localhost:<porta>/ping` (Postman) — ex. `nodejs-ping`, `nodejs-ping-ts`
- **React:** `http://localhost:<porta-react-example>/` (navegador)

### Fluxo completo (localhost)

**Terminal 1 — builder:**

```bash
export FORGE_API_KEY=dev-secret-key
forge-server
```

**Terminal 2 — CLI e deploy:**

```bash
forge setup --host http://localhost:8000 --api-key dev-secret-key
forge ping
cd /caminho/para/forge/examples/fastapi-ping
forge validate
forge deploy
forge list
# Postman: GET http://localhost:<host_port>/ping
forge stop ping-api
forge start ping-api
# forge delete -y ping-api   # remove tudo permanentemente
```

### Contrato da API (builder)

Todas as rotas exigem autenticação:

```
Authorization: Bearer <api_key>
```

| Situação | HTTP |
|----------|------|
| Token ausente ou inválido | 401 |
| `FORGE_API_KEY` não definida no servidor | 503 |

**`GET /ping`** — `{ "message": "Pong!" }`

**`POST /deploy`** — `multipart/form-data`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `archive` | arquivo | `.tar.gz` do projeto |
| `name` | string | Nome do app |
| `source_path` | string | Caminho absoluto do projeto |
| `manifest` | string | JSON do `forge.json` validado pela CLI |

Resposta (JSON): `{ "message": "...", "id": "...", "status": "running", "url": "http://localhost:18001", "host_port": 18001 }`.

O builder extrai o tarball, gera `Dockerfile` (FastAPI ou React), executa `docker build` + `docker run`.

**`GET /apps`** — resposta JSON:

```json
{ "apps": [{ "name": "meu-app", "status": "running", "url": "http://localhost:18000", "host_port": 18000 }] }
```

**`POST /apps/{name}/stop`** — para o container; status → `stopped`.

**`POST /apps/{name}/start`** — inicia container parado ou recria a partir da imagem; status → `running` (retorna `url`, `host_port`).

**`DELETE /apps/{name}`** — remove container, imagem Docker, entrada no registry e pasta `server/data/deployments/{id}/`.

O arquivo enviado exclui `.git`, `.venv`, `node_modules`, `__pycache__` e outros artefatos comuns.

## Recriar o venv

Se apagar `.venv` ou mudar de máquina, repita os passos 2 e 4 (o bloco no shell só precisa ser ajustado se o caminho do clone mudar).

```bash
cd /caminho/para/forge
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e cli/
pip install -e server/
deactivate
```

## Alternativa: só com venv ativo

Se não quiser alterar o shell, use o venv manualmente em cada sessão:

```bash
source /caminho/para/forge/.venv/bin/activate
forge ping
```

Ou chame o binário diretamente: `/caminho/para/forge/.venv/bin/forge ping`.

## Desenvolvimento

- CLI: `cli/forge_cli/`
- Server: `server/forge_server/`

Após mudar dependências:

```bash
source .venv/bin/activate
make install
# ou: pip install -e cli/ && pip install -e server/
```

Contributing guidelines: [CONTRIBUTING.md](CONTRIBUTING.md). CI runs smoke imports on push/PR (see `.github/workflows/ci.yml`).
