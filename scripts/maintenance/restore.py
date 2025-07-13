import click
from server import tasks


@click.command(help="Restore database and vector store from ARCHIVE")
@click.argument("archive")
def cli(archive: str) -> None:
    tasks.restore_data.run(archive)
    click.echo(f"Restored from {archive}")


if __name__ == "__main__":
    cli()
