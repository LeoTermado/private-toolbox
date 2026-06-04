"""Safe external-process execution helpers (no Flask).

Wraps subprocess so tools that shell out to a local executable (Ghostscript,
ffmpeg, tesseract, …) get a single, structured, non-raising result instead of
scattering try/except around subprocess calls.

Design notes:
- Commands are passed as an argument list (no shell), which avoids shell-injection
  and quoting problems with paths that contain spaces.
- run_command never raises for the usual failure modes (missing binary, non-zero
  exit, timeout). It always returns a ProcessResult; inspect `.ok`.
"""
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProcessResult:
    """Outcome of a single external command run."""
    command: List[str] = field(default_factory=list)
    ok: bool = False
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    error: Optional[str] = None  # set when the process could not run at all


def command_exists(command):
    """Return True if `command` is resolvable on PATH (via shutil.which)."""
    return shutil.which(command) is not None


def resolve_command(*candidates):
    """Return the first candidate command name that exists on PATH, else None.

    Useful where the same tool has different names per platform, e.g.
    resolve_command('gswin64c', 'gswin32c', 'gs') for Ghostscript on Windows/Unix.
    """
    for name in candidates:
        if name and command_exists(name):
            return name
    return None


def _as_text(value):
    """Coerce subprocess stdout/stderr (str or bytes or None) to str."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_command(command, timeout=None, cwd=None, env=None, input_data=None):
    """Run an external command and return a ProcessResult (never raises here).

    - command: a sequence of args, e.g. ["gs", "-sDEVICE=pdfwrite", ...].
    - timeout: seconds before the process is killed (None = no limit).
    - cwd/env: forwarded to subprocess.run.
    - input_data: optional text written to the process stdin.
    """
    command = list(command)
    if not command:
        return ProcessResult(command=command, ok=False, error="Empty command")

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            input=input_data,
            check=False,
        )
        return ProcessResult(
            command=command,
            ok=(proc.returncode == 0),
            returncode=proc.returncode,
            stdout=_as_text(proc.stdout),
            stderr=_as_text(proc.stderr),
        )
    except subprocess.TimeoutExpired as exc:
        return ProcessResult(
            command=command,
            ok=False,
            timed_out=True,
            stdout=_as_text(exc.stdout),
            stderr=_as_text(exc.stderr),
            error=f"Command timed out after {timeout}s",
        )
    except FileNotFoundError:
        return ProcessResult(
            command=command,
            ok=False,
            error=f"Command not found: {command[0]}",
        )
    except OSError as exc:
        return ProcessResult(command=command, ok=False, error=str(exc))
