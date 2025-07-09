import click

from server import tasks
from server.database import Call, get_session


@click.group(help="Maintenance utilities for TEL3SIS")
def cli() -> None:
    """Entry point for maintenance CLI."""
    pass


@cli.command("list-calls")
def list_calls_cmd() -> None:
    """Print all stored call records."""
    with get_session() as session:
        calls = session.query(Call).order_by(Call.created_at.desc()).all()
        for call in calls:
            click.echo(
                f"{call.id}: {call.call_sid} {call.from_number} -> {call.to_number} @ {call.created_at.isoformat()}"
            )


@cli.command("prune")
@click.option(
    "--days",
    default=30,
    show_default=True,
    help="Remove calls older than DAYS days",
)
def prune_cmd(days: int) -> None:
    """Delete call records older than ``days`` days."""
    removed = tasks.cleanup_old_calls.run(days=days)
    click.echo(f"Removed {removed} calls older than {days} days.")


if __name__ == "__main__":
    cli()
