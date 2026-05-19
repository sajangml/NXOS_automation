# NXOS Automation

Prototype NX-OS configuration generator for a three-site spine-leaf-super-spine fabric.

The project uses synthetic values and demo addressing so it can be shared safely as a GitHub showcase.

## What This Generates

Running the generator creates NX-OS configuration files for:

- `DC1`
- `DC2`
- `DC3`

Each DC contains:

- 2 pods
- 2 super-spines per pod
- 4 spines per pod
- 8 leafs per pod
- LF07 and LF08 as border leafs

Generated configs are written to:

```text
output_builds/SPINELEAF/DC1/
output_builds/SPINELEAF/DC2/
output_builds/SPINELEAF/DC3/
```

The generator creates 84 NX-OS configs in total.

## Project Layout

```text
base_template/              Jinja2 templates used to render NX-OS configs
environments/spineleaf/     Topology, global services, and per-DC variables
output_builds/SPINELEAF/    Generated NX-OS configuration output
scripts/                    Config generation script
docs/                       Design and hardware artefacts
```

The design and hardware explanation is in:

```text
docs/Design Artefact.md
```

## Requirements

- Python 3.9 or newer
- Packages listed in `requirements.txt`

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Generate Configs

```powershell
python .\scripts\generate_all_configs.py spineleaf
```

The script reads:

```text
environments/spineleaf/topology.yaml
environments/spineleaf/env_vars.yaml
environments/spineleaf/vars_common_template.yaml
```

Then it renders all device configs under:

```text
output_builds/SPINELEAF/
```

## Change the Topology

Edit:

```text
environments/spineleaf/topology.yaml
```

This file controls:

- number of sites, pods, spines, super-spines, and leafs
- hardware platform metadata
- recommended interface speeds
- border leaf IDs
- server count per leaf

## Change Global Services

Edit:

```text
environments/spineleaf/env_vars.yaml
```

This file controls:

- timezone
- DNS
- NTP
- AAA/RADIUS
- SNMPv3
- syslog
- telemetry
- netflow
- smart licensing
- management ACLs
- per-DC management and loopback ranges

## Rebuild Workflow

After editing topology or variables, run:

```powershell
python .\scripts\generate_all_configs.py spineleaf
```

Review the generated configs in `output_builds/SPINELEAF/`, then commit the changed files.
