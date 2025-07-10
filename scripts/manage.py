import click
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig

from server import database as db
from server import tasks


@click.group(help="Management commands for TEL3SIS")
def cli() -> None:
    """Entry point for management CLI."""


@cli.command("create-user")
@click.argument("username")
@click.argument("password")
@click.option("--role", default="user", show_default=True, help="User role")
def create_user_cmd(username: str, password: str, role: str) -> None:
    """Create a user with the given credentials."""
    db.init_db()
    db.create_user(username, password, role)
    click.echo(f"Created user '{username}' with role '{role}'.")


@cli.command("delete-user")
@click.argument("username")
def delete_user_cmd(username: str) -> None:
    """Delete a user account by ``username``."""
    db.init_db()
    if db.delete_user(username):
        click.echo(f"Deleted user '{username}'.")
    else:
        click.echo(f"User '{username}' not found.")


@cli.command("generate-api-key")
@click.argument("owner")
def generate_api_key_cmd(owner: str) -> None:
    """Generate and output an API key for OWNER."""
    db.init_db()
    key = db.create_api_key(owner)
    click.echo(key)


@cli.command()
def migrate() -> None:
    """Apply database migrations."""
    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_command.upgrade(alembic_cfg, "head")
    click.echo("Database migrated to head.")


@cli.command()
@click.option(
    "--days", default=30, show_default=True, help="Delete calls older than DAYS"
)
def cleanup(days: int) -> None:
    """Remove old call records and audio files."""
    removed = tasks.cleanup_old_calls.run(days=days)
    click.echo(f"Removed {removed} calls older than {days} days.")


if __name__ == "__main__":
    cli()
