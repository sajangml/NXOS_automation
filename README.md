# NXOS Automation

Prototype NX-OS automation project for a 2-spine / 8-leaf data centre fabric.

All values are synthetic. The repository uses documentation-safe IP ranges for management and demo-only addressing for the underlay, so it can be shared as a client-facing GitHub showcase without exposing a real network.

## Fabric Topology

Spines:

- `SPN01` / `spine01`
- `SPN02` / `spine02`

Leaves:

- `LEF01` / `leaf01`
- `LEF02` / `leaf02`
- `LEF03` / `leaf03`
- `LEF04` / `leaf04`
- `LEF05` / `leaf05`
- `LEF06` / `leaf06`
- `LEF07` / `leaf07`
- `LEF08` / `leaf08`

## Port Allocation

| Spine | Port | Leaf | Leaf Port | Underlay /31 |
| --- | --- | --- | --- | --- |
| spine01 | Ethernet1/1 | leaf01 | Ethernet1/49 | 10.0.1.0/31 |
| spine01 | Ethernet1/2 | leaf02 | Ethernet1/49 | 10.0.2.0/31 |
| spine01 | Ethernet1/3 | leaf03 | Ethernet1/49 | 10.0.3.0/31 |
| spine01 | Ethernet1/4 | leaf04 | Ethernet1/49 | 10.0.4.0/31 |
| spine01 | Ethernet1/5 | leaf05 | Ethernet1/49 | 10.0.5.0/31 |
| spine01 | Ethernet1/6 | leaf06 | Ethernet1/49 | 10.0.6.0/31 |
| spine01 | Ethernet1/7 | leaf07 | Ethernet1/49 | 10.0.7.0/31 |
| spine01 | Ethernet1/8 | leaf08 | Ethernet1/49 | 10.0.8.0/31 |
| spine02 | Ethernet1/1 | leaf01 | Ethernet1/50 | 10.0.101.0/31 |
| spine02 | Ethernet1/2 | leaf02 | Ethernet1/50 | 10.0.102.0/31 |
| spine02 | Ethernet1/3 | leaf03 | Ethernet1/50 | 10.0.103.0/31 |
| spine02 | Ethernet1/4 | leaf04 | Ethernet1/50 | 10.0.104.0/31 |
| spine02 | Ethernet1/5 | leaf05 | Ethernet1/50 | 10.0.105.0/31 |
| spine02 | Ethernet1/6 | leaf06 | Ethernet1/50 | 10.0.106.0/31 |
| spine02 | Ethernet1/7 | leaf07 | Ethernet1/50 | 10.0.107.0/31 |
| spine02 | Ethernet1/8 | leaf08 | Ethernet1/50 | 10.0.108.0/31 |

## Project Layout

```text
base_template/              Jinja2 NX-OS templates
environments/spineleaf/     Source-of-truth YAML for the demo fabric
NXOS_AUTOMATION/            Inventory, helpers, collection, sanity, and diff modules
scripts/generate_all_configs.py
output_builds/SPINELEAF/    Generated NX-OS configs
```

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\scripts\generate_all_configs.py spineleaf
```

Generated configs are written to `output_builds/SPINELEAF/`.
