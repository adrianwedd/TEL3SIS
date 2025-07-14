import asyncio
from pathlib import Path

import click
import uvicorn
import yaml

from scripts import dev_test_call, warmup_whisper, red_team, manage as manage_module


@click.group(
    help="TEL3SIS command line interface for development and maintenance tasks"
)
def cli() -> None:
    """Unified entry point for development helpers."""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Bind address")
@click.option("--port", default=3000, show_default=True, type=int, help="Listen port")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Run the TEL3SIS API server."""
    uvicorn.run(
        "server.app:create_app", host=host, port=port, reload=reload, factory=True
    )


@cli.command("red-team")
@click.option(
    "-o", "--output", type=click.Path(path_type=Path), help="File to write results"
)
def red_team_cmd(output: Path | None) -> None:
    """Execute adversarial prompt suite."""
    prompts = red_team.load_prompts()
    results = asyncio.run(red_team.run_red_team(prompts))
    summary = red_team.summarize_results(results)
    data = {"results": results, "summary": summary}
    if output:
        with open(output, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)
    else:
        click.echo(yaml.safe_dump(data))


@cli.command()
@click.option("--model", default="base", show_default=True, help="Whisper model name")
def warmup(model: str) -> None:
    """Preload a Whisper model for faster startup."""
    warmup_whisper.load_model(model)


@cli.command("dev-call")
def dev_call() -> None:
    """Start a local streaming conversation using microphone and speakers."""
    asyncio.run(dev_test_call.main())


@cli.command()
@click.option("--s3", is_flag=True, help="Upload to S3 if BACKUP_S3_BUCKET is set")
def backup(s3: bool) -> None:
    """Trigger an asynchronous backup of the database and vector store."""
    from server.tasks import backup_data

    backup_data.delay(upload_to_s3=s3)
    click.echo("Backup task queued")


@cli.command()
@click.argument("archive")
def restore(archive: str) -> None:
    """Trigger an asynchronous restore from ARCHIVE."""
    from server.tasks import restore_data

    restore_data.delay(archive)
    click.echo(f"Restore task queued for {archive}")


# Expose management commands under `tel3sis manage`
cli.add_command(manage_module.cli, name="manage")


if __name__ == "__main__":
    cli()
