import click
from server import tasks


@click.command(help="Dump database and vector store to a compressed archive")
@click.option("--s3", is_flag=True, help="Upload to S3 if BACKUP_S3_BUCKET is set")
def cli(s3: bool) -> None:
    path = tasks.backup_data.run(upload_to_s3=s3)
    click.echo(path)


if __name__ == "__main__":
    cli()
