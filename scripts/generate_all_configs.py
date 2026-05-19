import sys
from ipaddress import ip_network
from pathlib import Path
from datetime import datetime

import yaml
from jinja2 import Environment, FileSystemLoader


def load_yaml(path: Path):
    if not path.exists():
        print(f"Missing YAML file: {path}")
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def render_yaml_with_env(path: Path, env_vars: dict):
    if not path.exists():
        print(f"Missing template YAML: {path}")
        return {}
    raw = path.read_text(encoding="utf-8")
    rendered_text = Environment().from_string(raw).render(env=env_vars)
    return yaml.safe_load(rendered_text) or {}


def derive_snmp_engine_id(mgmt_ip: str) -> str:
    ip_only = str(mgmt_ip).split("/", 1)[0].strip()
    engine_seed = ip_only.replace(".", "A")
    padded = (engine_seed + ("F" * 24))[:24]
    octets = [padded[i:i + 2] for i in range(0, len(padded), 2)]
    return ":".join(octets)


def mgmt_ip(subnet: str, offset: int) -> str:
    network = ip_network(subnet, strict=False)
    return f"{network.network_address + offset}/{network.prefixlen}"


def host_prefix(site: dict, pod: dict) -> str:
    return f"{site['name'].lower()}-{pod['name'].lower()}"


def build_topology(topology: dict):
    devices = []
    interfaces = {}
    spines_per_pod = int(topology.get("spines_per_pod", 2))
    leaves_per_pod = int(topology.get("leaves_per_pod", 8))

    for site in topology.get("sites", []):
        site_id = int(site["site_id"])
        site_name = site["name"].upper()
        for pod in site.get("pods", []):
            pod_id = int(pod["pod_id"])
            pod_name = pod["name"].lower()
            prefix = host_prefix(site, pod)
            pod_offset = (pod_id - 1) * 30
            spine_asn = 65000 + site_id

            leaves = []
            for leaf_id in range(1, leaves_per_pod + 1):
                leaf_name = f"{prefix}-leaf{leaf_id:02d}"
                leaf_asn = 65100 + (site_id * 100) + (pod_id * 10) + leaf_id
                leaf = {
                    "hostname": leaf_name,
                    "fabric_id": f"{site_name}-P{pod_id}-LEF{leaf_id:02d}",
                    "site": site_name,
                    "site_id": site_id,
                    "pod": pod_name,
                    "pod_id": pod_id,
                    "type": "leaf",
                    "role": "leaf",
                    "mgmt_ip": mgmt_ip(site["management_subnet"], pod_offset + 20 + leaf_id),
                    "mgmt_gw": mgmt_ip(site["management_subnet"], 1).split("/", 1)[0],
                    "loopback0": f"10.{site_id}.{10 + pod_id}.{leaf_id}/32",
                    "loopback1": f"10.{site_id}.{110 + pod_id}.{leaf_id}/32",
                    "router_id": f"10.{site_id}.{10 + pod_id}.{leaf_id}",
                    "bgp_asn": leaf_asn,
                    "vtep_id": (site_id * 1000) + (pod_id * 100) + leaf_id,
                    "leaf_id": leaf_id,
                    "stp_priority": 24576,
                }
                leaves.append(leaf)
                devices.append(leaf)

            for spine_id in range(1, spines_per_pod + 1):
                spine_name = f"{prefix}-spine{spine_id:02d}"
                spine = {
                    "hostname": spine_name,
                    "fabric_id": f"{site_name}-P{pod_id}-SPN{spine_id:02d}",
                    "site": site_name,
                    "site_id": site_id,
                    "pod": pod_name,
                    "pod_id": pod_id,
                    "type": "spine",
                    "role": "spine",
                    "mgmt_ip": mgmt_ip(site["management_subnet"], pod_offset + 10 + spine_id),
                    "mgmt_gw": mgmt_ip(site["management_subnet"], 1).split("/", 1)[0],
                    "loopback0": f"10.{site_id}.{pod_id}.{10 + spine_id}/32",
                    "router_id": f"10.{site_id}.{pod_id}.{10 + spine_id}",
                    "bgp_asn": spine_asn,
                    "spine_id": spine_id,
                    "stp_priority": 4096 if spine_id == 1 else 8192,
                }
                devices.append(spine)

                spine_eth = []
                for leaf in leaves:
                    leaf_id = int(leaf["leaf_id"])
                    third_octet = (pod_id * 10 + leaf_id) if spine_id == 1 else (100 + pod_id * 10 + leaf_id)
                    spine_ip = f"10.{site_id}.{third_octet}.0/31"
                    leaf_ip = f"10.{site_id}.{third_octet}.1/31"
                    leaf_port = "Ethernet1/49" if spine_id == 1 else "Ethernet1/50"
                    spine_eth.append({
                        "name": f"Ethernet1/{leaf_id}",
                        "description": f"{spine_name} to {leaf['hostname']} fabric uplink",
                        "mode": "routed",
                        "peer_name": leaf["hostname"],
                        "peer_port": leaf_port,
                        "ip_address": spine_ip,
                        "mtu": 9216,
                        "no_shutdown": True,
                    })
                    leaf.setdefault("fabric_links", {})[spine_id] = {
                        "spine": spine_name,
                        "leaf_port": leaf_port,
                        "spine_port": f"Ethernet1/{leaf_id}",
                        "leaf_ip": leaf_ip,
                        "spine_ip": spine_ip,
                    }
                interfaces[spine_name] = {"ethernet": spine_eth}

            for leaf in leaves:
                leaf_eth = []
                for spine_id in range(1, spines_per_pod + 1):
                    link = leaf["fabric_links"][spine_id]
                    leaf_eth.append({
                        "name": link["leaf_port"],
                        "description": f"{leaf['hostname']} to {link['spine']} fabric uplink",
                        "mode": "routed",
                        "peer_name": link["spine"],
                        "peer_port": link["spine_port"],
                        "ip_address": link["leaf_ip"],
                        "mtu": 9216,
                        "no_shutdown": True,
                    })
                interfaces[leaf["hostname"]] = {"ethernet": leaf_eth}

                leaf["bgp_neighbors"] = [
                    {
                        "ip": leaf["fabric_links"][spine_id]["spine_ip"].split("/", 1)[0],
                        "remote_as": spine_asn,
                        "description": leaf["fabric_links"][spine_id]["spine"],
                        "update_source": leaf["fabric_links"][spine_id]["leaf_port"],
                    }
                    for spine_id in range(1, spines_per_pod + 1)
                ]

            for spine in [d for d in devices if d.get("site") == site_name and d.get("pod") == pod_name and d.get("role") == "spine"]:
                spine["bgp_neighbors"] = [
                    {
                        "ip": leaf["fabric_links"][int(spine["spine_id"])]["leaf_ip"].split("/", 1)[0],
                        "remote_as": leaf["bgp_asn"],
                        "description": leaf["hostname"],
                        "update_source": leaf["fabric_links"][int(spine["spine_id"])]["spine_port"],
                    }
                    for leaf in leaves
                ]

    for device in devices:
        device.pop("fabric_links", None)

    return {"devices": devices}, interfaces


def write_inventory_hosts(path: Path, devices: list[dict], env_name: str):
    hosts = {}
    for device in devices:
        group = "spine" if device["role"] == "spine" else "leaf"
        hosts[device["hostname"]] = {
            "hostname": str(device["mgmt_ip"]).split("/", 1)[0],
            "platform": "nxos",
            "groups": [group],
            "data": {
                "env": env_name,
                "role": device["role"],
                "site": device["site"],
                "pod": device["pod"],
                "fabric_id": device["fabric_id"],
            },
        }
    path.write_text(yaml.safe_dump(hosts, sort_keys=False), encoding="utf-8")


if len(sys.argv) < 2:
    print("Usage: python scripts/generate_all_configs.py <environment>")
    sys.exit(1)

env_name = sys.argv[1].lower()

base_dir = Path(__file__).resolve().parents[1]
env_path = base_dir / "environments" / env_name

env_vars = load_yaml(env_path / "env_vars.yaml")
topology = load_yaml(env_path / "topology.yaml")

if topology:
    device_data, generated_interfaces = build_topology(topology)
else:
    device_data = load_yaml(env_path / "device_vars.yaml")
    generated_interfaces = {}

for device in device_data.get("devices", []):
    if not device.get("snmp_engine_id") and device.get("mgmt_ip"):
        device["snmp_engine_id"] = derive_snmp_engine_id(device["mgmt_ip"])

common_data = render_yaml_with_env(env_path / "vars_common_template.yaml", env_vars)
interfaces_data = load_yaml(env_path / "interfaces.yaml")
interfaces_data.update(generated_interfaces)

write_inventory_hosts(
    base_dir / "NXOS_AUTOMATION" / "inventory" / "hosts.yaml",
    device_data.get("devices", []),
    env_name,
)

template_dir = base_dir / "base_template"
jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)
jinja_env.globals.update(env=env_vars)

template = jinja_env.get_template("generate_switch_config.j2")

builds_root = base_dir / "output_builds"
output_dir = builds_root / env_name.upper()
output_dir.mkdir(parents=True, exist_ok=True)

for old_config in output_dir.rglob("*.cfg"):
    old_config.unlink()

print(f"\nOutput directory: {output_dir}")

for device in device_data.get("devices", []):
    hostname = device.get("hostname", "UNKNOWN")
    print(f"Rendering {hostname}...")

    common_data["security"] = env_vars.get("security", {})
    common_data["dns_servers"] = list(env_vars.get("dns_servers", []))
    common_data["dns_domain"] = env_vars.get("dns_domain")

    rendered = template.render(
        inventory_hostname=hostname,
        device=device,
        env_name=env_name,
        env=env_vars,
        interfaces=interfaces_data,
        mgmt={"vrf": env_vars.get("mgmt_vrf", "management"), "description": "OOB Management"},
        common_data=common_data,
        now=datetime.now,
        **common_data,
    )

    site_output_dir = output_dir / device.get("site", "UNASSIGNED").upper()
    site_output_dir.mkdir(parents=True, exist_ok=True)
    outfile = site_output_dir / f"{hostname}.cfg"
    outfile.write_text(rendered, encoding="utf-8")
    print(f"Saved: {device.get('site', 'UNASSIGNED').upper()}\\{outfile.name}")

print(f"\nAll configs generated successfully for {env_name.upper()} in {output_dir}")
