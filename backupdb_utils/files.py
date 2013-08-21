import glob

from .exceptions import RestoreError
from .settings import BACKUP_DIR, BACKUP_TIMESTAMP_PATTERN


def get_latest_timestamped_file(ext, dir=BACKUP_DIR, pattern=BACKUP_TIMESTAMP_PATTERN):
    """
    Gets the latest timestamped backup file name with the given database type
    extension.
    """
    pattern = '{dir}/{pattern}.{ext}.gz'.format(
        dir=dir,
        pattern=pattern,
        ext=ext,
    )

    l = glob.glob(pattern)
    l.sort()
    l.reverse()

    if not l:
        raise RestoreError("No backups found matching '{0}' pattern".format(pattern))

    return l[0]
