
def validate(cmd):
    allowed = ["apt", "bash", "curl", "wget"]
    blocked = ["rm -rf", "shutdown", "mkfs"]

    if any(b in cmd for b in blocked):
        return False

    return any(cmd.startswith(a) for a in allowed)
