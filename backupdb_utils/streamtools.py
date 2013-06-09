import contextlib
import sys


def check_verbosity(old_fn):
    """
    Checks that the provided verbosity argument is less than or equal to the
    current verbosity level before executing the decorated method.  If this
    check fails, the method is not executed.
    """
    def new_fn(self, *args, **kwargs):
        verbosity = kwargs.pop('verbosity', 0)
        if verbosity <= self._verbosity:
            old_fn(self, *args, **kwargs)
    return new_fn


class StandardStreams(object):
    """
    Class to facilitate writing of log messages to standard streams.
    """
    def __init__(self):
        self._verbosity = 0

    @check_verbosity
    def err(self, msg, newline=True):
        """
        Prints the given message to stderr, including a newline by default.

        Examples:
        >>> err('Test')
        Test
        >>> err('Test', newline=False)
        Test>>>
        """
        sys.stderr.write(msg + ('\n' if newline else ''))

    @check_verbosity
    def bar(self, msg='', width=50, position=None, stream=sys.stderr):
        """
        Prints a bar text effect to the standard stream specified by `stream`.

        Examples:
        >>> bar('test', width=10)
        == test ==
        >>> bar(width=10)
        ==========
        >>> bar('Richard Dean Anderson is...', position='top')
        //========= Richard Dean Anderson is... ========\\\\
        >>> bar('...MacGyver', position='bottom')
        \\\\================= ...MacGyver ================//
        """
        width = max(width, len(msg) + 4)

        if msg:
            bar_len = width - len(msg) - 2
        else:
            bar_len = width

        is_odd = bool(bar_len % 2)
        bar_len //= 2

        start_bar = '=' * (bar_len + (1 if is_odd else 0))
        end_bar = '=' * bar_len

        if position == 'top':
            start_bar = '//' + start_bar[2:]
            end_bar = end_bar[:-2] + '\\\\'
        elif position == 'bottom':
            start_bar = '\\\\' + start_bar[2:]
            end_bar = end_bar[:-2] + '//'

        if msg:
            msg = ' {0} '.format(msg)

        stream.write(start_bar + msg + end_bar + '\n')

    def set_verbosity(self, verbosity):
        """
        Sets the current verbosity level.

        Examples:
        >>> set_verbosity(0)
        >>> err('Good morning', verbosity=0)
        Hello
        >>> err('Dave', verbosity=1)
        >>> set_verbosity(1)
        >>> err('Vietnam!!', verbosity=1)
        Vietnam!!
        """
        self._verbosity = verbosity


standard_streams = StandardStreams()

err = standard_streams.err
bar = standard_streams.bar
set_verbosity = standard_streams.set_verbosity


@contextlib.contextmanager
def section(msg):
    bar(msg, position='top')
    yield
    bar('...done!', position='bottom')
