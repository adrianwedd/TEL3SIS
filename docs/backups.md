# Database Backups

TEL3SIS stores call data in SQLite and vector embeddings on disk. Regular backups protect this data from corruption or accidental deletion.

## Manual Backup

Run the `tel3sis` CLI to create an archive containing both the database and vector store:

```bash
tel3sis backup [--s3]
```

Use the optional `--s3` flag to upload the archive to the bucket defined by `BACKUP_S3_BUCKET`.

## Manual Restore

To restore from a backup archive:

```bash
tel3sis restore path/to/backup.tar.gz
```

The command replaces the current database file and vector directory with the contents of the archive.

## Scheduled Backups

Backups can be automated using **cron** or Celery beat. Example cron entry creating a nightly backup at 2am:

```cron
0 2 * * * cd /opt/tel3sis && /usr/local/bin/tel3sis backup --s3
```

When using Celery beat, schedule the `server.tasks.backup_data` task with the desired interval.

