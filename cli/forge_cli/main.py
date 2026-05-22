import typer
from forge_cli.commands import delete as delete_cmd
from forge_cli.commands import deploy as deploy_cmd
from forge_cli.commands import list_apps as list_cmd
from forge_cli.commands import ping as ping_cmd
from forge_cli.commands import setup as setup_cmd
from forge_cli.commands import start as start_cmd
from forge_cli.commands import stop as stop_cmd
from forge_cli.commands import validate as validate_cmd
from forge_cli.commands import version as version_cmd

app = typer.Typer(
    name="forge",
    help="Forge — Personal deploy platform CLI",
    add_completion=False,
    no_args_is_help=True,
)

app.command("setup")(setup_cmd.setup)
app.command("ping")(ping_cmd.ping)
app.command("version")(version_cmd.version)
app.command("validate")(validate_cmd.validate)
app.command("deploy")(deploy_cmd.deploy)
app.command("list")(list_cmd.list_apps)
app.command("stop")(stop_cmd.stop)
app.command("start")(start_cmd.start)
app.command("delete")(delete_cmd.delete)

if __name__ == "__main__":
    app()
