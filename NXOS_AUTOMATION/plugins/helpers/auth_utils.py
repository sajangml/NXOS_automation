import io
import os
import tempfile
from pathlib import Path

import yaml
from nornir import InitNornir

from NXOS_AUTOMATION.plugins.helpers.env_utils import get_active_env

_cached_credentials = {}


def prompt_credentials(force_prompt=False):
    if not force_prompt and "USERNAME" in os.environ and "PASSWORD" in os.environ:
        return os.environ["USERNAME"], os.environ["PASSWORD"]

    username = os.environ.get("USERNAME", "")
    password = os.environ.get("PASSWORD", "")
    if not username or not password:
        raise RuntimeError("USERNAME and PASSWORD must be set before connecting to devices.")

    os.environ["USERNAME"] = username
    os.environ["PASSWORD"] = password
    _cached_credentials["username"] = username
    _cached_credentials["password"] = password
    return username, password


def _find_config_file() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "inventory" / "config.yaml",
        here.parents[3] / "inventory" / "config.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find Nornir config.yaml. Tried:\n  - "
        + "\n  - ".join(map(str, candidates))
    )


def init_nornir_secure(force_prompt=False):
    env = get_active_env().upper()
    print(f"\nInitializing Nornir for environment: {env}")

    prompt_credentials(force_prompt=force_prompt)

    config_file = _find_config_file()
    with io.open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml", encoding="utf-8")
    yaml.dump(config_data, tmp)
    tmp.close()

    nr = InitNornir(config_file=tmp.name)

    for host in nr.inventory.hosts.values():
        host.port = int(host.port or 22)
        host.username = os.environ.get("USERNAME")
        host.password = os.environ.get("PASSWORD")
        if "scrapli" in host.connection_options:
            scrapli_conn = host.connection_options["scrapli"]
            scrapli_conn.hostname = host.hostname
            scrapli_conn.username = os.environ["USERNAME"]
            scrapli_conn.password = os.environ["PASSWORD"]
            scrapli_conn.port = int(scrapli_conn.port or host.port or 22)

    print(f"Initialized Nornir using {config_file}\n")
    return nr
