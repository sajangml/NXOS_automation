from nornir.core.task import Result
from nornir_scrapli.tasks import send_command

from NXOS_AUTOMATION.plugins.helpers.auth_utils import init_nornir_secure
from NXOS_AUTOMATION.plugins.helpers.env_utils import filter_nornir_by_env, parse_env_argument


SHOW_COMMANDS = [
    "show hostname",
    "show interface status",
    "show ip interface brief",
    "show bgp ipv4 unicast summary",
    "show nve peers",
    "show lldp neighbors",
]


def run_basic_sanity(task):
    sections = []
    for command in SHOW_COMMANDS:
        response = task.run(task=send_command, command=command)
        output = response.result.result if hasattr(response.result, "result") else response.result
        sections.append(f"### {command}\n{output}")
    return Result(host=task.host, result="\n\n".join(sections))


if __name__ == "__main__":
    env = parse_env_argument()
    nr = filter_nornir_by_env(init_nornir_secure(), env)
    if not nr.inventory.hosts:
        raise SystemExit(f"No devices found for environment '{env}'")
    results = nr.run(task=run_basic_sanity)
    for host, result in results.items():
        print(f"{host}: {'failed' if result.failed else 'ok'}")
