import contextlib
import logging

logger = logging.getLogger(__name__)


def bar(msg='', width=40, position=None):
    r"""
    Returns a string with text centered in a bar caption.

    Examples:
    >>> bar('test', width=10)
    '== test =='
    >>> bar(width=10)
    '=========='
    >>> bar('Richard Dean Anderson is...', position='top', width=50)
    '//========= Richard Dean Anderson is... ========\\\\'
    >>> bar('...MacGyver', position='bottom', width=50)
    '\\\\================= ...MacGyver ================//'
    """
    if position == 'top':
        start_bar = '//'
        end_bar = r'\\'
    elif position == 'bottom':
        start_bar = r'\\'
        end_bar = '//'
    else:
        start_bar = end_bar = '=='

    if msg:
        msg = ' ' + msg + ' '

    width -= 4

    return start_bar + msg.center(width, '=') + end_bar


class SectionError(Exception):
    pass


class SectionWarning(Exception):
    pass


@contextlib.contextmanager
def section(msg):
    """
    Context manager that prints a top bar to stderr upon entering and a bottom
    bar upon exiting.  The caption of the top bar is specified by `msg`.  The
    caption of the bottom bar is '...done!' if the context manager exits
    successfully.  If a SectionError or SectionWarning is raised inside of the
    context manager, SectionError.message or SectionWarning.message is passed
    to logging.error or logging.warning respectively and the bottom bar caption
    becomes '...skipped.'.
    """
    logger.info(bar(msg, position='top'))
    try:
        yield
    except SectionError as e:
        logger.error(e)
        logger.info(bar('...skipped.', position='bottom'))
    except SectionWarning as e:
        logger.warning(e)
        logger.info(bar('...skipped.', position='bottom'))
    else:
        logger.info(bar('...done!', position='bottom'))
