# semantic_diff/domain_compare.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from .parser import ParsedConfig, InterfaceConfig, VlanConfig


@dataclass
class ObjectDelta:
    object_type: str          # e.g. "interface", "vlan", "vrf", "aaa"
    object_id: Optional[str]  # e.g. "Ethernet1/16" or "411" or None for global sets
    change_type: str          # "added", "removed", "modified"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticDiff:
    """
    Collection of ObjectDelta grouped by domain.
    """
    by_domain: Dict[str, List[ObjectDelta]] = field(default_factory=dict)

    def add(self, domain: str, delta: ObjectDelta) -> None:
        self.by_domain.setdefault(domain, []).append(delta)


def compare_configs(baseline: ParsedConfig, running: ParsedConfig) -> SemanticDiff:
    diff = SemanticDiff()

    _compare_simple_list_domain(diff, "aaa", baseline.aaa, running.aaa, object_type="aaa")
    _compare_simple_list_domain(diff, "qos", baseline.qos, running.qos, object_type="qos")
    _compare_simple_list_domain(diff, "snmp", baseline.snmp, running.snmp, object_type="snmp")
    _compare_simple_list_domain(diff, "ntp", baseline.ntp, running.ntp, object_type="ntp")

    _compare_vlans(diff, baseline.vlans, running.vlans)
    _compare_interfaces(diff, baseline.interfaces, running.interfaces)
    _compare_vrfs(diff, baseline.vrfs, running.vrfs)
    _compare_port_profiles(diff, baseline.port_profiles, running.port_profiles)

    # You can add 'other_globals' comparison if you care.
    return diff


def _diff_attributes(
    base_attrs: Dict[str, Any],
    run_attrs: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Return key-level before/after changes between two attribute dicts.
    """
    base_keys = set(base_attrs)
    run_keys = set(run_attrs)

    attr_changes: Dict[str, Dict[str, Any]] = {}
    for key in run_keys - base_keys:
        attr_changes[key] = {"before": None, "after": run_attrs[key]}
    for key in base_keys - run_keys:
        attr_changes[key] = {"before": base_attrs[key], "after": None}
    for key in base_keys & run_keys:
        if base_attrs[key] != run_attrs[key]:
            attr_changes[key] = {"before": base_attrs[key], "after": run_attrs[key]}
    return attr_changes


def _compare_simple_list_domain(
    diff: SemanticDiff,
    domain: str,
    base_list: List[str],
    run_list: List[str],
    object_type: str,
) -> None:
    base_set = set(base_list)
    run_set = set(run_list)

    for added in sorted(run_set - base_set):
        diff.add(domain, ObjectDelta(object_type=object_type, object_id=None,
                                     change_type="added", details={"line": added}))

    for removed in sorted(base_set - run_set):
        diff.add(domain, ObjectDelta(object_type=object_type, object_id=None,
                                     change_type="removed", details={"line": removed}))


def _compare_vlans(
    diff: SemanticDiff,
    base: Dict[str, VlanConfig],
    run: Dict[str, VlanConfig],
) -> None:
    base_ids = set(base)
    run_ids = set(run)

    # ---------------------------
    # Added VLANs
    # ---------------------------
    for v in sorted(run_ids - base_ids, key=str):
        diff.add("vlans", ObjectDelta(
            object_type="vlan",
            object_id=v,
            change_type="added",
            details={"vlan": _vlan_to_dict(run[v])},
        ))

    # ---------------------------
    # Removed VLANs
    # ---------------------------
    for v in sorted(base_ids - run_ids, key=str):
        diff.add("vlans", ObjectDelta(
            object_type="vlan",
            object_id=v,
            change_type="removed",
            details={"vlan": _vlan_to_dict(base[v])},
        ))

    # ---------------------------
    # Modified VLANs
    # ---------------------------
    for v in sorted(base_ids & run_ids, key=str):
        base_v = base[v]
        run_v = run[v]
        changes: Dict[str, Any] = {}

        # VLAN Name Modified
        if (base_v.name or "") != (run_v.name or ""):
            changes["name"] = {"before": base_v.name, "after": run_v.name}

        attr_changes = _diff_attributes(base_v.attributes, run_v.attributes)
        if attr_changes:
            changes["attributes"] = attr_changes

        if changes:
            diff.add("vlans", ObjectDelta(
                object_type="vlan",
                object_id=v,
                change_type="modified",
                details=changes,
            ))


def _vlan_to_dict(v: VlanConfig) -> Dict[str, Any]:
    return {
        "vlan_id": v.vlan_id,
        "name": v.name,
        "attributes": dict(sorted(v.attributes.items())),
    }


def _compare_interfaces(
    diff: SemanticDiff,
    base: Dict[str, InterfaceConfig],
    run: Dict[str, InterfaceConfig],
) -> None:
    base_names = set(base)
    run_names = set(run)

    for name in sorted(run_names - base_names):
        diff.add("interfaces", ObjectDelta(
            object_type="interface",
            object_id=name,
            change_type="added",
            details={"attributes": dict(sorted(run[name].attributes.items()))},
        ))

    for name in sorted(base_names - run_names):
        diff.add("interfaces", ObjectDelta(
            object_type="interface",
            object_id=name,
            change_type="removed",
            details={"attributes": dict(sorted(base[name].attributes.items()))},
        ))

    for name in sorted(base_names & run_names):
        base_i = base[name]
        run_i = run[name]
        changes: Dict[str, Any] = {}
        attr_changes = _diff_attributes(base_i.attributes, run_i.attributes)

        if attr_changes:
            changes["attributes"] = attr_changes

        if changes:
            diff.add("interfaces", ObjectDelta(
                object_type="interface",
                object_id=name,
                change_type="modified",
                details=changes,
            ))


def _compare_vrfs(
    diff: SemanticDiff,
    base: Dict[str, List[str]],
    run: Dict[str, List[str]],
) -> None:
    _compare_named_line_blocks(diff, "vrfs", "vrf", base, run, strip_lines=True)


def _compare_port_profiles(
    diff: SemanticDiff,
    base: Dict[str, List[str]],
    run: Dict[str, List[str]],
) -> None:
    _compare_named_line_blocks(diff, "port_profiles", "port-profile", base, run, strip_lines=False)


def _compare_named_line_blocks(
    diff: SemanticDiff,
    domain: str,
    object_type: str,
    base: Dict[str, List[str]],
    run: Dict[str, List[str]],
    strip_lines: bool,
) -> None:
    """
    Generic comparator for domains represented as name -> list[str].
    """
    base_names = set(base)
    run_names = set(run)
    add_delta = diff.add

    for name in sorted(run_names - base_names):
        add_delta(
            domain,
            ObjectDelta(
                object_type=object_type,
                object_id=name,
                change_type="added",
                details={"lines": sorted(run[name])},
            ),
        )

    for name in sorted(base_names - run_names):
        add_delta(
            domain,
            ObjectDelta(
                object_type=object_type,
                object_id=name,
                change_type="removed",
                details={"lines": sorted(base[name])},
            ),
        )

    for name in sorted(base_names & run_names):
        base_lines = [line.strip() for line in base[name]] if strip_lines else base[name]
        run_lines = [line.strip() for line in run[name]] if strip_lines else run[name]

        base_set = set(base_lines)
        run_set = set(run_lines)

        added = sorted(run_set - base_set)
        removed = sorted(base_set - run_set)
        if added or removed:
            add_delta(
                domain,
                ObjectDelta(
                    object_type=object_type,
                    object_id=name,
                    change_type="modified",
                    details={"added": added, "removed": removed},
                ),
            )
