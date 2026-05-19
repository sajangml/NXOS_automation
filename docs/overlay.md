# VXLAN EVPN Overlay Design Artefact

# 1. Purpose

This document defines the VXLAN EVPN overlay architecture deployed on top of the IS-IS routed underlay fabric across:

* DC1
* DC2
* DC3

The overlay provides:

* Layer-2 extension across the fabric
* distributed Anycast Gateway services
* scalable MAC/IP learning
* tenant segmentation
* multi-pod VXLAN transport
* EVPN-based control-plane learning
* scalable BGP Route Reflection hierarchy

The overlay operates independently from the underlay routing domain.

---

# 2. Scope

This document covers:

* BGP EVPN overlay architecture
* Route Reflector hierarchy
* VTEP design
* NVE interface model
* EVPN control-plane peering
* overlay ASN allocation
* route reflection hierarchy
* loopback peering model

This document excludes:

* tenant VRF definitions
* VLAN-to-VNI mappings
* Anycast Gateway configuration
* external WAN/DCI route leaking
* firewall services
* Internet edge connectivity

---

# 3. Overlay Architecture

The VXLAN EVPN overlay operates on top of the routed IS-IS underlay.

## Overlay Hierarchy

```text id="5v76oi"
Leaf VTEPs
    ↓
Spine Route Reflectors
    ↓
Super-Spine Route Reflectors
```

---

# 4. Overlay Design Model

## Leaf Switches

Leaf switches provide:

* VXLAN Tunnel Endpoints (VTEPs)
* tenant VLAN termination
* Anycast Gateway functionality
* VXLAN encapsulation/decapsulation
* EVPN route advertisement

---

## Spine Switches

Spine switches operate as:

```text id="2xwx1k"
EVPN Route Reflectors
```

Spines do not:

* terminate VXLAN tunnels
* host tenant VRFs
* host Anycast Gateway SVIs

---

## Super-Spines

Super-Spines provide:

```text id="0olx8w"
top-level hierarchical EVPN route reflection
```

between pods.

Super-Spines do not:

* terminate VXLAN tunnels
* host tenant VRFs
* host Anycast Gateway SVIs

---

# 5. Overlay Routing Model

The overlay uses:

```text id="e0g85i"
MP-BGP EVPN
```

with:

```text id="n8hmyi"
iBGP EVPN
```

inside each data center fabric.

---

# 6. Overlay ASN Allocation

Each DC operates an independent EVPN ASN.

| Data Center | Overlay ASN |
| ----------- | ----------- |
| DC1         | 65101       |
| DC2         | 65102       |
| DC3         | 65103       |

---

# 7. Underlay Dependency

The EVPN overlay relies on the IS-IS underlay for:

* loopback reachability
* ECMP transport
* VXLAN packet forwarding
* routed transport convergence

The overlay forms BGP sessions using:

```text id="8x6nlv"
Loopback0
```

interfaces advertised via IS-IS.

---

# 8. Loopback Design

## Loopback0 Purpose

Loopback0 acts as:

* BGP router-id
* VTEP source interface
* EVPN peering endpoint
* stable overlay endpoint

---

## Loopback Allocation

| Device Type | Address Range |
| ----------- | ------------- |
| Spine       | 10.x.1.0/24   |
| Leaf        | 10.x.2.0/24   |
| Super-Spine | 10.x.3.0/24   |

---

# 9. Route Reflection Hierarchy

The overlay uses hierarchical route reflection.

---

## 9.1 Leaf-to-Spine Relationship

Leafs peer with:

* SP01
* SP02
* SP03
* SP04

The Leafs are:

```text id="gx1hgu"
Route Reflector Clients
```

of the Spines.

---

## 9.2 Spine-to-Super-Spine Relationship

Spines peer with:

* SS01
* SS02

The Spines are:

```text id="nh4qko"
Route Reflector Clients
```

of the Super-Spines.

---

## 9.3 Super-Spine Relationship

Super-Spines peer with:

* remote-pod Super-Spines

using standard iBGP EVPN peerings.

Super-Spines are not RR clients of each other.

---

# 10. EVPN Address Family

All overlay peerings use:

```text id="f5uz56"
address-family l2vpn evpn
```

---

# 11. Community Handling

All EVPN peers must advertise:

```text id="4mp7p7"
send-community both
```

or:

```text id="ekmndw"
send-community extended
```

---

## Rationale

EVPN requires extended communities for:

* Route Targets
* Router MAC advertisements
* EVPN route import/export policies

---

# 12. Route Target Retention

Spines and Super-Spines must use:

```text id="5nqns2"
retain route-target all
```

---

## Rationale

Because these devices do not locally host tenant VRFs, they would otherwise discard EVPN routes.

The command ensures:

* EVPN routes remain in memory
* reflected routes propagate correctly
* full overlay reachability is maintained

---

# 13. VTEP Design

Only Leafs and Border Gateway Leafs operate as VTEPs.

---

## NVE Interface Model

Each VTEP uses:

```text id="x29g5r"
interface nve1
```

with:

| Parameter        | Value     |
| ---------------- | --------- |
| Source Interface | Loopback0 |
| Control Plane    | BGP EVPN  |
| Encapsulation    | VXLAN     |

---

# 14. Overlay Feature Requirements

## Leaf / BGW Leafs

Required features:

```cisco
feature bgp
feature nv overlay
nv overlay evpn
```

---

## Spine / Super-Spine

Required features:

```cisco
feature bgp
```

Spines and Super-Spines do not require:

```text id="azw3oi"
feature nv overlay
```

because they do not terminate VXLAN tunnels.

---

# 15. Leaf Overlay Peering Model

Each Leaf peers with:

| Peer Type | Quantity |
| --------- | -------: |
| Spine RRs |        4 |

Example:

| Local Device | Peers     |
| ------------ | --------- |
| LF01         | SP01–SP04 |

---

# 16. Spine Overlay Peering Model

Each Spine peers with:

| Peer Type    | Quantity |
| ------------ | -------: |
| Leaf Clients |        8 |
| Super-Spines |        2 |

---

# 17. Super-Spine Overlay Peering Model

Each Super-Spine peers with:

| Peer Type           | Quantity |
| ------------------- | -------: |
| Spine Clients       |        8 |
| Remote Super-Spines | Variable |

---

# 18. Overlay Failure Domains

The hierarchical RR design minimizes:

* excessive BGP peering
* full-mesh scaling problems
* control-plane churn
* overlay convergence amplification

---

# 19. Overlay Scaling Benefits

The hierarchical EVPN design provides:

| Capability            | Outcome                 |
| --------------------- | ----------------------- |
| Hierarchical RR       | Scalable control plane  |
| Reduced BGP sessions  | Lower memory/CPU        |
| Pod isolation         | Operational simplicity  |
| Structured reflection | Predictable convergence |
| Loopback peering      | Stable transport        |
| ECMP underlay         | High throughput         |

---

# 20. Overlay Control Plane Flow

## Route Advertisement Path

```text id="iwk4d8"
Leaf VTEP
    →
Spine RR
    →
Super-Spine RR
    →
Remote Spine RR
    →
Remote Leaf VTEP
```

---

# 21. Hardware Roles

| Device Role | Function              |
| ----------- | --------------------- |
| Leaf        | VTEP                  |
| Border Leaf | VTEP + Border Gateway |
| Spine       | EVPN RR               |
| Super-Spine | Hierarchical EVPN RR  |

---

# 22. Design Constraints

## Important Operational Rules

### Only Leafs terminate VXLAN tunnels

Spines and Super-Spines must not:

* host tenant SVIs
* host Anycast Gateway
* configure NVE interfaces
* terminate VXLAN encapsulation

---

### Overlay sessions must use Loopback0

All EVPN peerings use:

```text id="grwrze"
update-source loopback0
```

This ensures:

* stable TCP sessions
* ECMP underlay transport
* independence from physical interfaces

---

# 23. Future Expansion Capability

The overlay architecture supports:

| Capability                  | Supported |
| --------------------------- | --------- |
| Multi-Pod EVPN              | Yes       |
| Multi-Site EVPN             | Yes       |
| EVPN Type-5 Routing         | Yes       |
| Distributed Anycast Gateway | Yes       |
| Tenant VRFs                 | Yes       |
| VRF route leaking           | Yes       |
| DCI extension               | Yes       |
| AI/HPC east-west scaling    | Yes       |

---

# 24. Operational Characteristics

The resulting overlay provides:

| Capability           | Outcome                    |
| -------------------- | -------------------------- |
| MP-BGP EVPN          | Control-plane MAC learning |
| VXLAN transport      | Layer-2 extension          |
| Hierarchical RR      | Scalable peering           |
| Loopback peering     | Stable sessions            |
| Structured hierarchy | Predictable convergence    |
| RR route retention   | Full EVPN visibility       |

---

# 25. Design Summary

The VXLAN EVPN overlay architecture establishes a scalable and resilient multi-pod overlay network operating on top of the routed IS-IS underlay.

The design intentionally separates:

to maintain deterministic operations, scalable convergence, and operational separation.

The resulting architecture provides a production-grade EVPN fabric suitable for:

* multi-tenant virtualization
* Kubernetes platforms
* east-west heavy workloads
* scalable Layer-2 extension
* Anycast Gateway services
* future multi-site EVPN expansion
* AI/HPC-ready transport scaling
