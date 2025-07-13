"""Utility to rebuild ChromaDB vectors from stored call summaries."""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from server import database as db
from server.vector_db import VectorDB
from server.settings import Settings


@click.command(help="Recreate vector embeddings from existing call summaries")
def cli() -> None:
    """Load summaries from the database and rebuild the vector store."""

    vector_path = Path(Settings().vector_db_path)
    if vector_path.exists():
        shutil.rmtree(vector_path)

    with db.get_session() as session:
        rows = session.query(db.Call.call_sid, db.Call.summary).all()

    vdb = VectorDB(persist_directory=str(vector_path), collection_name="summaries")
    if rows:
        vdb.add_texts([summary for _, summary in rows], ids=[sid for sid, _ in rows])

    click.echo(f"Rebuilt vectors for {len(rows)} summaries")


if __name__ == "__main__":
    cli()
