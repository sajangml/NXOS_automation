from datetime import datetime
from pathlib import Path

from nornir.core.task import Result
from nornir_scrapli.tasks import send_command

from NXOS_AUTOMATION.plugins.helpers.auth_utils import init_nornir_secure
from NXOS_AUTOMATION.plugins.helpers.env_utils import filter_nornir_by_env, parse_env_argument


def get_running_config(task):
    result = task.run(task=send_command, command="show running-config")
    running = result.result.result if hasattr(result.result, "result") else result.result
    output_dir = Path("results/configs")
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"{task.host.name.strip()}.cfg"
    filename.write_text(f"! Captured on {datetime.now():%Y%m%d_%H%M%S}\n{running}", encoding="utf-8")
    return Result(host=task.host, result=f"Saved config: {filename}")


if __name__ == "__main__":
    env = parse_env_argument()
    nr = filter_nornir_by_env(init_nornir_secure(), env)
    if not nr.inventory.hosts:
        raise SystemExit(f"No devices found for environment '{env}'")
    results = nr.run(task=get_running_config)
    for host, result in results.items():
        print(f"{host}: {result.result}")
