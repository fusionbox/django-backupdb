import glob

from .exceptions import RestoreError
from .settings import BACKUP_DIR, TIMESTAMP_PATTERN


def get_latest_timestamped_file(ext):
    """
    Gets the latest timestamped backup file name with the given database type
    extension.
    """
    # Make glob pattern
    pattern = '{dir}/{pattern}.{ext}.gz'.format(
        dir=BACKUP_DIR,
        pattern=TIMESTAMP_PATTERN,
        ext=ext,
    )

    # Find files
    l = glob.glob(pattern)
    l.sort()
    l.reverse()

    if not l:
        raise RestoreError("No backups found matching '{0}' pattern".format(pattern))

    return l[0]
