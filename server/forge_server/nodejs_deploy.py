import json
from pathlib import Path

DEFAULT_NODEJS_START_JS = "node index.js"
DEFAULT_NODEJS_START_TS = "node dist/index.js"
DEFAULT_NODEJS_BUILD_TS = "npm run build"
DEFAULT_NODEJS_BUILD_JS = "true"
DEFAULT_NODEJS_BUILD_TS_PRISMA = "npx prisma generate && npm run build"

PRISMA_RUNTIME_COPY = """COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=build /app/node_modules/@prisma ./node_modules/@prisma
COPY --from=build /app/prisma ./prisma"""


def _package_main(source_dir: Path) -> str:
    pkg_path = source_dir / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text())
            main = pkg.get("main")
            if isinstance(main, str) and main.strip():
                return main.strip().lstrip("./")
        except json.JSONDecodeError:
            pass
    return "index.js"


def is_typescript_project(source_dir: Path) -> bool:
    return (source_dir / "tsconfig.json").exists()


def has_prisma(source_dir: Path) -> bool:
    return (source_dir / "prisma" / "schema.prisma").exists()


def resolve_nodejs_commands(
    source_dir: Path,
    manifest: dict,
) -> tuple[str, str, str]:
    """
    Resolve build command, start command, and Dockerfile COPY lines for runtime stage.
    """
    has_ts = is_typescript_project(source_dir)
    uses_prisma = has_prisma(source_dir)

    build_cmd = (manifest.get("build") or "").strip()
    start_cmd = (manifest.get("start") or "").strip()

    if has_ts:
        build_cmd = build_cmd or (
            DEFAULT_NODEJS_BUILD_TS_PRISMA if uses_prisma else DEFAULT_NODEJS_BUILD_TS
        )
        start_cmd = start_cmd or DEFAULT_NODEJS_START_TS
        runtime_copy = (
            PRISMA_RUNTIME_COPY if uses_prisma else "COPY --from=build /app/dist ./dist"
        )
    else:
        build_cmd = build_cmd or DEFAULT_NODEJS_BUILD_JS
        main_file = _package_main(source_dir)
        start_cmd = start_cmd or f"node {main_file}"
        if uses_prisma:
            runtime_copy = PRISMA_RUNTIME_COPY.replace(
                "COPY --from=build /app/dist ./dist\n", ""
            ) + f"\nCOPY --from=build /app/{main_file} ./{main_file}"
        else:
            runtime_copy = f"COPY --from=build /app/{main_file} ./{main_file}"

    return build_cmd, start_cmd, runtime_copy
