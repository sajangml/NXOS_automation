# semantic_diff/report.py

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any, Iterable, Optional

from .domain_compare import SemanticDiff, ObjectDelta
from .parser import ParsedConfig, VlanConfig, InterfaceConfig


# ---------------------------------------------------------
# Helper: domain ordering
# ---------------------------------------------------------

DOMAIN_ORDER = [
    "vlans",
    "interfaces",
    "vrfs",
    "port_profiles",
    "aaa",
    "qos",
    "snmp",
    "ntp",
]


def _group_deltas_by_change(diff: SemanticDiff) -> Dict[str, Dict[str, List[ObjectDelta]]]:
    grouped: Dict[str, Dict[str, List[ObjectDelta]]] = {
        "added": {},
        "removed": {},
        "modified": {},
    }
    for domain, deltas in diff.by_domain.items():
        for delta in deltas:
            grouped.setdefault(delta.change_type, {}).setdefault(domain, []).append(delta)
    return grouped


# ---------------------------------------------------------
# Public entry point
# ---------------------------------------------------------

def render_human_report(
    hostname: str,
    env: str,
    baseline_path: str,
    running_path: str,
    generated_at: datetime,
    diff: SemanticDiff,
    baseline_model: Optional[ParsedConfig] = None,
    running_model: Optional[ParsedConfig] = None,
) -> str:
    """
    Final human-readable report.

    Sections:
      1) Missing config from running (present in baseline)
      2) Extra config on running (not in baseline)
      3) Modified objects (same object, changed attributes)
    """
    lines: List[str] = []

    # Header
    lines.append("! ======================================================")
    lines.append("! NX-OS AUTOMATION - SEMANTIC CONFIG DIFF REPORT")
    lines.append(f"! Hostname: {hostname}")
    lines.append(f"! Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"! Environment: {env.upper()}")
    lines.append(f"! Baseline: {baseline_path}")
    lines.append(f"! Running : {running_path}")
    lines.append("! ======================================================")
    lines.append("")

    grouped = _group_deltas_by_change(diff)

    # Section 1: Missing config (present in baseline, missing on running)
    lines.append("==== [SECTION 1 — BASELINE-ONLY CONFIG (MISSING ON DEVICE RUNNING CONFIG)] ====")
    _render_missing(lines, grouped.get("removed", {}))

    # Section 2: Extra config (present on running, not in baseline)
    lines.append("")
    lines.append("==== [SECTION 2 — RUNNING-ONLY CONFIG (PRESENT ON DEVICE, NOT IN BASELINE)] ====")
    _render_extra(lines, grouped.get("added", {}))

    # Section 3: Modified objects
    lines.append("")
    lines.append("==== [SECTION 3 — SAME OBJECT, DIFFERENT VALUES (BASELINE VS RUNNING)] ====")
    _render_modified(lines, grouped.get("modified", {}))

    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------
# Section 1: Missing (REMOVED)
# ---------------------------------------------------------

def _render_missing(lines: List[str], removed_by_domain: Dict[str, List[ObjectDelta]]) -> None:
    if not removed_by_domain:
        lines.append("! No missing config relative to baseline.")
        return

    for domain in DOMAIN_ORDER:
        domain_deltas = removed_by_domain.get(domain, [])
        if not domain_deltas:
            continue

        lines.append("")
        lines.append(f"[{domain.upper()}]")

        if domain == "vlans":
            _render_missing_vlans(lines, domain_deltas)
        elif domain == "interfaces":
            _render_missing_interfaces(lines, domain_deltas)
        elif domain == "vrfs":
            _render_missing_vrfs(lines, domain_deltas)
        elif domain == "port_profiles":
            _render_missing_port_profiles(lines, domain_deltas)
        elif domain in ("aaa", "qos", "snmp", "ntp"):
            _render_missing_simple_lines(lines, domain_deltas)
        else:
            _render_generic_missing(lines, domain_deltas)


def _render_missing_vlans(lines: List[str], deltas: List[ObjectDelta]) -> None:
    _render_vlan_deltas(lines, deltas)


def _render_missing_interfaces(lines: List[str], deltas: List[ObjectDelta]) -> None:
    def sort_key(d: ObjectDelta):
        return d.object_id or ""

    for d in sorted(deltas, key=sort_key):
        if_name = d.object_id or "UNKNOWN"
        attrs = d.details.get("attributes", {})
        lines.extend(_nxos_interface_block_from_attrs(if_name, attrs))
        lines.append("")


def _render_missing_vrfs(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.object_id or ""):
        name = d.object_id or "UNKNOWN"
        vrf_lines: Iterable[str] = d.details.get("lines", [])
        lines.append(f"vrf context {name}")
        for l in vrf_lines:
            l = l.strip()
            if l:
                lines.append(f"  {l}")
        lines.append("")


def _render_missing_port_profiles(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.object_id or ""):
        name = d.object_id or "UNKNOWN"
        pp_lines: Iterable[str] = d.details.get("lines", [])
        lines.append(f"port-profile {name}")
        for l in pp_lines:
            l = l.strip()
            if l:
                lines.append(f"  {l}")
        lines.append("")


def _render_missing_simple_lines(lines: List[str], deltas: List[ObjectDelta]) -> None:
    # aaa/qos/snmp/ntp — these store the exact line already
    for d in sorted(deltas, key=lambda x: x.details.get("line", "")):
        line = d.details.get("line")
        if line:
            lines.append(line)


def _render_generic_missing(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in deltas:
        lines.append(f"! removed: {d}")


# ---------------------------------------------------------
# Section 2: Extra (ADDED)
# ---------------------------------------------------------

def _render_extra(lines: List[str], added_by_domain: Dict[str, List[ObjectDelta]]) -> None:
    if not added_by_domain:
        lines.append("! No extra config on running beyond baseline.")
        return

    for domain in DOMAIN_ORDER:
        domain_deltas = added_by_domain.get(domain, [])
        if not domain_deltas:
            continue

        lines.append("")
        lines.append(f"[{domain.upper()}]")

        if domain == "vlans":
            _render_extra_vlans(lines, domain_deltas)
        elif domain == "interfaces":
            _render_extra_interfaces(lines, domain_deltas)
        elif domain == "vrfs":
            _render_extra_vrfs(lines, domain_deltas)
        elif domain == "port_profiles":
            _render_extra_port_profiles(lines, domain_deltas)
        elif domain in ("aaa", "qos", "snmp", "ntp"):
            _render_extra_simple_lines(lines, domain_deltas)
        else:
            _render_generic_extra(lines, domain_deltas)


def _render_extra_vlans(lines: List[str], deltas: List[ObjectDelta]) -> None:
    _render_vlan_deltas(lines, deltas)


def _render_extra_interfaces(lines: List[str], deltas: List[ObjectDelta]) -> None:
    def sort_key(d: ObjectDelta):
        return d.object_id or ""

    for d in sorted(deltas, key=sort_key):
        if_name = d.object_id or "UNKNOWN"
        attrs = d.details.get("attributes", {})
        lines.extend(_nxos_interface_block_from_attrs(if_name, attrs))
        lines.append("")


def _render_extra_vrfs(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.object_id or ""):
        name = d.object_id or "UNKNOWN"
        vrf_lines: Iterable[str] = d.details.get("lines", [])
        lines.append(f"vrf context {name}")
        for l in vrf_lines:
            l = l.strip()
            if l:
                lines.append(f"  {l}")
        lines.append("")


def _render_extra_port_profiles(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.object_id or ""):
        name = d.object_id or "UNKNOWN"
        pp_lines: Iterable[str] = d.details.get("lines", [])
        lines.append(f"port-profile {name}")
        for l in pp_lines:
            l = l.strip()
            if l:
                lines.append(f"  {l}")
        lines.append("")


def _render_extra_simple_lines(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.details.get("line", "")):
        line = d.details.get("line")
        if line:
            lines.append(line)


def _render_generic_extra(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in deltas:
        lines.append(f"! added: {d}")


# ---------------------------------------------------------
# Section 3: Modified
# ---------------------------------------------------------

def _render_modified(lines: List[str], modified_by_domain: Dict[str, List[ObjectDelta]]) -> None:
    if not modified_by_domain:
        lines.append("! No modified objects relative to baseline.")
        return

    for domain in DOMAIN_ORDER:
        domain_deltas = modified_by_domain.get(domain, [])
        if not domain_deltas:
            continue

        lines.append("")
        lines.append(f"[{domain.upper()}]")

        if domain == "vlans":
            _render_modified_vlans(lines, domain_deltas)
        elif domain == "interfaces":
            _render_modified_interfaces(lines, domain_deltas)
        elif domain == "vrfs":
            _render_modified_vrfs(lines, domain_deltas)
        elif domain == "port_profiles":
            _render_modified_port_profiles(lines, domain_deltas)
        else:
            _render_generic_modified(lines, domain_deltas)


def _render_modified_vlans(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.object_id or ""):
        vid = d.object_id or "UNKNOWN"
        lines.append(f"vlan {vid}")
        details = d.details

        name_change = details.get("name")
        if isinstance(name_change, dict):
            lines.append(
                f"  name: {name_change.get('before')} -> {name_change.get('after')}"
            )

        attr_changes = details.get("attributes", {})
        for k in sorted(attr_changes.keys()):
            change = attr_changes[k]
            lines.append(
                f"  {k}: {change.get('before')} -> {change.get('after')}"
            )
        lines.append("")


def _render_modified_interfaces(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.object_id or ""):
        if_name = d.object_id or "UNKNOWN"
        lines.append(f"interface {if_name}")
        details = d.details
        attr_changes = details.get("attributes", {})

        for k in sorted(attr_changes.keys()):
            change = attr_changes[k]
            lines.append(
                f"  {k}: {change.get('before')} -> {change.get('after')}"
            )
        lines.append("")


def _render_modified_vrfs(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.object_id or ""):
        name = d.object_id or "UNKNOWN"
        details = d.details
        added = details.get("added", [])
        removed = details.get("removed", [])
        lines.append(f"vrf context {name}")
        if added:
            lines.append("  ! Added lines:")
            for l in added:
                lines.append(f"    + {l}")
        if removed:
            lines.append("  ! Removed lines:")
            for l in removed:
                lines.append(f"    - {l}")
        lines.append("")


def _render_modified_port_profiles(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in sorted(deltas, key=lambda x: x.object_id or ""):
        name = d.object_id or "UNKNOWN"
        details = d.details
        added = details.get("added", [])
        removed = details.get("removed", [])
        lines.append(f"port-profile {name}")
        if added:
            lines.append("  ! Added lines:")
            for l in added:
                lines.append(f"    + {l}")
        if removed:
            lines.append("  ! Removed lines:")
            for l in removed:
                lines.append(f"    - {l}")
        lines.append("")


def _render_generic_modified(lines: List[str], deltas: List[ObjectDelta]) -> None:
    for d in deltas:
        lines.append(f"! modified: {d}")


# ---------------------------------------------------------
# NX-OS reconstruction helpers
# ---------------------------------------------------------

def _nxos_vlan_block_from_dict(vinfo: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    vlan_id = str(vinfo.get("vlan_id", "")).strip()
    name = vinfo.get("name")
    attrs: Dict[str, Any] = vinfo.get("attributes", {}) or {}

    # Special-case "configuration-<id>" pattern
    if vlan_id.startswith("configuration-"):
        _, _, raw_id = vlan_id.partition("configuration-")
        header = f"vlan configuration {raw_id}"
    else:
        header = f"vlan {vlan_id}"

    lines.append(header)

    if name:
        lines.append(f"  name {name}")

    for k, v in sorted(attrs.items()):
        if v is None or v == "":
            continue
        lines.append(f"  {k} {v}")

    return lines


def _render_vlan_deltas(lines: List[str], deltas: List[ObjectDelta]) -> None:
    """
    Render VLAN deltas while compacting "simple" numeric VLANs (no attrs/name)
    into NX-OS range syntax to reduce noisy per-VLAN output.
    """
    simple_ids: List[int] = []
    complex_vlans: List[Dict[str, Any]] = []

    for d in deltas:
        vinfo = d.details.get("vlan", {}) or {}
        vid = str(vinfo.get("vlan_id", "")).strip()
        name = vinfo.get("name")
        attrs = vinfo.get("attributes", {}) or {}

        if vid.isdigit() and not name and not attrs:
            simple_ids.append(int(vid))
        else:
            complex_vlans.append(vinfo)

    if simple_ids:
        lines.append(f"vlan {_compress_int_ranges(sorted(set(simple_ids)))}")
        lines.append("")

    def sort_key(vinfo: Dict[str, Any]) -> Any:
        vid = str(vinfo.get("vlan_id", "")).strip()
        return (0, int(vid)) if vid.isdigit() else (1, vid)

    for vinfo in sorted(complex_vlans, key=sort_key):
        lines.extend(_nxos_vlan_block_from_dict(vinfo))
        lines.append("")


def _compress_int_ranges(ids: List[int]) -> str:
    if not ids:
        return ""

    ranges: List[str] = []
    start = prev = ids[0]
    for current in ids[1:]:
        if current == prev + 1:
            prev = current
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = current
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


def _nxos_interface_block_from_attrs(if_name: str, attrs: Dict[str, Any]) -> List[str]:
    lines: List[str] = [f"interface {if_name}"]

    for key, value in sorted(attrs.items()):
        if value is None:
            continue

        # Shutdown is boolean-ish
        if key == "shutdown":
            if isinstance(value, bool):
                lines.append("  shutdown" if value else "  no shutdown")
            else:
                val_str = str(value).lower()
                if val_str in ("true", "yes", "on"):
                    lines.append("  shutdown")
                elif val_str in ("false", "no", "off"):
                    lines.append("  no shutdown")
                else:
                    lines.append(f"  shutdown {value}")
            continue

        if key == "description":
            lines.append(f"  description {value}")
            continue

        if key == "mtu":
            lines.append(f"  mtu {value}")
            continue

        if key == "service-policy":
            lines.append(f"  service-policy {value}")
            continue

        if key == "switchport":
            lines.append(f"  switchport {value}")
            continue

        if key == "ip":
            lines.append(f"  ip {value}")
            continue

        if key == "vrf":
            lines.append(f"  vrf {value}")
            continue

        if key == "channel-group":
            lines.append(f"  channel-group {value}")
            continue

        if key == "inherit":
            value_str = str(value)
            if value_str.startswith("port-profile "):
                lines.append(f"  inherit {value_str}")
            else:
                lines.append(f"  inherit port-profile {value_str}")
            continue

        if key == "authentication":
            lines.append(f"  authentication {value}")
            continue

        if key == "hsrp":
            lines.append(f"  hsrp {value}")
            continue

        if key == "bfd":
            lines.append(f"  bfd {value}")
            continue

        if key == "no":
            lines.append(f"  no {value}")
            continue

        # Fallback generic
        lines.append(f"  {key} {value}")

    return lines
