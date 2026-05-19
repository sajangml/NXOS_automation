# Core Network Design Artefact

# 1. Purpose

This document defines the core network architecture interconnecting the multi-data-center VXLAN EVPN fabrics deployed across:

* DC1
* DC2
* DC3

The core network provides:

* resilient inter-data-center transport
* external routing-domain separation
* scalable DCI routing
* deterministic routed forwarding
* high-availability transport
* future MPLS/SR expansion capability
* scalable Border Gateway connectivity

The core network operates independently from the internal fabric underlay.

---

# 2. Scope

This document covers:

* Cisco IOS-XR core router architecture
* DCI transport topology
* XR-to-XR interconnectivity
* Border Gateway Leaf connectivity
* ASN allocation
* IP addressing
* routing-domain separation
* eBGP transport routing

This document excludes:

* VXLAN EVPN overlay configuration
* tenant VRF design
* MPLS L3VPN services
* SR-MPLS/SRv6 implementation
* Internet edge connectivity
* firewall services

---

# 3. Core Network Architecture

Each data center contains two dedicated Cisco IOS-XR core routers.

## Core Router Allocation

| Data Center | Routers            |
| ----------- | ------------------ |
| DC1         | DC1-XR01, DC1-XR02 |
| DC2         | DC2-XR01, DC2-XR02 |
| DC3         | DC3-XR01, DC3-XR02 |

---

# 4. Core Network Role

The XR core routers provide:

* DCI transport routing
* WAN/core route exchange
* inter-site resiliency
* routing-domain isolation
* scalable external transport
* future MPLS/SR transport foundation

---

# 5. DCI Topology

The DCI transport uses a resilient dual-router topology.

## DCI Interconnect Model

```text id="w9h8vt"
DC1-XR ↔ DC2-XR
DC2-XR ↔ DC3-XR
DC3-XR ↔ DC1-XR
```

Each XR pair is interconnected using dedicated routed point-to-point transport links.

---

# 6. Routing Architecture

# 6.1 Internal Fabric Routing

| Domain                     | Protocol      |
| -------------------------- | ------------- |
| Leaf ↔ Spine ↔ Super-Spine | IS-IS Level-2 |
| VXLAN Overlay              | MP-BGP EVPN   |

---

# 6.2 Core Routing

| Segment  | Protocol          |
| -------- | ----------------- |
| BGW ↔ XR | eBGP IPv4 Unicast |
| XR ↔ XR  | eBGP IPv4 Unicast |

---

# 7. Routing Domain Separation

The architecture intentionally separates:

| Domain          | Routing Scope       |
| --------------- | ------------------- |
| Fabric Underlay | Internal DC routing |
| Core Network    | DCI/WAN routing     |

The XR core routers do not participate in:

```text id="0m07li"
FABRIC-UNDERLAY IS-IS
```

This prevents:

* WAN instability propagating into the fabric
* uncontrolled IS-IS flooding
* oversized failure domains
* fabric/core convergence coupling

---

# 8. ASN Allocation

## Fabric ASNs

| Data Center | ASN   |
| ----------- | ----- |
| DC1         | 65101 |
| DC2         | 65102 |
| DC3         | 65103 |

---

## Core ASN

| Domain          | ASN   |
| --------------- | ----- |
| XR Core Network | 65000 |

---

# 9. Infrastructure Addressing Model

# 9.1 Infrastructure Supernets

| DC  | Infrastructure Supernet |
| --- | ----------------------- |
| DC1 | 10.1.0.0/16             |
| DC2 | 10.2.0.0/16             |
| DC3 | 10.3.0.0/16             |

---

# 9.2 Management Addressing

Management addressing is separated between:

* XR infrastructure
* Fabric infrastructure

## Allocation

| DC  | XR Management | Fabric Management |
| --- | ------------- | ----------------- |
| DC1 | 10.1.100.0/25 | 10.1.100.128/25   |
| DC2 | 10.2.100.0/25 | 10.2.100.128/25   |
| DC3 | 10.3.100.0/25 | 10.3.100.128/25   |

---

# 9.3 XR Loopback Allocation

Loopback0 provides:

* router-id
* BGP peering source
* telemetry source
* future SR/MPLS node SID anchor
* stable transport endpoint

---

## Allocation

| Device   | Loopback0   |
| -------- | ----------- |
| DC1-XR01 | 10.1.4.1/32 |
| DC1-XR02 | 10.1.4.2/32 |
| DC2-XR01 | 10.2.4.1/32 |
| DC2-XR02 | 10.2.4.2/32 |
| DC3-XR01 | 10.3.4.1/32 |
| DC3-XR02 | 10.3.4.2/32 |

---

# 9.4 Future SR/MPLS Node SID Allocation

Reserved for future SR-MPLS or SRv6 expansion.

| DC  | Node SID Range |
| --- | -------------- |
| DC1 | 10.1.5.0/24    |
| DC2 | 10.2.5.0/24    |
| DC3 | 10.3.5.0/24    |

---

# 10. BGW to XR Transit Addressing

Dedicated routed transit subnets are allocated between Border Gateway Leafs and XR routers.

## Allocation

| DC  | Transit Range   |
| --- | --------------- |
| DC1 | 172.16.250.0/24 |
| DC2 | 172.17.250.0/24 |
| DC3 | 172.18.250.0/24 |

---

## Example DC1 Allocation

| Link        | Subnet          |
| ----------- | --------------- |
| LF07 ↔ XR01 | 172.16.250.0/31 |
| LF07 ↔ XR02 | 172.16.250.2/31 |
| LF08 ↔ XR01 | 172.16.250.4/31 |
| LF08 ↔ XR02 | 172.16.250.6/31 |

---

# 11. XR-to-XR DCI Transit Addressing

Dedicated routed transport networks are allocated for DCI interconnectivity.

## DCI Transit Allocation

| DCI Segment | Network        |
| ----------- | -------------- |
| DC1 ↔ DC2   | 172.31.12.0/24 |
| DC2 ↔ DC3   | 172.31.23.0/24 |
| DC3 ↔ DC1   | 172.31.31.0/24 |

---

## Example Interface Allocation

# DC1 ↔ DC2

| Device   | Interface | Address        |
| -------- | --------- | -------------- |
| DC1-XR01 | Hu0/0/0/0 | 172.31.12.0/31 |
| DC2-XR01 | Hu0/0/0/0 | 172.31.12.1/31 |
| DC1-XR02 | Hu0/0/0/0 | 172.31.12.2/31 |
| DC2-XR02 | Hu0/0/0/0 | 172.31.12.3/31 |

---

# DC2 ↔ DC3

| Device   | Interface | Address        |
| -------- | --------- | -------------- |
| DC2-XR01 | Hu0/0/0/1 | 172.31.23.0/31 |
| DC3-XR01 | Hu0/0/0/1 | 172.31.23.1/31 |
| DC2-XR02 | Hu0/0/0/1 | 172.31.23.2/31 |
| DC3-XR02 | Hu0/0/0/1 | 172.31.23.3/31 |

---

# DC3 ↔ DC1

| Device   | Interface | Address        |
| -------- | --------- | -------------- |
| DC3-XR01 | Hu0/0/0/2 | 172.31.31.0/31 |
| DC1-XR01 | Hu0/0/0/1 | 172.31.31.1/31 |
| DC3-XR02 | Hu0/0/0/2 | 172.31.31.2/31 |
| DC1-XR02 | Hu0/0/0/1 | 172.31.31.3/31 |

---

# 12. Physical Interface Design

All core-facing interfaces operate as:

```text id="2sv78r"
Layer-3 routed interfaces
```

---

## Interface Standards

| Parameter        | Value   |
| ---------------- | ------- |
| Interface Mode   | Routed  |
| Addressing       | /31     |
| MTU              | 9216    |
| Routing Protocol | eBGP    |
| ECMP             | Enabled |

---

# 13. Border Gateway Integration

Border Gateway Leafs provide the routing boundary between:

| Domain          | Protocol     |
| --------------- | ------------ |
| Internal Fabric | IS-IS + EVPN |
| Core/DCI        | eBGP         |

The following interfaces are reserved for XR connectivity:

| Interface | Purpose |
| --------- | ------- |
| Eth1/53   | XR01    |
| Eth1/54   | XR02    |

These interfaces must not participate in:

```text id="e4u2xj"
FABRIC-UNDERLAY IS-IS
```

---

# 14. Route Advertisement Model

## Fabric to Core

Border Leafs advertise:

* summarized DC infrastructure prefixes
* selected EVPN-reachable routes
* internal reachability policies

---

## Core to Fabric

XR routers advertise:

* remote data center reachability
* DCI transport routes
* optional default route policies

---

# 15. High Availability Design

Each Border Gateway Leaf peers with:

* XR01
* XR02

Each XR router peers with:

* remote-site XR01
* remote-site XR02

This provides:

* dual-path resiliency
* ECMP forwarding
* deterministic failover
* transport redundancy

---

# 16. Failure Domain Design

The architecture intentionally isolates:

| Domain       | Failure Scope    |
| ------------ | ---------------- |
| Fabric IS-IS | Internal DC only |
| XR Core      | DCI/WAN only     |

This minimizes:

* control-plane instability propagation
* convergence amplification
* large blast-radius events
* operational coupling

---

# 17. Future Expansion Capability

The architecture supports future implementation of:

| Capability             | Supported |
| ---------------------- | --------- |
| MPLS L3VPN             | Yes       |
| SR-MPLS                | Yes       |
| SRv6                   | Yes       |
| EVPN Interconnect      | Yes       |
| Traffic Engineering    | Yes       |
| QoS transport policies | Yes       |
| WAN federation         | Yes       |

---

# 18. Hardware Platforms

| Layer                | Platform                |
| -------------------- | ----------------------- |
| Core/DCI             | Cisco IOS-XR            |
| Border Gateway Leafs | Cisco Nexus 93180YC-FX3 |

---

# 19. Operational Characteristics

The core network provides:

| Capability                    | Outcome                     |
| ----------------------------- | --------------------------- |
| Dedicated DCI routing         | Stable transport            |
| eBGP policy control           | Deterministic routing       |
| Address hierarchy             | Simplified operations       |
| Dual-router architecture      | High availability           |
| Transport separation          | Operational isolation       |
| Structured transit allocation | Predictable troubleshooting |

---

# 20. Design Summary

The core network architecture establishes a scalable and resilient DCI routing domain interconnecting the multi-data-center VXLAN EVPN fabrics.

The design intentionally separates:

```text id="h8axaf"
internal fabric routing
```

from:

```text id="80j7u4"
external DCI/core routing
```

to maintain deterministic convergence, bounded failure domains, and operational isolation.

The resulting architecture provides a scalable foundation for:

* multi-site EVPN fabrics
* future MPLS/SR transport
* resilient inter-data-center routing
* high-throughput east-west transport
* WAN integration
* AI/HPC-ready transport expansion
