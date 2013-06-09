from subprocess import Popen, PIPE, CalledProcessError
import os

from .streams import err


def pipe_commands(cmds, extra_env=None, show_stderr=False, show_last_stdout=False):
    """
    Executes the list of commands piping each one into the next.
    """
    if extra_env:
        env = os.environ.copy()
        env.update(extra_env)
        env_str = ' '.join("{0}='{1}'".format(k, v) for k, v in extra_env.items()) + ' '
    else:
        env = None
        env_str = ''

    cmd_strs = [
        '{env_str}{cmd_str}'.format(env_str=env_str, cmd_str=' '.join(cmd))
        for cmd in cmds
    ]

    err('* Running `{0}`'.format(' | '.join(cmd_strs)), verbosity=2)

    with open('/dev/null', 'w') as NULL:
        # Start processes
        num_cmds = len(cmds)
        processes = []
        for i, (cmd_str, cmd) in enumerate(zip(cmd_strs, cmds), 1):
            p_prev = processes[-1][1] if processes else None

            if i == num_cmds:
                p_stdout = None if show_last_stdout else NULL
            else:
                p_stdout = PIPE
            p_stdin = p_prev.stdout if p_prev else None
            p_stderr = None if show_stderr else NULL

            p_curr = Popen(cmd, env=env, stdout=p_stdout, stdin=p_stdin, stderr=p_stderr)
            processes.append((cmd_str, p_curr))

        # Close processes
        for cmd_str, p in processes:
            if p.stdout:
                p.stdout.close()
            if p.wait() != 0:
                raise CalledProcessError(cmd=cmd_str, returncode=p.returncode)


def pipe_commands_to_file(cmds, path, extra_env=None, show_stderr=False):
    """
    Executes the list of commands piping each one into the next and writing
    stdout of the last process into a file at the given path.
    """
    if extra_env:
        env = os.environ.copy()
        env.update(extra_env)
        env_str = ' '.join("{0}='{1}'".format(k, v) for k, v in extra_env.items()) + ' '
    else:
        env = None
        env_str = ''

    cmd_strs = [
        '{env_str}{cmd_str}'.format(env_str=env_str, cmd_str=' '.join(cmd))
        for cmd in cmds
    ]

    err('* Saving output of `{0}`'.format(' | '.join(cmd_strs)), verbosity=2)

    with open('/dev/null', 'w') as NULL:
        # Start processes
        processes = []
        for cmd_str, cmd in zip(cmd_strs, cmds):
            p_prev = processes[-1][1] if processes else None

            p_stdin = p_prev.stdout if p_prev else None
            p_stderr = None if show_stderr else NULL

            p_curr = Popen(cmd, env=env, stdout=PIPE, stdin=p_stdin, stderr=p_stderr)
            processes.append((cmd_str, p_curr))

        p_last = processes[-1][1]

        with open(path, 'w') as f:
            # Write data to file in chunks (works for arbitrarily large files)
            while True:
                data = p_last.stdout.read(512 * 1024)
                if len(data) == 0:
                    break
                f.write(data)

            # Close processes
            for cmd_str, p in processes:
                p.stdout.close()
                if p.wait() != 0:
                    raise CalledProcessError(cmd=cmd_str, returncode=p.returncode)
