# semantic_diff/parser.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple, Optional, Union


@dataclass
class InterfaceConfig:
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VlanConfig:
    vlan_id: str
    name: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedConfig:
    """
    High-level semantic model of an NX-OS config.
    Extend domains as needed.
    """
    metadata: Dict[str, Any] = field(default_factory=dict)
    aaa: List[str] = field(default_factory=list)
    qos: List[str] = field(default_factory=list)
    snmp: List[str] = field(default_factory=list)
    ntp: List[str] = field(default_factory=list)
    vlans: Dict[str, VlanConfig] = field(default_factory=dict)
    vrfs: Dict[str, List[str]] = field(default_factory=dict)
    interfaces: Dict[str, InterfaceConfig] = field(default_factory=dict)
    port_profiles: Dict[str, List[str]] = field(default_factory=dict)
    other_globals: List[str] = field(default_factory=list)


def _parse_key_value_from_subcommand(line: str) -> Tuple[str, Union[str, bool]]:
    """
    Given an indented config line like ' description foo bar'
    return (key, value) pairs suitable for interface attributes, etc.
    """
    l = line.strip()
    if not l:
        return ("", "")

    parts = l.split()
    key = parts[0]
    if len(parts) == 1:
        # commands like 'switchport' / 'shutdown'
        if key == "shutdown":
            return ("shutdown", True)
        if key == "no":
            # e.g. 'no shutdown' => handle separately in parser
            return ("no", True)
        return (key, True)

    if key == "no" and parts[1] == "shutdown":
        return ("shutdown", False)

    value = " ".join(parts[1:])
    return (key, value)


def parse_config_lines(lines: List[str]) -> ParsedConfig:
    """
    Convert normalized lines into a ParsedConfig with semantic domains.
    Very 'first-pass' but structured enough for meaningful diff.
    """
    cfg = ParsedConfig()
    strip = str.strip

    current_block_header: Optional[str] = None
    current_block_lines: List[str] = []

    def flush_block():
        nonlocal current_block_header, current_block_lines
        if current_block_header is None:
            return

        header = strip(current_block_header)
        body = current_block_lines

        # Dispatch by header
        if header.startswith("interface "):
            _handle_interface_block(cfg, header, body)
        elif header.startswith("vlan "):
            _handle_vlan_block(cfg, header, body)
        elif header.startswith("vrf context "):
            _handle_vrf_block(cfg, header, body)
        elif header.startswith("port-profile "):
            _handle_port_profile_block(cfg, header, body)
        else:
            # treat as generic global block
            cfg.other_globals.append(header)
            cfg.other_globals.extend(body)

        current_block_header = None
        current_block_lines = []

    for line in lines:
        # Top-level vs sub-command
        if not line.startswith(" "):  # new block or global command
            # flush previous block if any
            if current_block_header is not None:
                flush_block()

            # classify global lines or start of a block
            if line.startswith("hostname "):
                cfg.metadata["hostname"] = strip(line.split("hostname ", 1)[1])
            elif line.startswith("version "):
                cfg.metadata["version"] = strip(line.split("version ", 1)[1])
            elif line.startswith("aaa "):
                cfg.aaa.append(strip(line))
            elif line.startswith("radius-server ") or line.startswith("tacacs-server "):
                cfg.aaa.append(strip(line))
            elif line.startswith("username "):
                cfg.aaa.append(strip(line))
            elif line.startswith("snmp-server ") or line.startswith("no snmp-server "):
                cfg.snmp.append(strip(line))
            elif line.startswith("ntp "):
                cfg.ntp.append(strip(line))
            elif line.startswith("class-map") or line.startswith("policy-map") or line.startswith("system qos"):
                cfg.qos.append(strip(line))
            elif line.startswith("interface ") or line.startswith("vlan ") \
                    or line.startswith("vrf context ") or line.startswith("port-profile "):
                # start new block
                current_block_header = line
                current_block_lines = []
            else:
                # unknown/global
                cfg.other_globals.append(strip(line))
        else:
            # sub-command, belongs to current block
            if current_block_header is None:
                # orphan indented line; treat as other_global
                cfg.other_globals.append(strip(line))
            else:
                current_block_lines.append(line)

    # flush last block
    if current_block_header is not None:
        flush_block()

    return cfg


def _handle_interface_block(cfg: ParsedConfig, header: str, body: List[str]) -> None:
    _, name = header.split("interface", 1)
    name = name.strip()

    iface = InterfaceConfig(name=name, attributes={})

    for line in body:
        key, value = _parse_key_value_from_subcommand(line)
        if not key:
            continue

        # If key already present, you may want to listify.
        # For now, last one wins.
        iface.attributes[key] = value

    cfg.interfaces[name] = iface


def _handle_vlan_block(cfg: ParsedConfig, header: str, body: List[str]) -> None:

    header = header.strip()

    # Case 1: vlan configuration 320 -> treat as single "configuration-320"
    if header.startswith("vlan configuration"):
        _, _, vlan_id = header.split()
        vlan_id = f"configuration-{vlan_id}"

        vlan = VlanConfig(vlan_id=vlan_id)
        cfg.vlans[vlan_id] = vlan
        return

    # Case 2: vlan <id>,<id>,<range>...
    # Extract everything after "vlan"
    try:
        _, vlan_raw = header.split("vlan", 1)
    except ValueError:
        return

    vlan_raw = vlan_raw.strip()

    # VLAN list parsing: "1,10,20-30"
    vlan_items = vlan_raw.split(",")

    vlan_ids = []

    for item in vlan_items:
        item = item.strip()

        # Range e.g., 20-30
        if "-" in item:
            start, end = item.split("-")
            start = int(start)
            end = int(end)
            vlan_ids.extend(list(range(start, end + 1)))
        else:
            # Single VLAN
            if item.isdigit():
                vlan_ids.append(int(item))

    # Now create one VlanConfig per VLAN id
    for vid in vlan_ids:
        v = VlanConfig(vlan_id=str(vid))

        # Parse body normally
        for line in body:
            key, value = _parse_key_value_from_subcommand(line)
            if key == "name":
                v.name = str(value)
            elif key:
                v.attributes[key] = value

        cfg.vlans[str(vid)] = v



def _handle_vrf_block(cfg: ParsedConfig, header: str, body: List[str]) -> None:
    _, name = header.split("vrf context", 1)
    name = name.strip()
    cfg.vrfs[name] = [l.strip() for l in body]


def _handle_port_profile_block(cfg: ParsedConfig, header: str, body: List[str]) -> None:
    # header like: "port-profile type ethernet XXX" or "port-profile XXX"
    parts = header.split()
    if len(parts) >= 2 and parts[0] == "port-profile":
        profile_name = parts[-1]
    else:
        profile_name = header.strip()

    cfg.port_profiles[profile_name] = [l.strip() for l in body]
def parse_config(lines: List[str]) -> ParsedConfig:
    return parse_config_lines(lines)
