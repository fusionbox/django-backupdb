from subprocess import Popen, PIPE, CalledProcessError
import logging
import os
import shutil

logger = logging.getLogger(__name__)


def extend_env(extra_env):
    """
    Copies and extends the current environment with the values present in
    `extra_env`.
    """
    env = os.environ.copy()
    env.update(extra_env)
    return env


def get_env_str(env):
    """
    Gets a string representation of a dict as though it contained environment
    variable values.
    """
    return ' '.join("{0}='{1}'".format(k, v) for k, v in env.items())


def pipe_commands(cmds, extra_env=None, show_stderr=False, show_last_stdout=False):
    """
    Executes the list of commands piping each one into the next.
    """
    env = extend_env(extra_env) if extra_env else None
    env_str = (get_env_str(extra_env) + ' ') if extra_env else ''
    cmd_strs = [env_str + ' '.join(cmd) for cmd in cmds]

    logger.info('Running `{0}`'.format(' | '.join(cmd_strs)))

    with open('/dev/null', 'w') as NULL:
        # Start processes
        processes = []
        last_i = len(cmds) - 1
        for i, (cmd_str, cmd) in enumerate(zip(cmd_strs, cmds)):
            if i == last_i:
                p_stdout = None if show_last_stdout else NULL
            else:
                p_stdout = PIPE
            p_stdin = processes[-1][1].stdout if processes else None
            p_stderr = None if show_stderr else NULL

            p = Popen(cmd, env=env, stdout=p_stdout, stdin=p_stdin, stderr=p_stderr)
            processes.append((cmd_str, p))

        # Close processes
        error = False
        for cmd_str, p in processes:
            if p.stdout:
                p.stdout.close()
            if p.wait() != 0:
                error = True
        if error:
            raise CalledProcessError(cmd=cmd_str, returncode=p.returncode)


def pipe_commands_to_file(cmds, path, extra_env=None, show_stderr=False):
    """
    Executes the list of commands piping each one into the next and writing
    stdout of the last process into a file at the given path.
    """
    env = extend_env(extra_env) if extra_env else None
    env_str = (get_env_str(extra_env) + ' ') if extra_env else ''
    cmd_strs = [env_str + ' '.join(cmd) for cmd in cmds]

    logger.info('Saving output of `{0}`'.format(' | '.join(cmd_strs)))

    with open('/dev/null', 'w') as NULL:
        # Start processes
        processes = []
        for cmd_str, cmd in zip(cmd_strs, cmds):
            p_stdin = processes[-1][1].stdout if processes else None
            p_stderr = None if show_stderr else NULL

            p = Popen(cmd, env=env, stdout=PIPE, stdin=p_stdin, stderr=p_stderr)
            processes.append((cmd_str, p))

        p_last = processes[-1][1]

        with open(path, 'wb') as f:
            shutil.copyfileobj(p_last.stdout, f)

            # Close processes
            error = False
            for cmd_str, p in processes:
                p.stdout.close()
                if p.wait() != 0:
                    error = True
            if error:
                raise CalledProcessError(cmd=cmd_str, returncode=p.returncode)
