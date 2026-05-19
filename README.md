# NXOS Automation

Prototype NX-OS automation project for a multi-site spine-leaf data centre fabric.

All values are synthetic. The repository uses documentation-safe management IP ranges and demo-only underlay addressing, so it can be shared as a client-facing GitHub showcase without exposing a real network.

## Fabric Topology

The demo fabric contains three data centres:

- `DC1`
- `DC2`
- `DC3`

Each data centre contains two pods:

- `pod1`
- `pod2`

Each pod contains:

- 2 spines
- 8 leaves

Total generated devices:

- 6 pods
- 12 spines
- 48 leaves
- 60 NX-OS configs

Device naming follows this pattern:

```text
dc<site>-pod<pod>-spine<id>
dc<site>-pod<pod>-leaf<id>
```

Examples:

```text
dc1-pod1-spine01  fabric_id: DC1-P1-SPN01
dc1-pod1-leaf01   fabric_id: DC1-P1-LEF01
dc3-pod2-spine02  fabric_id: DC3-P2-SPN02
dc3-pod2-leaf08   fabric_id: DC3-P2-LEF08
```

## Port Allocation

The same port model is repeated inside every pod.

| Spine | Spine Port | Leaf | Leaf Port |
| --- | --- | --- | --- |
| spine01 | Ethernet1/1 | leaf01 | Ethernet1/49 |
| spine01 | Ethernet1/2 | leaf02 | Ethernet1/49 |
| spine01 | Ethernet1/3 | leaf03 | Ethernet1/49 |
| spine01 | Ethernet1/4 | leaf04 | Ethernet1/49 |
| spine01 | Ethernet1/5 | leaf05 | Ethernet1/49 |
| spine01 | Ethernet1/6 | leaf06 | Ethernet1/49 |
| spine01 | Ethernet1/7 | leaf07 | Ethernet1/49 |
| spine01 | Ethernet1/8 | leaf08 | Ethernet1/49 |
| spine02 | Ethernet1/1 | leaf01 | Ethernet1/50 |
| spine02 | Ethernet1/2 | leaf02 | Ethernet1/50 |
| spine02 | Ethernet1/3 | leaf03 | Ethernet1/50 |
| spine02 | Ethernet1/4 | leaf04 | Ethernet1/50 |
| spine02 | Ethernet1/5 | leaf05 | Ethernet1/50 |
| spine02 | Ethernet1/6 | leaf06 | Ethernet1/50 |
| spine02 | Ethernet1/7 | leaf07 | Ethernet1/50 |
| spine02 | Ethernet1/8 | leaf08 | Ethernet1/50 |

The generator allocates unique underlay `/31` point-to-point networks per site, pod, spine, and leaf.

## Project Layout

```text
base_template/                    Jinja2 NX-OS templates
environments/spineleaf/topology.yaml
environments/spineleaf/           Source-of-truth YAML for the demo fabric
NXOS_AUTOMATION/                  Inventory, helpers, collection, sanity, and diff modules
scripts/generate_all_configs.py
output_builds/SPINELEAF/          Generated NX-OS configs
```

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\scripts\generate_all_configs.py spineleaf
```

Generated configs are written to `output_builds/SPINELEAF/`. The same run also refreshes `NXOS_AUTOMATION/inventory/hosts.yaml` from `topology.yaml`.
