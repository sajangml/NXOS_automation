# NXOS Automation

Prototype NX-OS automation project for a multi-site data centre fabric with a super-spine, spine, and leaf hierarchy.

All values are synthetic. The repository uses documentation-safe management IP ranges and demo-only underlay addressing, so it can be shared as a client-facing GitHub showcase without exposing a real network.

## Physical Design Summary

The model supports three data centres: `DC1`, `DC2`, and `DC3`.

Each data centre has two independent fabric pods. Each pod has its own super-spine layer, spine layer, and leaf layer.

The normal server leafs connect upward to all four spines in the same pod. The spines then connect upward to both super-spines. Leaf 7 and Leaf 8 in each pod act as border gateway leafs, so they provide the external handoff from the fabric to the Cisco XR core/DCI routers.

Traffic flow is:

```text
Server
  |
Leaf
  |
Spine
  |
Super-Spine
  |
Border Leaf 7 / Leaf 8
  |
Cisco XR Core / DCI Router
  |
DC2 / DC3
```

Corrected rule:

```text
Super-spines do not connect directly to XR.
Border Leaf 7 and Leaf 8 connect to XR/core.
```

## Per-DC Device Count

| Layer           | Devices |
| --------------- | ------: |
| Pods            |       2 |
| Super-Spines    |       4 |
| Spines          |       8 |
| Leafs           |      16 |
| Border Leafs    |       4 |
| Servers         |     160 |
| XR/Core Routers |       2 |

## DC1 Server-to-Leaf

| Pod    | Leaf        | Leaf Ports   | Servers           |
| ------ | ----------- | ------------ | ----------------- |
| DC1-P1 | DC1-P1-LF01 | Eth1/1-1/10  | DC1-P1-SRV001-010 |
| DC1-P1 | DC1-P1-LF02 | Eth1/1-1/10  | DC1-P1-SRV011-020 |
| DC1-P1 | DC1-P1-LF03 | Eth1/1-1/10  | DC1-P1-SRV021-030 |
| DC1-P1 | DC1-P1-LF04 | Eth1/1-1/10  | DC1-P1-SRV031-040 |
| DC1-P1 | DC1-P1-LF05 | Eth1/1-1/10  | DC1-P1-SRV041-050 |
| DC1-P1 | DC1-P1-LF06 | Eth1/1-1/10  | DC1-P1-SRV051-060 |
| DC1-P1 | DC1-P1-LF07 | Eth1/1-1/10  | DC1-P1-SRV061-070 |
| DC1-P1 | DC1-P1-LF08 | Eth1/1-1/10  | DC1-P1-SRV071-080 |
| DC1-P2 | DC1-P2-LF01 | Eth1/1-1/10  | DC1-P2-SRV081-090 |
| DC1-P2 | DC1-P2-LF02 | Eth1/1-1/10  | DC1-P2-SRV091-100 |
| DC1-P2 | DC1-P2-LF03 | Eth1/1-1/10  | DC1-P2-SRV101-110 |
| DC1-P2 | DC1-P2-LF04 | Eth1/1-1/10  | DC1-P2-SRV111-120 |
| DC1-P2 | DC1-P2-LF05 | Eth1/1-1/10  | DC1-P2-SRV121-130 |
| DC1-P2 | DC1-P2-LF06 | Eth1/1-1/10  | DC1-P2-SRV131-140 |
| DC1-P2 | DC1-P2-LF07 | Eth1/1-1/10  | DC1-P2-SRV141-150 |
| DC1-P2 | DC1-P2-LF08 | Eth1/1-1/10  | DC1-P2-SRV151-160 |

## DC2 Server-to-Leaf

| Pod    | Leaf        | Leaf Ports   | Servers           |
| ------ | ----------- | ------------ | ----------------- |
| DC2-P1 | DC2-P1-LF01 | Eth1/1-1/10  | DC2-P1-SRV001-010 |
| DC2-P1 | DC2-P1-LF02 | Eth1/1-1/10  | DC2-P1-SRV011-020 |
| DC2-P1 | DC2-P1-LF03 | Eth1/1-1/10  | DC2-P1-SRV021-030 |
| DC2-P1 | DC2-P1-LF04 | Eth1/1-1/10  | DC2-P1-SRV031-040 |
| DC2-P1 | DC2-P1-LF05 | Eth1/1-1/10  | DC2-P1-SRV041-050 |
| DC2-P1 | DC2-P1-LF06 | Eth1/1-1/10  | DC2-P1-SRV051-060 |
| DC2-P1 | DC2-P1-LF07 | Eth1/1-1/10  | DC2-P1-SRV061-070 |
| DC2-P1 | DC2-P1-LF08 | Eth1/1-1/10  | DC2-P1-SRV071-080 |
| DC2-P2 | DC2-P2-LF01 | Eth1/1-1/10  | DC2-P2-SRV081-090 |
| DC2-P2 | DC2-P2-LF02 | Eth1/1-1/10  | DC2-P2-SRV091-100 |
| DC2-P2 | DC2-P2-LF03 | Eth1/1-1/10  | DC2-P2-SRV101-110 |
| DC2-P2 | DC2-P2-LF04 | Eth1/1-1/10  | DC2-P2-SRV111-120 |
| DC2-P2 | DC2-P2-LF05 | Eth1/1-1/10  | DC2-P2-SRV121-130 |
| DC2-P2 | DC2-P2-LF06 | Eth1/1-1/10  | DC2-P2-SRV131-140 |
| DC2-P2 | DC2-P2-LF07 | Eth1/1-1/10  | DC2-P2-SRV141-150 |
| DC2-P2 | DC2-P2-LF08 | Eth1/1-1/10  | DC2-P2-SRV151-160 |

## DC3 Server-to-Leaf

| Pod    | Leaf        | Leaf Ports   | Servers           |
| ------ | ----------- | ------------ | ----------------- |
| DC3-P1 | DC3-P1-LF01 | Eth1/1-1/10  | DC3-P1-SRV001-010 |
| DC3-P1 | DC3-P1-LF02 | Eth1/1-1/10  | DC3-P1-SRV011-020 |
| DC3-P1 | DC3-P1-LF03 | Eth1/1-1/10  | DC3-P1-SRV021-030 |
| DC3-P1 | DC3-P1-LF04 | Eth1/1-1/10  | DC3-P1-SRV031-040 |
| DC3-P1 | DC3-P1-LF05 | Eth1/1-1/10  | DC3-P1-SRV041-050 |
| DC3-P1 | DC3-P1-LF06 | Eth1/1-1/10  | DC3-P1-SRV051-060 |
| DC3-P1 | DC3-P1-LF07 | Eth1/1-1/10  | DC3-P1-SRV061-070 |
| DC3-P1 | DC3-P1-LF08 | Eth1/1-1/10  | DC3-P1-SRV071-080 |
| DC3-P2 | DC3-P2-LF01 | Eth1/1-1/10  | DC3-P2-SRV081-090 |
| DC3-P2 | DC3-P2-LF02 | Eth1/1-1/10  | DC3-P2-SRV091-100 |
| DC3-P2 | DC3-P2-LF03 | Eth1/1-1/10  | DC3-P2-SRV101-110 |
| DC3-P2 | DC3-P2-LF04 | Eth1/1-1/10  | DC3-P2-SRV111-120 |
| DC3-P2 | DC3-P2-LF05 | Eth1/1-1/10  | DC3-P2-SRV121-130 |
| DC3-P2 | DC3-P2-LF06 | Eth1/1-1/10  | DC3-P2-SRV131-140 |
| DC3-P2 | DC3-P2-LF07 | Eth1/1-1/10  | DC3-P2-SRV141-150 |
| DC3-P2 | DC3-P2-LF08 | Eth1/1-1/10  | DC3-P2-SRV151-160 |

## Leaf-to-Spine Port Mapping

Same for DC1, DC2, and DC3 in both pods.

| Leaf Port | Destination |
| --------- | ----------- |
| Eth1/49   | SP01        |
| Eth1/50   | SP02        |
| Eth1/51   | SP03        |
| Eth1/52   | SP04        |

Spine-side mapping:

| Leaf | SP01 Port | SP02 Port | SP03 Port | SP04 Port |
| ---- | --------- | --------- | --------- | --------- |
| LF01 | Eth1/1    | Eth1/1    | Eth1/1    | Eth1/1    |
| LF02 | Eth1/2    | Eth1/2    | Eth1/2    | Eth1/2    |
| LF03 | Eth1/3    | Eth1/3    | Eth1/3    | Eth1/3    |
| LF04 | Eth1/4    | Eth1/4    | Eth1/4    | Eth1/4    |
| LF05 | Eth1/5    | Eth1/5    | Eth1/5    | Eth1/5    |
| LF06 | Eth1/6    | Eth1/6    | Eth1/6    | Eth1/6    |
| LF07 | Eth1/7    | Eth1/7    | Eth1/7    | Eth1/7    |
| LF08 | Eth1/8    | Eth1/8    | Eth1/8    | Eth1/8    |

## Spine-to-Super-Spine Port Mapping

Same for DC1, DC2, and DC3 in both pods.

| Spine | Spine Port | Super-Spine | Super-Spine Port |
| ----- | ---------- | ----------- | ---------------- |
| SP01  | Eth1/49    | SS01        | Eth1/1           |
| SP01  | Eth1/50    | SS02        | Eth1/1           |
| SP02  | Eth1/49    | SS01        | Eth1/2           |
| SP02  | Eth1/50    | SS02        | Eth1/2           |
| SP03  | Eth1/49    | SS01        | Eth1/3           |
| SP03  | Eth1/50    | SS02        | Eth1/3           |
| SP04  | Eth1/49    | SS01        | Eth1/4           |
| SP04  | Eth1/50    | SS02        | Eth1/4           |

## DC1 Pod-to-Pod Super-Spine

| Source      | Port    | Destination | Port    |
| ----------- | ------- | ----------- | ------- |
| DC1-P1-SS01 | Eth1/49 | DC1-P2-SS01 | Eth1/49 |
| DC1-P1-SS01 | Eth1/50 | DC1-P2-SS02 | Eth1/49 |
| DC1-P1-SS02 | Eth1/49 | DC1-P2-SS01 | Eth1/50 |
| DC1-P1-SS02 | Eth1/50 | DC1-P2-SS02 | Eth1/50 |

## DC2 Pod-to-Pod Super-Spine

| Source      | Port    | Destination | Port    |
| ----------- | ------- | ----------- | ------- |
| DC2-P1-SS01 | Eth1/49 | DC2-P2-SS01 | Eth1/49 |
| DC2-P1-SS01 | Eth1/50 | DC2-P2-SS02 | Eth1/49 |
| DC2-P1-SS02 | Eth1/49 | DC2-P2-SS01 | Eth1/50 |
| DC2-P1-SS02 | Eth1/50 | DC2-P2-SS02 | Eth1/50 |

## DC3 Pod-to-Pod Super-Spine

| Source      | Port    | Destination | Port    |
| ----------- | ------- | ----------- | ------- |
| DC3-P1-SS01 | Eth1/49 | DC3-P2-SS01 | Eth1/49 |
| DC3-P1-SS01 | Eth1/50 | DC3-P2-SS02 | Eth1/49 |
| DC3-P1-SS02 | Eth1/49 | DC3-P2-SS01 | Eth1/50 |
| DC3-P1-SS02 | Eth1/50 | DC3-P2-SS02 | Eth1/50 |

## DC1 Border Leafs to XR/Core

| Border Leaf | Port    | XR Router | XR Port    |
| ----------- | ------- | --------- | ---------- |
| DC1-P1-LF07 | Eth1/53 | DC1-XR01  | Hu0/0/0/10 |
| DC1-P1-LF07 | Eth1/54 | DC1-XR02  | Hu0/0/0/10 |
| DC1-P1-LF08 | Eth1/53 | DC1-XR01  | Hu0/0/0/11 |
| DC1-P1-LF08 | Eth1/54 | DC1-XR02  | Hu0/0/0/11 |
| DC1-P2-LF07 | Eth1/53 | DC1-XR01  | Hu0/0/0/12 |
| DC1-P2-LF07 | Eth1/54 | DC1-XR02  | Hu0/0/0/12 |
| DC1-P2-LF08 | Eth1/53 | DC1-XR01  | Hu0/0/0/13 |
| DC1-P2-LF08 | Eth1/54 | DC1-XR02  | Hu0/0/0/13 |

## DC2 Border Leafs to XR/Core

| Border Leaf | Port    | XR Router | XR Port    |
| ----------- | ------- | --------- | ---------- |
| DC2-P1-LF07 | Eth1/53 | DC2-XR01  | Hu0/0/0/10 |
| DC2-P1-LF07 | Eth1/54 | DC2-XR02  | Hu0/0/0/10 |
| DC2-P1-LF08 | Eth1/53 | DC2-XR01  | Hu0/0/0/11 |
| DC2-P1-LF08 | Eth1/54 | DC2-XR02  | Hu0/0/0/11 |
| DC2-P2-LF07 | Eth1/53 | DC2-XR01  | Hu0/0/0/12 |
| DC2-P2-LF07 | Eth1/54 | DC2-XR02  | Hu0/0/0/12 |
| DC2-P2-LF08 | Eth1/53 | DC2-XR01  | Hu0/0/0/13 |
| DC2-P2-LF08 | Eth1/54 | DC2-XR02  | Hu0/0/0/13 |

## DC3 Border Leafs to XR/Core

| Border Leaf | Port    | XR Router | XR Port    |
| ----------- | ------- | --------- | ---------- |
| DC3-P1-LF07 | Eth1/53 | DC3-XR01  | Hu0/0/0/10 |
| DC3-P1-LF07 | Eth1/54 | DC3-XR02  | Hu0/0/0/10 |
| DC3-P1-LF08 | Eth1/53 | DC3-XR01  | Hu0/0/0/11 |
| DC3-P1-LF08 | Eth1/54 | DC3-XR02  | Hu0/0/0/11 |
| DC3-P2-LF07 | Eth1/53 | DC3-XR01  | Hu0/0/0/12 |
| DC3-P2-LF07 | Eth1/54 | DC3-XR02  | Hu0/0/0/12 |
| DC3-P2-LF08 | Eth1/53 | DC3-XR01  | Hu0/0/0/13 |
| DC3-P2-LF08 | Eth1/54 | DC3-XR02  | Hu0/0/0/13 |

## Inter-DC XR Port Mapping

| Source Router | Source Port | Destination Router | Destination Port |
| ------------- | ----------- | ------------------ | ---------------- |
| DC1-XR01      | Hu0/0/0/0   | DC2-XR01           | Hu0/0/0/0        |
| DC1-XR02      | Hu0/0/0/0   | DC2-XR02           | Hu0/0/0/0        |
| DC2-XR01      | Hu0/0/0/1   | DC3-XR01           | Hu0/0/0/1        |
| DC2-XR02      | Hu0/0/0/1   | DC3-XR02           | Hu0/0/0/1        |
| DC3-XR01      | Hu0/0/0/2   | DC1-XR01           | Hu0/0/0/1        |
| DC3-XR02      | Hu0/0/0/2   | DC1-XR02           | Hu0/0/0/1        |

DC2 and DC3 follow the same internal port convention as DC1; only the device prefix changes.

## Important Design Note

Leaf 7 and Leaf 8 are border gateway leafs.

| Role                     | Ports           |
| ------------------------ | --------------- |
| Server-facing            | Eth1/1-Eth1/10  |
| Fabric uplinks to spines | Eth1/49-Eth1/52 |
| Core/XR uplinks          | Eth1/53-Eth1/54 |

This gives each data centre a clean physical design where compute traffic, fabric uplinks, and external DCI/core handoff are separated by port range.

## Generated Output

Generated NX-OS configs are written under:

```text
output_builds/SPINELEAF/DC1/
output_builds/SPINELEAF/DC2/
output_builds/SPINELEAF/DC3/
```

Each DC has 28 NX-OS configs:

- 4 super-spines
- 8 spines
- 16 leaves

Across all three sites, the generator creates 84 NX-OS configs.

## Global Services Variables

Global services are defined in `environments/spineleaf/env_vars.yaml` under `global_services`. The rendered configs include the shared baseline for:

- timezone, DNS, NTP, SSH, AAA/RADIUS, SNMPv3, syslog
- management ACL source subnets
- smart licensing, telemetry, netflow, and config archive
- the shared MOTD banner

Per-DC override variables are defined in the same file under `dc_overrides`. DC1, DC2, and DC3 each have their own management subnet and role-based loopback pools for spines, leafs, super-spines, and XR/core planning.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\scripts\generate_all_configs.py spineleaf
```

The same run also refreshes `NXOS_AUTOMATION/inventory/hosts.yaml` from `topology.yaml`.
