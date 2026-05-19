import sys
import yaml
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from datetime import datetime


# ---------- Helper: safe YAML loader ----------
def load_yaml(path: Path):
    if not path.exists():
        print(f" Missing YAML file: {path}")
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


# ---------- Helper: render YAML file through Jinja with env ----------
def render_yaml_with_env(path: Path, env_vars: dict):
    """
    Treat a YAML file as a Jinja template, render it with 'env',
    then parse the result as YAML again.
    This is what resolves things like {{ env.local_admin_hash }}
    inside vars_common_template.yaml.
    """
    if not path.exists():
        print(f" Missing template YAML: {path}")
        return {}
    raw = path.read_text(encoding="utf-8")
    jenv = Environment()
    rendered_text = jenv.from_string(raw).render(env=env_vars)
    data = yaml.safe_load(rendered_text)
    return data or {}


def derive_snmp_engine_id(mgmt_ip: str) -> str:
    """
    Build a deterministic 24-character demo SNMP engine ID from the device management IP.
    Example:
      192.0.2.11 -> 19:2A:0A:2A:11:FF:FF:FF:FF:FF:FF:FF
    """
    ip_only = str(mgmt_ip).split("/", 1)[0].strip()
    engine_seed = ip_only.replace(".", "A")
    padded = (engine_seed + ("F" * 24))[:24]
    octets = [padded[i:i + 2] for i in range(0, len(padded), 2)]
    return ":".join(octets)


# ---------- Parse environment argument ----------
if len(sys.argv) < 2:
    print("Usage: python scripts/generate_all_configs.py <environment>")
    sys.exit(1)

env_name = sys.argv[1].lower()

base_dir = Path(__file__).resolve().parents[1]
env_path = base_dir / "environments" / env_name

device_vars_file = env_path / "device_vars.yaml"
common_vars_file = env_path / "vars_common_template.yaml"
env_vars_file = env_path / "env_vars.yaml"
interfaces_file = env_path / "interfaces.yaml"

# ---------- Load env + device YAMLs ----------
env_vars = load_yaml(env_vars_file)
device_data = load_yaml(device_vars_file)

for device in device_data.get("devices", []):
    if not device.get("snmp_engine_id") and device.get("mgmt_ip"):
        device["snmp_engine_id"] = derive_snmp_engine_id(device["mgmt_ip"])

# Pre-render common vars YAML with env (fixes {{ env.* }} in YAML)
common_data = render_yaml_with_env(common_vars_file, env_vars)

# Load interfaces.yaml (no Jinja inside, so plain load)
interfaces_data = load_yaml(interfaces_file)


def enrich_spineleaf(devices: list[dict]) -> None:
    leaves = [d for d in devices if str(d.get("role", d.get("type", ""))).lower() == "leaf"]
    spines = [d for d in devices if str(d.get("role", d.get("type", ""))).lower() == "spine"]

    for device in leaves:
        leaf_id = int(device.get("leaf_id", 0))
        device["bgp_neighbors"] = [
            {
                "ip": f"10.0.{leaf_id}.0",
                "remote_as": 65000,
                "description": "spine01",
                "update_source": f"Ethernet1/49",
            },
            {
                "ip": f"10.0.{leaf_id + 100}.0",
                "remote_as": 65000,
                "description": "spine02",
                "update_source": f"Ethernet1/50",
            },
        ]

    for spine in spines:
        is_spine02 = str(spine.get("hostname", "")).lower() == "spine02"
        offset = 100 if is_spine02 else 0
        spine["bgp_neighbors"] = [
            {
                "ip": f"10.0.{int(leaf['leaf_id']) + offset}.1",
                "remote_as": leaf["bgp_asn"],
                "description": leaf["hostname"],
                "update_source": f"Ethernet1/{int(leaf['leaf_id'])}",
            }
            for leaf in leaves
        ]


enrich_spineleaf(device_data.get("devices", []))

# ---------- Jinja template setup ----------
template_dir = base_dir / "base_template"
jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

# Make 'env' available globally in all templates
jinja_env.globals.update(env=env_vars)

template = jinja_env.get_template("generate_switch_config.j2")

# ---------- Output directory ----------
builds_root = base_dir / "output_builds"
builds_root.mkdir(exist_ok=True)

# Permanent environment folders (ESV, PROD, etc.)
output_dir = builds_root / env_name.upper()
output_dir.mkdir(exist_ok=True)

print(f"\nOutput directory: {output_dir}")

# ---------- Render per device ----------
for device in device_data.get("devices", []):
    hostname = device.get("hostname", "UNKNOWN")
    print(f"Rendering {hostname}...")
    print(f"Loaded interfaces keys for {env_name}: {list(interfaces_data.keys())}")

    # mgmt object for mgmt_interface_block.j2
    mgmt_defaults = {
        "vrf": env_vars.get("mgmt_vrf", "management"),
        "description": "OOB Management",
    }

    # Include security ACL and DNS info in common_data
    common_data["security"] = env_vars.get("security", {})

    dns_servers = []
    if env_vars.get("dns_servers"):
        dns_servers = list(env_vars["dns_servers"])
    else:
        if env_vars.get("dns_primary"):
            dns_servers.append(env_vars["dns_primary"])
        if env_vars.get("dns_secondary"):
            dns_servers.append(env_vars["dns_secondary"])

    common_data["dns_servers"] = dns_servers
    common_data["dns_domain"] = env_vars.get("dns_domain")

    rendered = template.render(
        inventory_hostname=hostname,
        device=device,
        env_name=env_name,
        env=env_vars,           # explicit for includes
        interfaces=interfaces_data,
        mgmt=mgmt_defaults,
        common_data=common_data,
        now=datetime.now,       # if you ever want timestamps in templates
        **common_data,          # unpack common vars (system, radius, snmp, etc.)
    )

    outfile = output_dir / f"{hostname}.cfg"
    outfile.write_text(rendered, encoding="utf-8")
    print(f"Saved (replaced if existed): {outfile.name}")

print(f"\nAll configs generated successfully for {env_name.upper()} in {output_dir}")
