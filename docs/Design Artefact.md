# NXOS Automation Design Artefact

## Physical Design Summary

The model supports three data centres: `DC1`, `DC2`, and `DC3`.

Each data centre has two independent fabric pods. Each pod has its own super-spine layer, spine layer, and leaf layer.

The normal server leafs connect upward to all four spines in the same pod. The spines then connect upward to both super-spines. Leaf 7 and Leaf 8 in each pod act as border gateway leafs, so they provide the external handoff from the fabric to the Cisco XR core/DCI routers.

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

## Fabric Hardware Recommendation

| Layer       | Platform             | ASIC           | Rack Role                  |
| ----------- | -------------------- | -------------- | -------------------------- |
| Leaf        | Nexus 93180YC-FX3    | CloudScale FX3 | Top-of-rack                |
| Border Leaf | Nexus 93180YC-FX3    | CloudScale FX3 | Dedicated border rack pair |
| Spine       | Nexus 9364C-GX       | CloudScale GX  | End-of-row                 |
| Super-Spine | Nexus 9364C-GX       | CloudScale GX  | Network spine row          |
| DCI/Core    | Cisco IOS-XR routers | Platform-based | Core/DCI rack              |

The Nexus 93180YC-FX3 fits the leaf and border leaf design because it provides 1/10/25G server-facing ports plus 40/100G QSFP28 uplinks for spine and XR/core connectivity.

The Nexus 9364C-GX is recommended for spine and super-spine roles because it provides high radix 100/400G capability, better EVPN scale, larger ECMP headroom, and a longer lifecycle for future AI/HPC or high-throughput workloads.

## Design Summary

| Item                 | Design                  |
| -------------------- | ----------------------- |
| Data Centres         | DC1, DC2, DC3           |
| Pods per DC          | 2                       |
| Super-Spines per Pod | 2                       |
| Spines per Pod       | 4                       |
| Leafs per Pod        | 8                       |
| Border Leafs per Pod | LF07 and LF08           |
| Servers per Leaf     | 10                      |
| Servers per Pod      | 80                      |
| Servers per DC       | 160                     |
| Server Leaf Platform | Cisco Nexus 93180YC-FX3 |
| Border Leaf Platform | Cisco Nexus 93180YC-FX3 |
| Spine Platform       | Cisco Nexus 9364C-GX    |
| Super-Spine Platform | Cisco Nexus 9364C-GX    |
| DCI/Core Platform    | Cisco IOS-XR routers    |

## Leaf Port Allocation

Standard compute leafs `LF01-LF06`:

| Port Range | Usage                     |
| ---------- | ------------------------- |
| Eth1/1-10  | Servers                   |
| Eth1/49-52 | Spine uplinks             |
| Eth1/53-54 | Reserved/Future expansion |

Border leafs `LF07-LF08`:

| Port Range | Usage           |
| ---------- | --------------- |
| Eth1/1-10  | Servers         |
| Eth1/49-52 | Spine uplinks   |
| Eth1/53-54 | XR/Core uplinks |

## Leaf-to-Spine Port Mapping

This applies to every pod in every DC.

| Leaf | Leaf Port | Spine | Spine Port |
| ---- | --------- | ----- | ---------- |
| LF01 | Eth1/49   | SP01  | Eth1/1     |
| LF01 | Eth1/50   | SP02  | Eth1/1     |
| LF01 | Eth1/51   | SP03  | Eth1/1     |
| LF01 | Eth1/52   | SP04  | Eth1/1     |
| LF02 | Eth1/49   | SP01  | Eth1/2     |
| LF02 | Eth1/50   | SP02  | Eth1/2     |
| LF02 | Eth1/51   | SP03  | Eth1/2     |
| LF02 | Eth1/52   | SP04  | Eth1/2     |
| LF03 | Eth1/49   | SP01  | Eth1/3     |
| LF03 | Eth1/50   | SP02  | Eth1/3     |
| LF03 | Eth1/51   | SP03  | Eth1/3     |
| LF03 | Eth1/52   | SP04  | Eth1/3     |
| LF04 | Eth1/49   | SP01  | Eth1/4     |
| LF04 | Eth1/50   | SP02  | Eth1/4     |
| LF04 | Eth1/51   | SP03  | Eth1/4     |
| LF04 | Eth1/52   | SP04  | Eth1/4     |
| LF05 | Eth1/49   | SP01  | Eth1/5     |
| LF05 | Eth1/50   | SP02  | Eth1/5     |
| LF05 | Eth1/51   | SP03  | Eth1/5     |
| LF05 | Eth1/52   | SP04  | Eth1/5     |
| LF06 | Eth1/49   | SP01  | Eth1/6     |
| LF06 | Eth1/50   | SP02  | Eth1/6     |
| LF06 | Eth1/51   | SP03  | Eth1/6     |
| LF06 | Eth1/52   | SP04  | Eth1/6     |
| LF07 | Eth1/49   | SP01  | Eth1/7     |
| LF07 | Eth1/50   | SP02  | Eth1/7     |
| LF07 | Eth1/51   | SP03  | Eth1/7     |
| LF07 | Eth1/52   | SP04  | Eth1/7     |
| LF08 | Eth1/49   | SP01  | Eth1/8     |
| LF08 | Eth1/50   | SP02  | Eth1/8     |
| LF08 | Eth1/51   | SP03  | Eth1/8     |
| LF08 | Eth1/52   | SP04  | Eth1/8     |

## Spine-to-Super-Spine Port Mapping

This applies to every pod in every DC.

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

## Pod-to-Pod Super-Spine Connectivity

This applies inside each DC.

| Source  | Port    | Destination | Port    |
| ------- | ------- | ----------- | ------- |
| P1-SS01 | Eth1/49 | P2-SS01     | Eth1/49 |
| P1-SS01 | Eth1/50 | P2-SS02     | Eth1/49 |
| P1-SS02 | Eth1/49 | P2-SS01     | Eth1/50 |
| P1-SS02 | Eth1/50 | P2-SS02     | Eth1/50 |

## Border Leaf-to-XR Port Mapping

This applies to DC1, DC2, and DC3.

| Border Leaf | Border Leaf Port | XR Router | XR Port    |
| ----------- | ---------------- | --------- | ---------- |
| P1-LF07     | Eth1/53          | XR01      | Hu0/0/0/10 |
| P1-LF07     | Eth1/54          | XR02      | Hu0/0/0/10 |
| P1-LF08     | Eth1/53          | XR01      | Hu0/0/0/11 |
| P1-LF08     | Eth1/54          | XR02      | Hu0/0/0/11 |
| P2-LF07     | Eth1/53          | XR01      | Hu0/0/0/12 |
| P2-LF07     | Eth1/54          | XR02      | Hu0/0/0/12 |
| P2-LF08     | Eth1/53          | XR01      | Hu0/0/0/13 |
| P2-LF08     | Eth1/54          | XR02      | Hu0/0/0/13 |

## Inter-DC XR-to-XR Port Mapping

| Source Router | Source Port | Destination Router | Destination Port |
| ------------- | ----------- | ------------------ | ---------------- |
| DC1-XR01      | Hu0/0/0/0   | DC2-XR01           | Hu0/0/0/0        |
| DC1-XR02      | Hu0/0/0/0   | DC2-XR02           | Hu0/0/0/0        |
| DC2-XR01      | Hu0/0/0/1   | DC3-XR01           | Hu0/0/0/1        |
| DC2-XR02      | Hu0/0/0/1   | DC3-XR02           | Hu0/0/0/1        |
| DC3-XR01      | Hu0/0/0/2   | DC1-XR01           | Hu0/0/0/1        |
| DC3-XR02      | Hu0/0/0/2   | DC1-XR02           | Hu0/0/0/1        |

## Server Port Allocation

This applies per DC.

| Pod | Leaf | Leaf Ports    | Servers    |
| --- | ---- | ------------- | ---------- |
| P1  | LF01 | Eth1/1-Eth1/10 | SRV001-010 |
| P1  | LF02 | Eth1/1-Eth1/10 | SRV011-020 |
| P1  | LF03 | Eth1/1-Eth1/10 | SRV021-030 |
| P1  | LF04 | Eth1/1-Eth1/10 | SRV031-040 |
| P1  | LF05 | Eth1/1-Eth1/10 | SRV041-050 |
| P1  | LF06 | Eth1/1-Eth1/10 | SRV051-060 |
| P1  | LF07 | Eth1/1-Eth1/10 | SRV061-070 |
| P1  | LF08 | Eth1/1-Eth1/10 | SRV071-080 |
| P2  | LF01 | Eth1/1-Eth1/10 | SRV081-090 |
| P2  | LF02 | Eth1/1-Eth1/10 | SRV091-100 |
| P2  | LF03 | Eth1/1-Eth1/10 | SRV101-110 |
| P2  | LF04 | Eth1/1-Eth1/10 | SRV111-120 |
| P2  | LF05 | Eth1/1-Eth1/10 | SRV121-130 |
| P2  | LF06 | Eth1/1-Eth1/10 | SRV131-140 |
| P2  | LF07 | Eth1/1-Eth1/10 | SRV141-150 |
| P2  | LF08 | Eth1/1-Eth1/10 | SRV151-160 |

## Hardware and Link Count

| Device Type  | Per Pod | Per DC | 3 DC Total |
| ------------ | ------: | -----: | ---------: |
| Super-Spines |       2 |      4 |         12 |
| Spines       |       4 |      8 |         24 |
| Leafs        |       8 |     16 |         48 |
| Border Leafs |       2 |      4 |         12 |
| XR Routers   |     N/A |      2 |          6 |
| Servers      |      80 |    160 |        480 |

| Link Type              |   Per Pod | Per DC | 3 DC Total |
| ---------------------- | --------: | -----: | ---------: |
| Server-to-Leaf         |        80 |    160 |        480 |
| Leaf-to-Spine          |        32 |     64 |        192 |
| Spine-to-Super-Spine   |         8 |     16 |         48 |
| Pod-to-Pod Super-Spine |       N/A |      4 |         12 |
| Border Leaf-to-XR      |         4 |      8 |         24 |
| Inter-DC XR Links      |       N/A | Shared |          6 |

## Speed Recommendation

| Link Type              | Speed        |
| ---------------------- | ------------ |
| Server-to-Leaf         | 10/25G       |
| Leaf-to-Spine          | 100G         |
| Spine-to-Super-Spine   | 100G or 400G |
| Pod-to-Pod Super-Spine | 100G or 400G |
| Border Leaf-to-XR      | 100G         |
| XR-to-XR DCI           | 100G or 400G |

Current leaf oversubscription is favorable:

```text
10 x 25G servers = 250G southbound
4 x 100G uplinks = 400G northbound
250G : 400G = 1 : 1.6
```

## Final Design Position

This is a clean 3-DC, 2-pod-per-DC, spine-leaf-super-spine architecture with dedicated border leaf handoff to the XR core.

```text
Compute/server traffic terminates on leafs.
Fabric aggregation happens through spines and super-spines.
External/DCI routing terminates on LF07/LF08 border leafs.
DC-to-DC routing is handled by Cisco XR routers.
```
