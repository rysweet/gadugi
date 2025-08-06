import subprocess

_real_run = subprocess.run

def _patched_run(*args, **kwargs):
    cmd = args[0] if args else kwargs.get("args", [])
    if isinstance(cmd, list) and "claude" in cmd[0]:
        class Result:
            returncode = 0
            stdout = "TeamCoach analysis completed\n"
            stderr = ""
        return Result()
    return _real_run(*args, **kwargs)

subprocess.run = _patched_run