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
        return yaml.safe_load(f) or {}


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
    return ":".join(padded[i:i + 2] for i in range(0, len(padded), 2))


def mgmt_ip(subnet: str, offset: int) -> str:
    network = ip_network(subnet, strict=False)
    return f"{network.network_address + offset}/{network.prefixlen}"


def subnet_ip(subnet: str, offset: int, prefixlen=32) -> str:
    network = ip_network(subnet, strict=False)
    return f"{network.network_address + offset}/{prefixlen}"


def p2p(site_id: int, pod_id: int, link_index: int):
    base = link_index * 2
    return f"172.{16 + site_id}.{pod_id}.{base}/31", f"172.{16 + site_id}.{pod_id}.{base + 1}/31"


def interpod_p2p(site_id: int, link_index: int):
    base = link_index * 2
    return f"172.{16 + site_id}.200.{base}/31", f"172.{16 + site_id}.200.{base + 1}/31"


def build_topology(topology: dict, env_vars: dict | None = None):
    env_vars = env_vars or {}
    dc_overrides = env_vars.get("dc_overrides", {})
    devices = []
    interfaces = {}
    super_spines_per_pod = int(topology.get("super_spines_per_pod", 2))
    spines_per_pod = int(topology.get("spines_per_pod", 4))
    leaves_per_pod = int(topology.get("leaves_per_pod", 8))
    servers_per_leaf = int(topology.get("servers_per_leaf", 10))

    for site in topology.get("sites", []):
        site_id = int(site["site_id"])
        site_name = site["name"].upper()
        site_override = dc_overrides.get(site_name.lower(), {})
        management_subnet = site_override.get("management_subnet", site["management_subnet"])
        loopbacks = site_override.get("loopbacks", {})
        site_devices = []
        pods_by_id = {int(pod["pod_id"]): pod for pod in site.get("pods", [])}
        super_spines_by_pod = {}

        for pod in site.get("pods", []):
            pod_id = int(pod["pod_id"])
            pod_name = pod["name"].lower()
            pod_code = f"P{pod_id}"
            pod_offset = (pod_id - 1) * 100
            spine_asn = 65000 + (site_id * 10) + pod_id

            super_spines = []
            spines = []
            leaves = []

            for ss_id in range(1, super_spines_per_pod + 1):
                name = f"{site_name}-{pod_code}-SS{ss_id:02d}"
                ss = {
                    "hostname": name,
                    "fabric_id": name,
                    "site": site_name,
                    "site_id": site_id,
                    "pod": pod_name,
                    "pod_id": pod_id,
                    "type": "super_spine",
                    "role": "super_spine",
                    "mgmt_ip": mgmt_ip(management_subnet, pod_offset + 10 + ss_id),
                    "mgmt_gw": mgmt_ip(management_subnet, 1).split("/", 1)[0],
                    "loopback0": subnet_ip(loopbacks.get("super_spine", f"10.{site_id}.{pod_id}.10/24"), pod_offset + ss_id),
                    "router_id": subnet_ip(loopbacks.get("super_spine", f"10.{site_id}.{pod_id}.10/24"), pod_offset + ss_id).split("/", 1)[0],
                    "bgp_asn": spine_asn,
                    "super_spine_id": ss_id,
                    "stp_priority": 4096,
                    "design_note": "Super-spines connect to spines and peer to the other pod super-spines. They do not connect directly to XR/core.",
                }
                super_spines.append(ss)
                site_devices.append(ss)
                devices.append(ss)
            super_spines_by_pod[pod_id] = super_spines

            for spine_id in range(1, spines_per_pod + 1):
                name = f"{site_name}-{pod_code}-SP{spine_id:02d}"
                spine = {
                    "hostname": name,
                    "fabric_id": name,
                    "site": site_name,
                    "site_id": site_id,
                    "pod": pod_name,
                    "pod_id": pod_id,
                    "type": "spine",
                    "role": "spine",
                    "mgmt_ip": mgmt_ip(management_subnet, pod_offset + 20 + spine_id),
                    "mgmt_gw": mgmt_ip(management_subnet, 1).split("/", 1)[0],
                    "loopback0": subnet_ip(loopbacks.get("spine", f"10.{site_id}.{pod_id}.20/24"), pod_offset + spine_id),
                    "router_id": subnet_ip(loopbacks.get("spine", f"10.{site_id}.{pod_id}.20/24"), pod_offset + spine_id).split("/", 1)[0],
                    "bgp_asn": spine_asn,
                    "spine_id": spine_id,
                    "stp_priority": 8192,
                    "design_note": "Spines connect down to all pod leaves and up to both pod super-spines.",
                }
                spines.append(spine)
                site_devices.append(spine)
                devices.append(spine)

            for leaf_id in range(1, leaves_per_pod + 1):
                name = f"{site_name}-{pod_code}-LF{leaf_id:02d}"
                is_border = leaf_id in [7, 8]
                leaf_asn = 65100 + (site_id * 100) + (pod_id * 10) + leaf_id
                first_server = ((pod_id - 1) * leaves_per_pod * servers_per_leaf) + ((leaf_id - 1) * servers_per_leaf) + 1
                last_server = first_server + servers_per_leaf - 1
                leaf = {
                    "hostname": name,
                    "fabric_id": name,
                    "site": site_name,
                    "site_id": site_id,
                    "pod": pod_name,
                    "pod_id": pod_id,
                    "type": "leaf",
                    "role": "border_leaf" if is_border else "leaf",
                    "border_gateway": is_border,
                    "mgmt_ip": mgmt_ip(management_subnet, pod_offset + 30 + leaf_id),
                    "mgmt_gw": mgmt_ip(management_subnet, 1).split("/", 1)[0],
                    "loopback0": subnet_ip(loopbacks.get("leaf", f"10.{site_id}.{pod_id}.30/24"), pod_offset + leaf_id),
                    "loopback1": f"10.{site_id}.{pod_id}.13{leaf_id}/32",
                    "router_id": subnet_ip(loopbacks.get("leaf", f"10.{site_id}.{pod_id}.30/24"), pod_offset + leaf_id).split("/", 1)[0],
                    "bgp_asn": leaf_asn,
                    "vtep_id": (site_id * 1000) + (pod_id * 100) + leaf_id,
                    "leaf_id": leaf_id,
                    "server_range": f"{site_name}-{pod_code}-SRV{first_server:03d}-{last_server:03d}",
                    "stp_priority": 24576,
                    "design_note": "Border gateway leaf: server-facing ports Eth1/1-10, fabric uplinks Eth1/49-52, XR/core uplinks Eth1/53-54." if is_border else "Server leaf: server-facing ports Eth1/1-10 and fabric uplinks Eth1/49-52.",
                }
                leaves.append(leaf)
                site_devices.append(leaf)
                devices.append(leaf)

            for leaf in leaves:
                leaf_eth = []
                for server_port in range(1, servers_per_leaf + 1):
                    server_number = ((pod_id - 1) * leaves_per_pod * servers_per_leaf) + ((leaf["leaf_id"] - 1) * servers_per_leaf) + server_port
                    leaf_eth.append({
                        "name": f"Ethernet1/{server_port}",
                        "description": f"{leaf['hostname']} to {site_name}-{pod_code}-SRV{server_number:03d} NIC1",
                        "mode": "access",
                        "access_vlan": 100 + int(leaf["leaf_id"]),
                        "peer_name": f"{site_name}-{pod_code}-SRV{server_number:03d}",
                        "peer_port": "NIC1",
                        "no_shutdown": True,
                    })

                for spine in spines:
                    spine_id = int(spine["spine_id"])
                    link_index = ((int(leaf["leaf_id"]) - 1) * spines_per_pod) + spine_id
                    spine_ip, leaf_ip = p2p(site_id, pod_id, link_index)
                    leaf_port = f"Ethernet1/{48 + spine_id}"
                    spine_port = f"Ethernet1/{leaf['leaf_id']}"
                    leaf_eth.append({
                        "name": leaf_port,
                        "description": f"{leaf['hostname']} to {spine['hostname']} fabric uplink",
                        "mode": "routed",
                        "peer_name": spine["hostname"],
                        "peer_port": spine_port,
                        "ip_address": leaf_ip,
                        "mtu": 9216,
                        "no_shutdown": True,
                    })
                    leaf.setdefault("fabric_links", {})[spine_id] = {
                        "peer": spine["hostname"],
                        "local_port": leaf_port,
                        "peer_port": spine_port,
                        "local_ip": leaf_ip,
                        "peer_ip": spine_ip,
                        "peer_asn": spine_asn,
                    }
                    spine.setdefault("leaf_links", []).append({
                        "peer": leaf["hostname"],
                        "local_port": spine_port,
                        "peer_port": leaf_port,
                        "local_ip": spine_ip,
                        "peer_ip": leaf_ip,
                        "peer_asn": leaf["bgp_asn"],
                    })

                if leaf["border_gateway"]:
                    border_index = ((pod_id - 1) * 2) + (int(leaf["leaf_id"]) - 7)
                    for xr_id in [1, 2]:
                        xr_name = f"{site_name}-XR{xr_id:02d}"
                        local_port = f"Ethernet1/{52 + xr_id}"
                        xr_port = f"Hu0/0/0/{10 + border_index}"
                        local_ip, xr_ip = p2p(site_id, 250 + pod_id, (border_index * 2) + xr_id)
                        leaf_eth.append({
                            "name": local_port,
                            "description": f"{leaf['hostname']} border/core uplink to {xr_name} {xr_port}",
                            "mode": "routed",
                            "peer_name": xr_name,
                            "peer_port": xr_port,
                            "ip_address": local_ip,
                            "mtu": 9216,
                            "no_shutdown": True,
                        })
                        leaf.setdefault("xr_links", []).append({
                            "peer": xr_name,
                            "local_port": local_port,
                            "peer_port": xr_port,
                            "local_ip": local_ip,
                            "peer_ip": xr_ip,
                            "peer_asn": 65200 + site_id,
                        })

                interfaces[leaf["hostname"]] = {"ethernet": leaf_eth}
                leaf["bgp_neighbors"] = [
                    {
                        "ip": link["peer_ip"].split("/", 1)[0],
                        "remote_as": link["peer_asn"],
                        "description": link["peer"],
                        "update_source": link["local_port"],
                    }
                    for link in leaf.get("fabric_links", {}).values()
                ] + [
                    {
                        "ip": link["peer_ip"].split("/", 1)[0],
                        "remote_as": link["peer_asn"],
                        "description": link["peer"],
                        "update_source": link["local_port"],
                    }
                    for link in leaf.get("xr_links", [])
                ]

            for spine in spines:
                spine_eth = []
                for link in spine.get("leaf_links", []):
                    spine_eth.append({
                        "name": link["local_port"],
                        "description": f"{spine['hostname']} to {link['peer']} fabric downlink",
                        "mode": "routed",
                        "peer_name": link["peer"],
                        "peer_port": link["peer_port"],
                        "ip_address": link["local_ip"],
                        "mtu": 9216,
                        "no_shutdown": True,
                    })

                for ss in super_spines:
                    ss_id = int(ss["super_spine_id"])
                    link_index = 40 + ((int(spine["spine_id"]) - 1) * super_spines_per_pod) + ss_id
                    ss_ip, spine_ip = p2p(site_id, pod_id, link_index)
                    spine_port = f"Ethernet1/{48 + ss_id}"
                    ss_port = f"Ethernet1/{spine['spine_id']}"
                    spine_eth.append({
                        "name": spine_port,
                        "description": f"{spine['hostname']} to {ss['hostname']} super-spine uplink",
                        "mode": "routed",
                        "peer_name": ss["hostname"],
                        "peer_port": ss_port,
                        "ip_address": spine_ip,
                        "mtu": 9216,
                        "no_shutdown": True,
                    })
                    spine.setdefault("super_spine_links", []).append({
                        "peer": ss["hostname"],
                        "local_port": spine_port,
                        "peer_port": ss_port,
                        "local_ip": spine_ip,
                        "peer_ip": ss_ip,
                        "peer_asn": spine_asn,
                    })
                    ss.setdefault("spine_links", []).append({
                        "peer": spine["hostname"],
                        "local_port": ss_port,
                        "peer_port": spine_port,
                        "local_ip": ss_ip,
                        "peer_ip": spine_ip,
                        "peer_asn": spine["bgp_asn"],
                    })
                    interfaces.setdefault(ss["hostname"], {"ethernet": []})["ethernet"].append({
                        "name": ss_port,
                        "description": f"{ss['hostname']} to {spine['hostname']} spine downlink",
                        "mode": "routed",
                        "peer_name": spine["hostname"],
                        "peer_port": spine_port,
                        "ip_address": ss_ip,
                        "mtu": 9216,
                        "no_shutdown": True,
                    })

                interfaces[spine["hostname"]] = {"ethernet": spine_eth}
                spine["bgp_neighbors"] = [
                    {
                        "ip": link["peer_ip"].split("/", 1)[0],
                        "remote_as": link["peer_asn"],
                        "description": link["peer"],
                        "update_source": link["local_port"],
                    }
                    for link in spine.get("leaf_links", []) + spine.get("super_spine_links", [])
                ]

        if 1 in super_spines_by_pod and 2 in super_spines_by_pod:
            pod1_ss = super_spines_by_pod[1]
            pod2_ss = super_spines_by_pod[2]
            link_number = 1
            for left in pod1_ss:
                for right in pod2_ss:
                    left_ip, right_ip = interpod_p2p(site_id, link_number)
                    left_port = f"Ethernet1/{48 + int(right['super_spine_id'])}"
                    right_port = f"Ethernet1/{48 + int(left['super_spine_id'])}"
                    interfaces.setdefault(left["hostname"], {"ethernet": []})["ethernet"].append({
                        "name": left_port,
                        "description": f"{left['hostname']} pod-to-pod link to {right['hostname']}",
                        "mode": "routed",
                        "peer_name": right["hostname"],
                        "peer_port": right_port,
                        "ip_address": left_ip,
                        "mtu": 9216,
                        "no_shutdown": True,
                    })
                    interfaces.setdefault(right["hostname"], {"ethernet": []})["ethernet"].append({
                        "name": right_port,
                        "description": f"{right['hostname']} pod-to-pod link to {left['hostname']}",
                        "mode": "routed",
                        "peer_name": left["hostname"],
                        "peer_port": left_port,
                        "ip_address": right_ip,
                        "mtu": 9216,
                        "no_shutdown": True,
                    })
                    left.setdefault("pod_peer_links", []).append({
                        "peer": right["hostname"],
                        "local_port": left_port,
                        "peer_ip": right_ip,
                        "peer_asn": right["bgp_asn"],
                    })
                    right.setdefault("pod_peer_links", []).append({
                        "peer": left["hostname"],
                        "local_port": right_port,
                        "peer_ip": left_ip,
                        "peer_asn": left["bgp_asn"],
                    })
                    link_number += 1

        for device in site_devices:
            if device["role"] == "super_spine":
                links = device.get("spine_links", []) + device.get("pod_peer_links", [])
                device["bgp_neighbors"] = [
                    {
                        "ip": link["peer_ip"].split("/", 1)[0],
                        "remote_as": link["peer_asn"],
                        "description": link["peer"],
                        "update_source": link["local_port"],
                    }
                    for link in links
                ]

    for device in devices:
        for transient_key in ["fabric_links", "xr_links", "leaf_links", "super_spine_links", "spine_links", "pod_peer_links"]:
            device.pop(transient_key, None)

    return {"devices": devices}, interfaces


def write_inventory_hosts(path: Path, devices: list[dict], env_name: str):
    hosts = {}
    for device in devices:
        group = device["role"]
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
                "border_gateway": device.get("border_gateway", False),
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
    device_data, generated_interfaces = build_topology(topology, env_vars)
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

output_dir = base_dir / "output_builds" / env_name.upper()
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
