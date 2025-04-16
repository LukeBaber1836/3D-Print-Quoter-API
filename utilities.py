import sys
import subprocess
from typing import Callable

def shell(
    command: str, hide_stdout: bool = False, stream: bool = False, **kwargs
) -> list[str]:  # type: ignore
    """
    Runs the command is a fully qualified shell.

    Args:
        command (str): A command.

    Raises:
        OSError: The error cause by the shell.
    """
    process = subprocess.Popen(
        command,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs,
    )

    output = []
    for line in iter(process.stdout.readline, ""):  # type: ignore
        output += [line.rstrip()]
        if not hide_stdout:
            sys.stdout.write(line)
        if stream:
            yield line.rstrip()  # type: ignore

    process.wait()

    if process.returncode != 0:
        raise OSError("\n".join(output))

    return output

def fancy_shell(
    command: str,
    **kwargs,
):
    for line in shell(command, hide_stdout=True, stream=True, **kwargs):
        print(line)