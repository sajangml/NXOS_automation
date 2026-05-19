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


def ip_to_system_id(ip: str) -> str:
    parts = ip.split("/")[-1] if "/" in ip else ip
    parts = parts.split(".")
    padded = "".join([f"{int(p):03d}" for p in parts])
    return f"{padded[0:4]}.{padded[4:8]}.{padded[8:12]}"


def get_p2p_link(cidr: str, link_index: int):
    network = ip_network(cidr, strict=False)
    subnets = list(network.subnets(new_prefix=31))
    if link_index < len(subnets):
        sub = subnets[link_index]
        return f"{sub.network_address}/31", f"{sub.network_address + 1}/31"
    raise ValueError(f"Link index {link_index} is out of bounds for pool {cidr}")

def build_topology(topology: dict, env_vars: dict | None = None, ip_data: dict | None = None, bgp_asns_data: dict | None = None):
    env_vars = env_vars or {}
    ip_data = ip_data or {}
    bgp_asns_data = bgp_asns_data or {}
    dc_allocations = ip_data.get("dc_allocations", {})
    dc_asns = bgp_asns_data.get("dc_asns", {})
    devices = []
    interfaces = {}
    super_spines_per_pod = int(topology.get("super_spines_per_pod", 2))
    spines_per_pod = int(topology.get("spines_per_pod", 4))
    leaves_per_pod = int(topology.get("leaves_per_pod", 8))
    servers_per_leaf = int(topology.get("servers_per_leaf", 10))
    hardware = topology.get("hardware", {})
    speeds = topology.get("speeds", {})

    for site in topology.get("sites", []):
        site_id = int(site["site_id"])
        site_name = site["name"].upper()
        site_override = dc_allocations.get(site_name.lower(), {})
        management_subnet = site_override.get("management", {}).get("fabric", "")
        loopbacks = site_override.get("loopbacks", {})
        p2p_scheme = site_override.get("p2p", {})
        site_devices = []
        xr_nodes = {}
        for xr_id in [1, 2]:
            name = f"{site_name}-XR{xr_id:02d}"
            xr_nodes[name] = {
                "hostname": name,
                "site": site_name,
                "site_id": site_id,
                "type": "xr",
                "role": "xr",
                "platform": "Cisco IOS-XR",
                "mgmt_ip": mgmt_ip(site_override.get("management", {}).get("xr", ""), xr_id),
                "loopback0": subnet_ip(loopbacks.get("xr", ""), xr_id),
                "router_id": subnet_ip(loopbacks.get("xr", ""), xr_id).split("/", 1)[0],
                "bgp_asn": bgp_asns_data.get("core_asn", 65000),
                "bgp_neighbors": [],
                "design_note": "Core XR routing node providing DCI transport.",
            }
            interfaces[name] = {"ethernet": []}

        pods_by_id = {int(pod["pod_id"]): pod for pod in site.get("pods", [])}
        super_spines_by_pod = {}

        for pod in site.get("pods", []):
            pod_id = int(pod["pod_id"])
            pod_name = pod["name"].lower()
            pod_code = f"P{pod_id}"
            pod_offset = (pod_id - 1) * 100
            
            # Retrieve the specific BGP ASN for this DC
            spine_asn = dc_asns.get(site_name.lower(), 65000)

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
                    "platform": hardware.get("super_spine", "Cisco Nexus 9364C-GX"),
                    "asic": "CloudScale GX",
                    "rack_role": "Network spine row",
                    "mgmt_ip": mgmt_ip(management_subnet, pod_offset + 10 + ss_id),
                    "mgmt_gw": mgmt_ip(management_subnet, 1).split("/", 1)[0],
                    "loopback0": subnet_ip(loopbacks.get("super_spine", f"10.{site_id}.{pod_id}.10/24"), pod_offset + ss_id),
                    "router_id": subnet_ip(loopbacks.get("super_spine", f"10.{site_id}.{pod_id}.10/24"), pod_offset + ss_id).split("/", 1)[0],
                    "isis_net": f"49.000{site_id}.{ip_to_system_id(subnet_ip(loopbacks.get('super_spine', f'10.{site_id}.{pod_id}.10/24'), pod_offset + ss_id).split('/')[0])}.00",
                    "bgp_asn": spine_asn,
                    "super_spine_id": ss_id,
                    "ss_global_id": ((pod_id - 1) * super_spines_per_pod) + ss_id,
                    "multicast_unique_rp": subnet_ip(loopbacks.get("multicast_rp", f"10.{site_id}.6.0/24"), ((pod_id - 1) * super_spines_per_pod) + ss_id).split("/")[0],
                    "stp_priority": 4096,
                    "design_note": "Super-spines connect to spines and peer to the other pod super-spines. They do not connect directly to XR/core.",
                    "evpn_rr_clients": [],
                    "evpn_rr_peers": [],
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
                    "platform": hardware.get("spine", "Cisco Nexus 9364C-GX"),
                    "asic": "CloudScale GX",
                    "rack_role": "End-of-row",
                    "mgmt_ip": mgmt_ip(management_subnet, pod_offset + 20 + spine_id),
                    "mgmt_gw": mgmt_ip(management_subnet, 1).split("/", 1)[0],
                    "loopback0": subnet_ip(loopbacks.get("spine", f"10.{site_id}.{pod_id}.20/24"), pod_offset + spine_id),
                    "router_id": subnet_ip(loopbacks.get("spine", f"10.{site_id}.{pod_id}.20/24"), pod_offset + spine_id).split("/", 1)[0],
                    "isis_net": f"49.000{site_id}.{ip_to_system_id(subnet_ip(loopbacks.get('spine', f'10.{site_id}.{pod_id}.20/24'), pod_offset + spine_id).split('/')[0])}.00",
                    "bgp_asn": spine_asn,
                    "spine_id": spine_id,
                    "stp_priority": 8192,
                    "design_note": "Spines connect down to all pod leaves and up to both pod super-spines.",
                    "evpn_rr_clients": [],
                    "evpn_rr_servers": [],
                }
                spines.append(spine)
                site_devices.append(spine)
                devices.append(spine)

            for leaf_id in range(1, leaves_per_pod + 1):
                name = f"{site_name}-{pod_code}-LF{leaf_id:02d}"
                is_border = leaf_id in [7, 8]
                leaf_asn = spine_asn # Using flat EVPN ASN model
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
                    "platform": hardware.get("border_leaf" if is_border else "leaf", "Cisco Nexus 93180YC-FX3"),
                    "asic": "CloudScale FX3",
                    "rack_role": "Dedicated border rack pair" if is_border else "Top-of-rack",
                    "border_gateway": is_border,
                    "mgmt_ip": mgmt_ip(management_subnet, pod_offset + 30 + leaf_id),
                    "mgmt_gw": mgmt_ip(management_subnet, 1).split("/", 1)[0],
                    "loopback0": subnet_ip(loopbacks.get("leaf", f"10.{site_id}.{pod_id}.30/24"), pod_offset + leaf_id),
                    "loopback1": f"10.{site_id}.{pod_id}.13{leaf_id}/32",
                    "router_id": subnet_ip(loopbacks.get("leaf", f"10.{site_id}.{pod_id}.30/24"), pod_offset + leaf_id).split("/", 1)[0],
                    "isis_net": f"49.000{site_id}.{ip_to_system_id(subnet_ip(loopbacks.get('leaf', f'10.{site_id}.{pod_id}.30/24'), pod_offset + leaf_id).split('/')[0])}.00",
                    "bgp_asn": leaf_asn,
                    "vtep_id": (site_id * 1000) + (pod_id * 100) + leaf_id,
                    "leaf_id": leaf_id,
                    "server_range": f"{site_name}-{pod_code}-SRV{first_server:03d}-{last_server:03d}",
                    "stp_priority": 24576,
                    "design_note": "Border gateway leaf: server-facing ports Eth1/1-10, fabric uplinks Eth1/49-52, XR/core uplinks Eth1/53-54." if is_border else "Server leaf: server-facing ports Eth1/1-10 and fabric uplinks Eth1/49-52.",
                    "evpn_rr_servers": [],
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
                        "speed": speeds.get("server_to_leaf", "25000"),
                        "mode": "routed",
                        "peer_name": f"{site_name}-{pod_code}-SRV{server_number:03d}",
                        "peer_port": "NIC1",
                        "no_shutdown": True,
                    })

                for spine in spines:
                    spine_id = int(spine["spine_id"])
                    link_index = ((int(leaf["leaf_id"]) - 1) * spines_per_pod) + spine_id
                    pool = p2p_scheme.get("leaf_to_spine", {}).get(f"pod{pod_id}", "172.16.1.0/24")
                    spine_ip, leaf_ip = get_p2p_link(pool, link_index)
                    leaf_port = f"Ethernet1/{48 + spine_id}"
                    spine_port = f"Ethernet1/{leaf['leaf_id']}"
                    leaf_eth.append({
                        "name": leaf_port,
                        "description": f"{leaf['hostname']} to {spine['hostname']} fabric uplink",
                        "speed": speeds.get("leaf_to_spine", "100000"),
                        "mode": "routed",
                        "peer_name": spine["hostname"],
                        "peer_port": spine_port,
                        "ip_address": leaf_ip,
                        "mtu": 9216,
                        "isis_underlay": True,
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
                    leaf["evpn_rr_servers"].append({
                        "ip": spine["loopback0"].split("/", 1)[0],
                        "remote_as": spine["bgp_asn"],
                        "description": f"EVPN_RR_TO_{spine['hostname']}",
                    })
                    spine["evpn_rr_clients"].append({
                        "ip": leaf["loopback0"].split("/", 1)[0],
                        "remote_as": leaf["bgp_asn"],
                        "description": f"EVPN_CLIENT_{leaf['hostname']}",
                    })

                if leaf["border_gateway"]:
                    border_index = ((pod_id - 1) * 2) + (int(leaf["leaf_id"]) - 7)
                    for xr_id in [1, 2]:
                        xr_name = f"{site_name}-XR{xr_id:02d}"
                        local_port = f"Ethernet1/{52 + xr_id}"
                        xr_port = f"HundredGigE0/0/0/{10 + border_index}"
                        pool = p2p_scheme.get("bgw_to_xr", "172.16.250.0/24")
                        local_ip, xr_ip = get_p2p_link(pool, (border_index * 2) + (xr_id - 1))
                        leaf_eth.append({
                            "name": local_port,
                            "description": f"TO_{xr_name}",
                            "speed": speeds.get("border_leaf_to_xr", "100000"),
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
                            "peer_asn": bgp_asns_data.get("core_asn", 65000),
                        })
                        interfaces[xr_name]["ethernet"].append({
                            "name": xr_port,
                            "description": f"TO_{leaf['hostname']}",
                            "ip_address": xr_ip,
                        })
                        xr_nodes[xr_name]["bgp_neighbors"].append({
                            "ip": local_ip.split("/")[0],
                            "remote_as": leaf["bgp_asn"],
                            "description": f"TO_{leaf['hostname']}",
                            "update_source": xr_port,
                        })

                interfaces[leaf["hostname"]] = {"ethernet": leaf_eth}
                
                # BGP neighbors list for Border Leaf to XR (removing underlay fabric P2P from BGP)
                leaf["bgp_neighbors"] = [
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
                        "speed": speeds.get("leaf_to_spine", "100000"),
                        "mode": "routed",
                        "peer_name": link["peer"],
                        "peer_port": link["peer_port"],
                        "ip_address": link["local_ip"],
                        "mtu": 9216,
                        "isis_underlay": True,
                        "no_shutdown": True,
                    })

                for ss in super_spines:
                    ss_id = int(ss["super_spine_id"])
                    link_index = 40 + ((int(spine["spine_id"]) - 1) * super_spines_per_pod) + ss_id
                    pool = p2p_scheme.get("spine_to_super_spine", {}).get(f"pod{pod_id}", "172.16.11.0/24")
                    ss_ip, spine_ip = get_p2p_link(pool, link_index)
                    spine_port = f"Ethernet1/{48 + ss_id}"
                    ss_port = f"Ethernet1/{spine['spine_id']}"
                    spine_eth.append({
                        "name": spine_port,
                        "description": f"{spine['hostname']} to {ss['hostname']} super-spine uplink",
                        "speed": speeds.get("spine_to_super_spine", "100000"),
                        "mode": "routed",
                        "peer_name": ss["hostname"],
                        "peer_port": ss_port,
                        "ip_address": spine_ip,
                        "mtu": 9216,
                        "isis_underlay": True,
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
                    spine["evpn_rr_servers"].append({
                        "ip": ss["loopback0"].split("/", 1)[0],
                        "remote_as": ss["bgp_asn"],
                        "description": f"EVPN_UPSTREAM_{ss['hostname']}",
                    })
                    ss["evpn_rr_clients"].append({
                        "ip": spine["loopback0"].split("/", 1)[0],
                        "remote_as": spine["bgp_asn"],
                        "description": f"EVPN_CLIENT_{spine['hostname']}",
                    })
                    interfaces.setdefault(ss["hostname"], {"ethernet": []})["ethernet"].append({
                        "name": ss_port,
                        "description": f"{ss['hostname']} to {spine['hostname']} spine downlink",
                        "speed": speeds.get("spine_to_super_spine", "100000"),
                        "mode": "routed",
                        "peer_name": spine["hostname"],
                        "peer_port": spine_port,
                        "ip_address": ss_ip,
                        "mtu": 9216,
                        "isis_underlay": True,
                        "no_shutdown": True,
                    })

                interfaces[spine["hostname"]] = {"ethernet": spine_eth}
                # Remove underlay P2P BGP peering for Spines
                spine["bgp_neighbors"] = []

        if 1 in super_spines_by_pod and 2 in super_spines_by_pod:
            pod1_ss = super_spines_by_pod[1]
            pod2_ss = super_spines_by_pod[2]
            link_number = 1
            for left in pod1_ss:
                for right in pod2_ss:
                    pool = p2p_scheme.get("pod_to_pod_super_spine", "172.16.200.0/24")
                    left_ip, right_ip = get_p2p_link(pool, link_number)
                    left_port = f"Ethernet1/{48 + int(right['super_spine_id'])}"
                    right_port = f"Ethernet1/{48 + int(left['super_spine_id'])}"
                    interfaces.setdefault(left["hostname"], {"ethernet": []})["ethernet"].append({
                        "name": left_port,
                        "description": f"{left['hostname']} pod-to-pod link to {right['hostname']}",
                        "speed": speeds.get("pod_to_pod_super_spine", "100000"),
                        "mode": "routed",
                        "peer_name": right["hostname"],
                        "peer_port": right_port,
                        "ip_address": left_ip,
                        "mtu": 9216,
                        "isis_underlay": True,
                        "no_shutdown": True,
                    })
                    interfaces.setdefault(right["hostname"], {"ethernet": []})["ethernet"].append({
                        "name": right_port,
                        "description": f"{right['hostname']} pod-to-pod link to {left['hostname']}",
                        "speed": speeds.get("pod_to_pod_super_spine", "100000"),
                        "mode": "routed",
                        "peer_name": left["hostname"],
                        "peer_port": left_port,
                        "ip_address": right_ip,
                        "mtu": 9216,
                        "isis_underlay": True,
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
                    left["evpn_rr_peers"].append({
                        "ip": right["loopback0"].split("/", 1)[0],
                        "remote_as": right["bgp_asn"],
                        "description": f"EVPN_REMOTE_POD_SS",
                    })
                    right["evpn_rr_peers"].append({
                        "ip": left["loopback0"].split("/", 1)[0],
                        "remote_as": left["bgp_asn"],
                        "description": f"EVPN_REMOTE_POD_SS",
                    })
                    link_number += 1

        site_super_spines = [d for d in site_devices if d.get("role") == "super_spine"]
        site_spines = [d for d in site_devices if d.get("role") == "spine"]
        site_leaves = [d for d in site_devices if d.get("role") in ["leaf", "border_leaf"]]

        site_multicast = site_override.get("multicast", {})
        anycast_rp_val = site_multicast.get("anycast_rp", f"10.{site_id}.6.254")
        multicast_group = site_multicast.get("group_range", "239.1.0.0/16")

        for ss in site_super_spines:
            ss["multicast"] = {
                "anycast_rp": anycast_rp_val,
                "group_range": multicast_group,
                "unique_rp": ss["multicast_unique_rp"],
                "anycast_rp_peers": [s["multicast_unique_rp"] for s in site_super_spines],
                "msdp_intra_peers": [s["multicast_unique_rp"] for s in site_super_spines if s["hostname"] != ss["hostname"]],
                "msdp_inter_peers": [],
                "is_inter_dc_speaker": ss["ss_global_id"] == 1,
            }
            if ss["ss_global_id"] == 1:
                for remote_site_id in [1, 2, 3]:
                    if remote_site_id != site_id:
                        ss["multicast"]["msdp_inter_peers"].append(f"10.{remote_site_id}.6.1")

        for sp in site_spines:
            sp["multicast"] = {
                "anycast_rp": anycast_rp_val,
                "group_range": multicast_group,
            }

        for lf in site_leaves:
            lf["multicast"] = {
                "anycast_rp": anycast_rp_val,
                "group_range": multicast_group,
            }

        for device in site_devices:
            if device["role"] == "super_spine":
                # Remove underlay BGP peering for super spines
                device["bgp_neighbors"] = []

        for xr in xr_nodes.values():
            site_devices.append(xr)
            devices.append(xr)

    for device in devices:
        for transient_key in ["fabric_links", "xr_links", "leaf_links", "super_spine_links", "spine_links", "pod_peer_links"]:
            device.pop(transient_key, None)

    dci_transit = ip_data.get("dci_transit", {})
    num_sites = len(topology.get("sites", []))
    for i in range(1, num_sites + 1):
        site_id = i
        next_site_id = (i % num_sites) + 1
        dci_pool = dci_transit.get(f"dc{site_id}_to_dc{next_site_id}", "")
        if not dci_pool:
            continue
        
        for xr_id in [1, 2]:
            local_xr = f"DC{site_id}-XR{xr_id:02d}"
            remote_xr = f"DC{next_site_id}-XR{xr_id:02d}"
            local_port = f"HundredGigE0/0/0/{next_site_id - 1}"
            remote_port = f"HundredGigE0/0/0/{site_id - 1}"
            local_ip, remote_ip = get_p2p_link(dci_pool, xr_id - 1)
            
            interfaces.setdefault(local_xr, {}).setdefault("ethernet", []).append({
                "name": local_port,
                "description": f"TO_{remote_xr}",
                "ip_address": local_ip,
                "mtu": 9216,
            })
            interfaces.setdefault(remote_xr, {}).setdefault("ethernet", []).append({
                "name": remote_port,
                "description": f"TO_{local_xr}",
                "ip_address": remote_ip,
                "mtu": 9216,
            })
            
            for dev in devices:
                if dev["hostname"] == local_xr:
                    dev["bgp_neighbors"].append({
                        "ip": remote_ip.split("/")[0],
                        "remote_as": bgp_asns_data.get("core_asn", 65000),
                        "description": f"TO_{remote_xr}",
                        "update_source": local_port,
                    })
                if dev["hostname"] == remote_xr:
                    dev["bgp_neighbors"].append({
                        "ip": local_ip.split("/")[0],
                        "remote_as": bgp_asns_data.get("core_asn", 65000),
                        "description": f"TO_{local_xr}",
                        "update_source": remote_port,
                    })

    return {"devices": devices}, interfaces


if len(sys.argv) < 2:
    print("Usage: python scripts/generate_all_configs.py <environment>")
    sys.exit(1)

env_name = sys.argv[1].lower()

base_dir = Path(__file__).resolve().parents[1]
env_path = base_dir / "environments" / env_name

env_vars = load_yaml(env_path / "env_vars.yaml")
ip_data = load_yaml(env_path / "ip_address.yaml")
bgp_asns_data = load_yaml(env_path / "bgp_asns.yaml")
topology = load_yaml(env_path / "topology.yaml")

if topology:
    device_data, generated_interfaces = build_topology(topology, env_vars, ip_data, bgp_asns_data)
else:
    device_data = load_yaml(env_path / "device_vars.yaml")
    generated_interfaces = {}

for device in device_data.get("devices", []):
    if not device.get("snmp_engine_id") and device.get("mgmt_ip"):
        device["snmp_engine_id"] = derive_snmp_engine_id(device["mgmt_ip"])

common_data = render_yaml_with_env(env_path / "vars_common_template.yaml", env_vars)
interfaces_data = load_yaml(env_path / "interfaces.yaml")
interfaces_data.update(generated_interfaces)

template_dir = base_dir / "base_template"
jinja_env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)
jinja_env.globals.update(env=env_vars)

template_nxos = jinja_env.get_template("generate_switch_config.j2")
template_xr = jinja_env.get_template("xr_config.j2")

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

    if device.get("role") == "xr":
        active_template = template_xr
    else:
        active_template = template_nxos

    rendered = active_template.render(
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
