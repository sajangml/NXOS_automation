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
  ↓
Leaf
  ↓
Spine
  ↓
Super-Spine
  ↓
Border Leaf 7 / Leaf 8
  ↓
Cisco XR Core / DCI Router
  ↓
DC2 / DC3
```

The corrected rule is:

```text
Super-spines do not connect directly to XR.
Border Leaf 7 and Leaf 8 connect to XR/core.
```

## DC1 Device Count

| Layer           | Devices |
| --------------- | ------: |
| Pods            |       2 |
| Super-Spines    |       4 |
| Spines          |       8 |
| Leafs           |      16 |
| Border Leafs    |       4 |
| Servers         |     160 |
| XR/Core Routers |       2 |

## DC1 POD1 Server-to-Leaf Connectivity

| Source Device     | Source Port | Destination Device | Destination Port |
| ----------------- | ----------- | ------------------ | ---------------- |
| DC1-P1-SRV001-010 | NIC1        | DC1-P1-LF01        | Eth1/1-Eth1/10   |
| DC1-P1-SRV011-020 | NIC1        | DC1-P1-LF02        | Eth1/1-Eth1/10   |
| DC1-P1-SRV021-030 | NIC1        | DC1-P1-LF03        | Eth1/1-Eth1/10   |
| DC1-P1-SRV031-040 | NIC1        | DC1-P1-LF04        | Eth1/1-Eth1/10   |
| DC1-P1-SRV041-050 | NIC1        | DC1-P1-LF05        | Eth1/1-Eth1/10   |
| DC1-P1-SRV051-060 | NIC1        | DC1-P1-LF06        | Eth1/1-Eth1/10   |
| DC1-P1-SRV061-070 | NIC1        | DC1-P1-LF07        | Eth1/1-Eth1/10   |
| DC1-P1-SRV071-080 | NIC1        | DC1-P1-LF08        | Eth1/1-Eth1/10   |

## DC1 POD2 Server-to-Leaf Connectivity

| Source Device     | Source Port | Destination Device | Destination Port |
| ----------------- | ----------- | ------------------ | ---------------- |
| DC1-P2-SRV081-090 | NIC1        | DC1-P2-LF01        | Eth1/1-Eth1/10   |
| DC1-P2-SRV091-100 | NIC1        | DC1-P2-LF02        | Eth1/1-Eth1/10   |
| DC1-P2-SRV101-110 | NIC1        | DC1-P2-LF03        | Eth1/1-Eth1/10   |
| DC1-P2-SRV111-120 | NIC1        | DC1-P2-LF04        | Eth1/1-Eth1/10   |
| DC1-P2-SRV121-130 | NIC1        | DC1-P2-LF05        | Eth1/1-Eth1/10   |
| DC1-P2-SRV131-140 | NIC1        | DC1-P2-LF06        | Eth1/1-Eth1/10   |
| DC1-P2-SRV141-150 | NIC1        | DC1-P2-LF07        | Eth1/1-Eth1/10   |
| DC1-P2-SRV151-160 | NIC1        | DC1-P2-LF08        | Eth1/1-Eth1/10   |

## DC1 POD1 Leaf-to-Spine Connectivity

Every leaf connects to all four spines in the same pod:

| Leaf Port | Spine |
| --------- | ----- |
| Eth1/49   | SP01  |
| Eth1/50   | SP02  |
| Eth1/51   | SP03  |
| Eth1/52   | SP04  |

Spine destination ports follow the leaf ID. For example, `DC1-P1-LF01` connects to `Eth1/1` on every spine, `DC1-P1-LF02` connects to `Eth1/2`, and `DC1-P1-LF08` connects to `Eth1/8`.

## DC1 POD2 Leaf-to-Spine Connectivity

Same pattern as POD1:

| Leaf Port | Spine |
| --------- | ----- |
| Eth1/49   | SP01  |
| Eth1/50   | SP02  |
| Eth1/51   | SP03  |
| Eth1/52   | SP04  |

Spine destination ports follow the leaf ID.

## DC1 POD1 Spine-to-Super-Spine Connectivity

| Source Device | Source Port | Destination Device | Destination Port |
| ------------- | ----------- | ------------------ | ---------------- |
| DC1-P1-SP01   | Eth1/49     | DC1-P1-SS01        | Eth1/1           |
| DC1-P1-SP01   | Eth1/50     | DC1-P1-SS02        | Eth1/1           |
| DC1-P1-SP02   | Eth1/49     | DC1-P1-SS01        | Eth1/2           |
| DC1-P1-SP02   | Eth1/50     | DC1-P1-SS02        | Eth1/2           |
| DC1-P1-SP03   | Eth1/49     | DC1-P1-SS01        | Eth1/3           |
| DC1-P1-SP03   | Eth1/50     | DC1-P1-SS02        | Eth1/3           |
| DC1-P1-SP04   | Eth1/49     | DC1-P1-SS01        | Eth1/4           |
| DC1-P1-SP04   | Eth1/50     | DC1-P1-SS02        | Eth1/4           |

## DC1 POD2 Spine-to-Super-Spine Connectivity

| Source Device | Source Port | Destination Device | Destination Port |
| ------------- | ----------- | ------------------ | ---------------- |
| DC1-P2-SP01   | Eth1/49     | DC1-P2-SS01        | Eth1/1           |
| DC1-P2-SP01   | Eth1/50     | DC1-P2-SS02        | Eth1/1           |
| DC1-P2-SP02   | Eth1/49     | DC1-P2-SS01        | Eth1/2           |
| DC1-P2-SP02   | Eth1/50     | DC1-P2-SS02        | Eth1/2           |
| DC1-P2-SP03   | Eth1/49     | DC1-P2-SS01        | Eth1/3           |
| DC1-P2-SP03   | Eth1/50     | DC1-P2-SS02        | Eth1/3           |
| DC1-P2-SP04   | Eth1/49     | DC1-P2-SS01        | Eth1/4           |
| DC1-P2-SP04   | Eth1/50     | DC1-P2-SS02        | Eth1/4           |

## DC1 Pod-to-Pod Super-Spine Connectivity

| Source Device | Source Port | Destination Device | Destination Port |
| ------------- | ----------- | ------------------ | ---------------- |
| DC1-P1-SS01   | Eth1/49     | DC1-P2-SS01        | Eth1/49          |
| DC1-P1-SS01   | Eth1/50     | DC1-P2-SS02        | Eth1/49          |
| DC1-P1-SS02   | Eth1/49     | DC1-P2-SS01        | Eth1/50          |
| DC1-P1-SS02   | Eth1/50     | DC1-P2-SS02        | Eth1/50          |

## DC1 Border Leaf to XR/Core Connectivity

Recommended: dual-home each border leaf to both XR routers.

| Source Device | Source Port | Destination Device | Destination Port | Function           |
| ------------- | ----------- | ------------------ | ---------------- | ------------------ |
| DC1-P1-LF07   | Eth1/53     | DC1-XR01           | Hu0/0/0/10       | Border/Core uplink |
| DC1-P1-LF07   | Eth1/54     | DC1-XR02           | Hu0/0/0/10       | Border/Core uplink |
| DC1-P1-LF08   | Eth1/53     | DC1-XR01           | Hu0/0/0/11       | Border/Core uplink |
| DC1-P1-LF08   | Eth1/54     | DC1-XR02           | Hu0/0/0/11       | Border/Core uplink |
| DC1-P2-LF07   | Eth1/53     | DC1-XR01           | Hu0/0/0/12       | Border/Core uplink |
| DC1-P2-LF07   | Eth1/54     | DC1-XR02           | Hu0/0/0/12       | Border/Core uplink |
| DC1-P2-LF08   | Eth1/53     | DC1-XR01           | Hu0/0/0/13       | Border/Core uplink |
| DC1-P2-LF08   | Eth1/54     | DC1-XR02           | Hu0/0/0/13       | Border/Core uplink |

## DC1 XR-to-DCI Connectivity

| Source Device | Source Port | Destination Device | Destination Port |
| ------------- | ----------- | ------------------ | ---------------- |
| DC1-XR01      | Hu0/0/0/0   | DC2-XR01           | Hu0/0/0/0        |
| DC1-XR01      | Hu0/0/0/1   | DC3-XR01           | Hu0/0/0/0        |
| DC1-XR02      | Hu0/0/0/0   | DC2-XR02           | Hu0/0/0/0        |
| DC1-XR02      | Hu0/0/0/1   | DC3-XR02           | Hu0/0/0/0        |

## Important Design Note

Leaf 7 and Leaf 8 are no longer just normal compute leafs. They are border gateway leafs.

So they have three roles:

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

With this design, each DC has 28 NX-OS configs:

- 4 super-spines
- 8 spines
- 16 leaves

Across all three sites, the generator creates 84 NX-OS configs.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\scripts\generate_all_configs.py spineleaf
```

The same run also refreshes `NXOS_AUTOMATION/inventory/hosts.yaml` from `topology.yaml`.
