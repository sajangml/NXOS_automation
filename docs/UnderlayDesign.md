# IS-IS Underlay Design Artefact

# 1. Purpose

This document defines the IS-IS underlay routing architecture for the multi-data-center spine-leaf fabric deployed across:

* DC1
* DC2
* DC3

The underlay provides:

* routed IP reachability across the fabric
* deterministic ECMP forwarding
* resilient pod-to-pod transport
* VXLAN EVPN overlay transport reachability
* scalable Clos-based forwarding
* fast convergence through BFD-assisted IS-IS

This document covers only:

```text id="xj2sj0"
Leaf ↔ Spine ↔ Super-Spine IS-IS underlay
```

This document intentionally excludes:

```text id="6ll6pf"
Border Gateway Leaf ↔ Core/XR routing
```

which is treated as a separate routing domain and design artefact.

---

# 2. Underlay Topology

The underlay follows a 3-stage Clos fabric architecture.

## Physical Hierarchy

```text id="vrz8q4"
Leaf Layer
    ↓
Spine Layer
    ↓
Super-Spine Layer
```

Each data center contains:

| Component            | Quantity |
| -------------------- | -------: |
| Pods                 |        2 |
| Super-Spines per Pod |        2 |
| Spines per Pod       |        4 |
| Leafs per Pod        |        8 |

---

# 3. Underlay Routing Protocol

The fabric underlay uses:

```text id="7e4g83"
IS-IS Level-2 only
```

across all routed fabric links.

---

# 4. IS-IS Design Principles

## 4.1 Flat Level-2 Topology

The fabric operates as a flat IS-IS Level-2 domain.

### Rationale

| Design Choice       | Benefit                             |
| ------------------- | ----------------------------------- |
| Level-2 only        | Simplified operations               |
| No Level-1 areas    | Eliminates route leaking complexity |
| Flat SPF domain     | Optimized Clos fabric forwarding    |
| ECMP everywhere     | Maximum path utilization            |
| Consistent topology | Predictable convergence             |

---

## 4.2 Point-to-Point Network Type

All routed underlay interfaces use:

```text id="90k06z"
isis network point-to-point
```

### Rationale

This:

* removes DIS election requirements
* accelerates adjacency formation
* reduces IS-IS control-plane overhead
* optimizes routed fabric convergence

---

## 4.3 BFD Integration

BFD is enabled on all IS-IS underlay interfaces.

### Rationale

BFD provides:

* sub-second link failure detection
* rapid SPF recalculation
* fast ECMP convergence
* improved east-west application resiliency

---

## 4.4 Passive Loopback Advertisement

Loopback interfaces are advertised into IS-IS using passive mode.

### Rationale

This ensures:

* loopbacks remain reachable
* no IS-IS hellos are transmitted on loopbacks
* stable overlay router-id advertisement

---

# 5. Fabric Addressing Model

# 5.1 Infrastructure Supernets

| DC  | Infrastructure Supernet |
| --- | ----------------------- |
| DC1 | 10.1.0.0/16             |
| DC2 | 10.2.0.0/16             |
| DC3 | 10.3.0.0/16             |

---

# 5.2 Management Subnets

| DC  | Management Subnet |
| --- | ----------------- |
| DC1 | 10.1.100.0/24     |
| DC2 | 10.2.100.0/24     |
| DC3 | 10.3.100.0/24     |

---

# 5.3 Loopback Allocation

## Loopback Allocation Rules

| Device Type | Address Block |
| ----------- | ------------- |
| Spine       | 10.x.1.0/24   |
| Leaf        | 10.x.2.0/24   |
| Super-Spine | 10.x.3.0/24   |

---

## Example DC1 Allocation

| Device      | Loopback0   |
| ----------- | ----------- |
| DC1-P1-SS01 | 10.1.3.1/32 |
| DC1-P1-SS02 | 10.1.3.2/32 |
| DC1-P1-SP01 | 10.1.1.1/32 |
| DC1-P1-SP02 | 10.1.1.2/32 |
| DC1-P1-LF01 | 10.1.2.1/32 |
| DC1-P1-LF07 | 10.1.2.7/32 |

---

# 5.4 P2P Underlay Addressing

All routed underlay links use:

```text id="t0nn6o"
/31 point-to-point addressing
```

---

# 5.5 P2P Supernet Allocation

| DC  | Underlay P2P Summary |
| --- | -------------------- |
| DC1 | 172.16.0.0/16        |
| DC2 | 172.17.0.0/16        |
| DC3 | 172.18.0.0/16        |

---

# 5.6 P2P Allocation Structure

## DC1

| Segment                   | Address Block   |
| ------------------------- | --------------- |
| POD1 Leaf-to-Spine        | 172.16.1.0/24   |
| POD2 Leaf-to-Spine        | 172.16.2.0/24   |
| POD1 Spine-to-Super-Spine | 172.16.11.0/24  |
| POD2 Spine-to-Super-Spine | 172.16.12.0/24  |
| Inter-Pod Super-Spine     | 172.16.200.0/24 |

---

## DC2

| Segment                   | Address Block   |
| ------------------------- | --------------- |
| POD1 Leaf-to-Spine        | 172.17.1.0/24   |
| POD2 Leaf-to-Spine        | 172.17.2.0/24   |
| POD1 Spine-to-Super-Spine | 172.17.11.0/24  |
| POD2 Spine-to-Super-Spine | 172.17.12.0/24  |
| Inter-Pod Super-Spine     | 172.17.200.0/24 |

---

## DC3

| Segment                   | Address Block   |
| ------------------------- | --------------- |
| POD1 Leaf-to-Spine        | 172.18.1.0/24   |
| POD2 Leaf-to-Spine        | 172.18.2.0/24   |
| POD1 Spine-to-Super-Spine | 172.18.11.0/24  |
| POD2 Spine-to-Super-Spine | 172.18.12.0/24  |
| Inter-Pod Super-Spine     | 172.18.200.0/24 |

---

# 6. IS-IS Area Design

Each data center operates as an independent IS-IS area.

| DC  | IS-IS Area |
| --- | ---------- |
| DC1 | 49.0001    |
| DC2 | 49.0002    |
| DC3 | 49.0003    |

---

# 7. NET Address Construction

## NET Format

```text id="4h4mdu"
49.<AREA>.<SYSTEM-ID>.00
```

---

## System-ID Derivation

The System-ID is derived from Loopback0.

Example:

| Loopback | System-ID      |
| -------- | -------------- |
| 10.1.2.7 | 0100.1002.0007 |

---

## Example NET

```text id="wix5nn"
49.0001.0100.1002.0007.00
```

---

# 8. Physical Interface Design

All underlay interfaces operate as:

```text id="gx0n2d"
Layer-3 routed interfaces
```

---

## Interface Standards

| Parameter          | Value          |
| ------------------ | -------------- |
| Switchport Mode    | no switchport  |
| MTU                | 9216           |
| IS-IS Network Type | point-to-point |
| Addressing         | /31            |
| BFD                | enabled        |
| Shutdown State     | no shutdown    |

---

# 9. Leaf Underlay Design

Leaf switches provide:

* server attachment
* VXLAN VTEP functionality
* routed ECMP uplinks toward spines

---

## Leaf Uplink Allocation

| Interface | Destination |
| --------- | ----------- |
| Eth1/49   | Spine-01    |
| Eth1/50   | Spine-02    |
| Eth1/51   | Spine-03    |
| Eth1/52   | Spine-04    |

---

# 10. Spine Underlay Design

Spine switches provide:

* routed aggregation
* ECMP transit
* pod-wide underlay forwarding

---

## Spine Downlinks

| Interface Range | Destination     |
| --------------- | --------------- |
| Eth1/1–8        | Leafs LF01–LF08 |

---

## Spine Uplinks

| Interface | Destination    |
| --------- | -------------- |
| Eth1/49   | Super-Spine-01 |
| Eth1/50   | Super-Spine-02 |

---

# 11. Super-Spine Underlay Design

Super-Spines provide:

* inter-pod transport
* pod aggregation
* fabric-wide ECMP forwarding

---

## Super-Spine Downlinks

| Interface Range | Destination |
| --------------- | ----------- |
| Eth1/1–4        | Spine-01–04 |

---

## Inter-Pod Super-Spine Links

| Interface | Destination            |
| --------- | ---------------------- |
| Eth1/49   | Remote Pod Super-Spine |
| Eth1/50   | Remote Pod Super-Spine |

---

# 12. ECMP Design

The underlay enables:

```text id="5e9i7x"
maximum-paths 64
```

across the IS-IS domain.

---

## Rationale

This allows:

* full Clos utilization
* optimal path diversity
* high east-west throughput
* deterministic multipathing

---

# 13. MTU Design

All routed fabric interfaces use:

```text id="4um5y0"
MTU 9216
```

---

## Rationale

This accommodates:

* VXLAN encapsulation overhead
* storage traffic
* large east-west frames
* multicast replication
* future AI/HPC transport requirements

---

# 14. Failure Domain Design

The IS-IS underlay domain is intentionally restricted to:

```text id="fkwqih"
Leaf ↔ Spine ↔ Super-Spine fabric routing
```

This ensures:

* predictable SPF scope
* contained flooding domains
* stable fabric convergence
* isolation from WAN/core instability

---

# 15. Hardware Platforms

| Layer       | Platform                |
| ----------- | ----------------------- |
| Leaf        | Cisco Nexus 93180YC-FX3 |
| Spine       | Cisco Nexus 9364C-GX    |
| Super-Spine | Cisco Nexus 9364C-GX    |

---

# 16. Operational Characteristics

The resulting underlay provides:

| Capability              | Outcome                       |
| ----------------------- | ----------------------------- |
| ECMP Clos forwarding    | Deterministic pathing         |
| IS-IS SPF convergence   | Fast recovery                 |
| BFD-assisted detection  | Sub-second failover           |
| Routed fabric transport | VXLAN-ready underlay          |
| Flat L2 IS-IS domain    | Simplified operations         |
| Point-to-point links    | Optimized adjacency formation |

---

# 17. Design Summary

The underlay architecture establishes a scalable routed transport fabric optimized for:

* VXLAN EVPN overlays
* east-west heavy workloads
* Kubernetes platforms
* virtualization
* storage fabrics
* high-throughput application transport
* multi-pod data center fabrics
* future AI/HPC transport scalability



# IS-IS Underlay Config Model

## 1. Global IS-IS Template

```cisco
feature isis
feature bfd

router isis FABRIC-UNDERLAY
  net <ISIS_NET>
  is-type level-2
  log-adjacency-changes
  address-family ipv4 unicast
    maximum-paths 64
```

---

## 2. Leaf Config Model

Applies to **LF01–LF08**.

```cisco
hostname <DC>-<POD>-LF<NN>

feature isis
feature bfd

router isis FABRIC-UNDERLAY
  net <ISIS_NET>
  is-type level-2
  log-adjacency-changes
  address-family ipv4 unicast
    maximum-paths 64

interface loopback0
  description ROUTING_LOOPBACK_UNDERLAY
  ip address <LOOPBACK0>/32
  ip router isis FABRIC-UNDERLAY
  isis passive-interface level-2

interface Ethernet1/49
  description TO_<DC>-<POD>-SP01
  no switchport
  mtu 9216
  ip address <P2P_TO_SP01>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/50
  description TO_<DC>-<POD>-SP02
  no switchport
  mtu 9216
  ip address <P2P_TO_SP02>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/51
  description TO_<DC>-<POD>-SP03
  no switchport
  mtu 9216
  ip address <P2P_TO_SP03>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/52
  description TO_<DC>-<POD>-SP04
  no switchport
  mtu 9216
  ip address <P2P_TO_SP04>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown
```

---

## 3. Spine Config Model

Applies to **SP01–SP04**.

```cisco
hostname <DC>-<POD>-SP<NN>

feature isis
feature bfd

router isis FABRIC-UNDERLAY
  net <ISIS_NET>
  is-type level-2
  log-adjacency-changes
  address-family ipv4 unicast
    maximum-paths 64

interface loopback0
  description ROUTING_LOOPBACK_UNDERLAY
  ip address <LOOPBACK0>/32
  ip router isis FABRIC-UNDERLAY
  isis passive-interface level-2

interface Ethernet1/1
  description TO_<DC>-<POD>-LF01
  no switchport
  mtu 9216
  ip address <P2P_TO_LF01>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/2
  description TO_<DC>-<POD>-LF02
  no switchport
  mtu 9216
  ip address <P2P_TO_LF02>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/3
  description TO_<DC>-<POD>-LF03
  no switchport
  mtu 9216
  ip address <P2P_TO_LF03>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/4
  description TO_<DC>-<POD>-LF04
  no switchport
  mtu 9216
  ip address <P2P_TO_LF04>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/5
  description TO_<DC>-<POD>-LF05
  no switchport
  mtu 9216
  ip address <P2P_TO_LF05>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/6
  description TO_<DC>-<POD>-LF06
  no switchport
  mtu 9216
  ip address <P2P_TO_LF06>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/7
  description TO_<DC>-<POD>-LF07
  no switchport
  mtu 9216
  ip address <P2P_TO_LF07>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/8
  description TO_<DC>-<POD>-LF08
  no switchport
  mtu 9216
  ip address <P2P_TO_LF08>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/49
  description TO_<DC>-<POD>-SS01
  no switchport
  mtu 9216
  ip address <P2P_TO_SS01>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/50
  description TO_<DC>-<POD>-SS02
  no switchport
  mtu 9216
  ip address <P2P_TO_SS02>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown
```

---

## 4. Super-Spine Config Model

Applies to **SS01–SS02**.

```cisco
hostname <DC>-<POD>-SS<NN>

feature isis
feature bfd

router isis FABRIC-UNDERLAY
  net <ISIS_NET>
  is-type level-2
  log-adjacency-changes
  address-family ipv4 unicast
    maximum-paths 64

interface loopback0
  description ROUTING_LOOPBACK_UNDERLAY
  ip address <LOOPBACK0>/32
  ip router isis FABRIC-UNDERLAY
  isis passive-interface level-2

interface Ethernet1/1
  description TO_<DC>-<POD>-SP01
  no switchport
  mtu 9216
  ip address <P2P_TO_SP01>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/2
  description TO_<DC>-<POD>-SP02
  no switchport
  mtu 9216
  ip address <P2P_TO_SP02>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/3
  description TO_<DC>-<POD>-SP03
  no switchport
  mtu 9216
  ip address <P2P_TO_SP03>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/4
  description TO_<DC>-<POD>-SP04
  no switchport
  mtu 9216
  ip address <P2P_TO_SP04>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/49
  description TO_REMOTE_POD_SS01_OR_SS02
  no switchport
  mtu 9216
  ip address <P2P_TO_REMOTE_POD_SS>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/50
  description TO_REMOTE_POD_SS01_OR_SS02
  no switchport
  mtu 9216
  ip address <P2P_TO_REMOTE_POD_SS>/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown
```

---

## 5. Example Config — DC1-P1-LF01

```cisco
hostname DC1-P1-LF01

feature isis
feature bfd

router isis FABRIC-UNDERLAY
  net 49.0001.0100.1002.0001.00
  is-type level-2
  log-adjacency-changes
  address-family ipv4 unicast
    maximum-paths 64

interface loopback0
  description ROUTING_LOOPBACK_UNDERLAY
  ip address 10.1.2.1/32
  ip router isis FABRIC-UNDERLAY
  isis passive-interface level-2

interface Ethernet1/49
  description TO_DC1-P1-SP01
  no switchport
  mtu 9216
  ip address 172.16.1.0/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/50
  description TO_DC1-P1-SP02
  no switchport
  mtu 9216
  ip address 172.16.1.2/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/51
  description TO_DC1-P1-SP03
  no switchport
  mtu 9216
  ip address 172.16.1.4/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/52
  description TO_DC1-P1-SP04
  no switchport
  mtu 9216
  ip address 172.16.1.6/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown
```

---

## 6. Example Config — DC1-P1-SP01

```cisco
hostname DC1-P1-SP01

feature isis
feature bfd

router isis FABRIC-UNDERLAY
  net 49.0001.0100.1001.0001.00
  is-type level-2
  log-adjacency-changes
  address-family ipv4 unicast
    maximum-paths 64

interface loopback0
  description ROUTING_LOOPBACK_UNDERLAY
  ip address 10.1.1.1/32
  ip router isis FABRIC-UNDERLAY
  isis passive-interface level-2

interface Ethernet1/1
  description TO_DC1-P1-LF01
  no switchport
  mtu 9216
  ip address 172.16.1.1/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/2
  description TO_DC1-P1-LF02
  no switchport
  mtu 9216
  ip address 172.16.1.9/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/3
  description TO_DC1-P1-LF03
  no switchport
  mtu 9216
  ip address 172.16.1.17/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/4
  description TO_DC1-P1-LF04
  no switchport
  mtu 9216
  ip address 172.16.1.25/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/5
  description TO_DC1-P1-LF05
  no switchport
  mtu 9216
  ip address 172.16.1.33/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/6
  description TO_DC1-P1-LF06
  no switchport
  mtu 9216
  ip address 172.16.1.41/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/7
  description TO_DC1-P1-LF07
  no switchport
  mtu 9216
  ip address 172.16.1.49/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/8
  description TO_DC1-P1-LF08
  no switchport
  mtu 9216
  ip address 172.16.1.57/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/49
  description TO_DC1-P1-SS01
  no switchport
  mtu 9216
  ip address 172.16.11.0/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/50
  description TO_DC1-P1-SS02
  no switchport
  mtu 9216
  ip address 172.16.11.2/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown
```

---

## 7. Example Config — DC1-P1-SS01

```cisco
hostname DC1-P1-SS01

feature isis
feature bfd

router isis FABRIC-UNDERLAY
  net 49.0001.0100.1003.0001.00
  is-type level-2
  log-adjacency-changes
  address-family ipv4 unicast
    maximum-paths 64

interface loopback0
  description ROUTING_LOOPBACK_UNDERLAY
  ip address 10.1.3.1/32
  ip router isis FABRIC-UNDERLAY
  isis passive-interface level-2

interface Ethernet1/1
  description TO_DC1-P1-SP01
  no switchport
  mtu 9216
  ip address 172.16.11.1/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/2
  description TO_DC1-P1-SP02
  no switchport
  mtu 9216
  ip address 172.16.11.5/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/3
  description TO_DC1-P1-SP03
  no switchport
  mtu 9216
  ip address 172.16.11.9/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/4
  description TO_DC1-P1-SP04
  no switchport
  mtu 9216
  ip address 172.16.11.13/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/49
  description TO_DC1-P2-SS01
  no switchport
  mtu 9216
  ip address 172.16.200.0/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown

interface Ethernet1/50
  description TO_DC1-P2-SS02
  no switchport
  mtu 9216
  ip address 172.16.200.2/31
  ip router isis FABRIC-UNDERLAY
  isis network point-to-point
  isis bfd
  no shutdown
```

This config model keeps the IS-IS artefact clean and excludes BGW-to-core peering.

