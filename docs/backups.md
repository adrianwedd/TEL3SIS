# Database Backups

TEL3SIS stores call data in SQLite and vector embeddings on disk. Regular backups protect this data from corruption or accidental deletion.

## Manual Backup

Run the maintenance script to create an archive containing both the database and vector store:

```bash
python -m scripts.maintenance.backup [--s3]
```

The optional `--s3` flag uploads the archive to the bucket defined by `BACKUP_S3_BUCKET`.

## Manual Restore

To restore from a backup archive:

```bash
python -m scripts.maintenance.restore path/to/backup.tar.gz
```

The command replaces the current database file and vector directory with the contents of the archive.

## Scheduled Backups

Backups can be automated using **cron** or Celery beat. Example cron entry creating a nightly backup at 2am:

```cron
0 2 * * * cd /opt/tel3sis && /usr/local/bin/python -m scripts.maintenance.backup --s3
```

When using Celery beat, schedule the `server.tasks.backup_data` task with the desired interval.

