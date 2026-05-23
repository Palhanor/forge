# Security Policy

## Supported versions

Forge is an early-stage project (POC). Security fixes are applied on the default branch as they are reported and validated.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report sensitive issues privately by opening a [GitHub Security Advisory](https://docs.github.com/en/code-security/security-advisories/guiding-through-the-process-of-reporting-vulnerabilities/reporting-a-vulnerability-with-github-security-advisories) (preferred once the repository is public) or by contacting the maintainers through the channel listed in the repository profile.

Include:

- Description of the issue and impact
- Steps to reproduce
- Affected versions or commits
- Suggested fix (if any)

We aim to acknowledge reports within a reasonable timeframe and coordinate disclosure.

## Security practices for operators

When self-hosting the Forge builder:

1. **API keys** — Set `FORGE_API_KEY` via environment variable on the server. Never commit real keys to git. Use `server/.env.example` as a template only.
2. **CLI config** — `~/.forge/config.json` contains your API key locally; it must stay outside the repository.
3. **Docker socket** — The builder requires access to the Docker daemon to build and run apps. When the builder runs in a container (`docker-compose.yml`), mounting `/var/run/docker.sock` grants effective control over all containers and images on that host (equivalent to root on the Docker host). Run only on hosts you trust; isolate network access in production.
4. **No TLS by default** — Local development uses plain HTTP. Use HTTPS (reverse proxy) before exposing the builder on the internet.
5. **Deploy data** — `server/data/` or `FORGE_DATA_DIR` (e.g. `/var/lib/forge/data` in Compose) may contain uploaded project archives and metadata; protect filesystem permissions and backups.
6. **Authentication** — All builder API routes require `Authorization: Bearer <api_key>`. Use a long, random key in production.

## Application environment variables (POC)

When `envFile` is set in `forge.json`, the referenced file is packaged in the deploy archive and passed to the container at runtime (`docker run --env-file`). Treat these files as secrets: do not commit `.env` to git, and assume anyone with access to `server/data/` can read deployed values. This is not an encrypted secrets store.

## Out of scope for the current POC

- Multi-tenant isolation
- Encrypted secrets store for application environment variables (inline or managed secrets API)
- Automated vulnerability scanning of user-uploaded code
- Production-grade rate limiting and audit logging

These may be addressed in future releases.
