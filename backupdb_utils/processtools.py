from subprocess import Popen, PIPE, CalledProcessError
import os

from .streamtools import err


def pipe_commands_to_file(cmds, path, extra_env=None):
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

    # Start processes
    processes = []
    for cmd_str, cmd in zip(cmd_strs, cmds):
        p_prev = processes[-1][1] if processes else None
        p_curr = Popen(cmd, env=env, stdout=PIPE, stdin=p_prev.stdout if p_prev else None)
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
