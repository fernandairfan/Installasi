import paramiko
from database import get_active_vps


def run_command(user_id, command):
    vps = get_active_vps(user_id)
    if not vps:
        return "No VPS selected"

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(vps["host"], username=vps["user"], password=vps["password"], timeout=10)

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode() + stderr.read().decode()

        ssh.close()
        return output if output else "Done"
    except Exception as e:
        return str(e)
