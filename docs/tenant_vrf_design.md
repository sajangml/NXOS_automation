# VXLAN EVPN Non-Multicast Tenant Overlay Design

# 1. Purpose

This document defines the non-multicast VXLAN EVPN tenant overlay architecture used within the multi-data-centre VXLAN EVPN fabric.

The design provides:

* tenant segmentation
* distributed Anycast Gateway services
* EVPN-based endpoint learning
* ingress-replication-based VXLAN BUM handling
* elimination of multicast dependency for tenant replication

The architecture uses:

```text id="3cgch8"
IS-IS      = underlay unicast routing
BGP EVPN   = overlay MAC/IP control plane
VXLAN      = tenant encapsulation
Ingress Replication = BUM transport mechanism
```

This design is intended for tenants that do not require multicast-assisted VXLAN replication.

---

# 2. Design Principles

| Principle                     | Design Decision          |
| ----------------------------- | ------------------------ |
| Overlay control plane         | MP-BGP EVPN              |
| Tenant isolation              | VRF segmentation         |
| VXLAN replication             | EVPN ingress replication |
| Gateway model                 | Anycast Gateway          |
| Underlay multicast dependency | Not required             |
| Spine role                    | Pure transport           |
| Leaf role                     | VXLAN VTEP edge          |

---

# 3. Architecture Overview

The non-multicast tenant architecture uses EVPN ingress replication for VXLAN BUM traffic handling.

VXLAN BUM traffic is replicated by the ingress VTEP directly toward remote VTEPs learned through the EVPN control plane.

The design eliminates the requirement for:

* PIM Sparse Mode
* multicast transport trees
* RP placement
* MSDP synchronization
* multicast-group VNI mappings

---

# 4. VXLAN BUM Replication Model

## 4.1 Ingress Replication Operation

Ingress replication operates as follows:

```text id="oz4rqo"
Ingress VTEP:
  Replicates BUM traffic toward all remote VTEPs participating in the VNI

Remote VTEPs:
  Receive replicated VXLAN encapsulated traffic directly
```

Remote VTEP membership is dynamically learned through EVPN Type-3 Inclusive Multicast Ethernet Tag routes.

---

# 5. Device Role Definitions

## 5.1 Spine Role

Spines provide:

* underlay IP transit
* ECMP forwarding
* EVPN route reflection transit

Spines do not host:

* tenant VLANs
* tenant SVIs
* VXLAN VNIs
* Anycast Gateway services

---

## 5.2 Leaf / Border Leaf Role

Leafs and Border Leafs provide:

* VXLAN VTEP functionality
* tenant VLAN termination
* ingress replication
* EVPN endpoint learning
* distributed Anycast Gateway services

---

# 6. Tenant Architecture

## 6.1 Tenant Model

Each tenant contains:

* one VRF
* one L3 VNI
* one or more L2 VNIs
* distributed Anycast Gateway services

The architecture uses:

```text id="d5td6j"
L3 VNI = VRF transport
L2 VNI = ingress replication domain
```

---

## 6.2 Tenant Example

| Item             | Value         |
| ---------------- | ------------- |
| Tenant           | TENANT-B      |
| VRF              | TENANT-B      |
| L3 VNI           | 50100         |
| L3 VNI VLAN      | 1099          |
| Application VLAN | 110           |
| L2 VNI           | 30110         |
| Gateway          | 10.20.10.1/24 |

---

# 7. EVPN Overlay Design

## 7.1 EVPN Control Plane

The VXLAN overlay uses MP-BGP EVPN as the distributed control plane.

EVPN provides:

* MAC learning
* IP learning
* endpoint advertisement
* ARP suppression
* distributed Anycast Gateway synchronization
* VTEP membership discovery

---

## 7.2 VNI Behavior

### L3 VNI

L3 VNIs are associated to tenant VRFs only.

Example:

```text id="h7sv65"
member vni 50100 associate-vrf
```

L3 VNIs do not participate in ingress replication.

---

### L2 VNI

L2 VNIs use EVPN ingress replication.

Example:

```text id="hh3qjk"
member vni 30110
  ingress-replication protocol bgp
```

---

# 8. Anycast Gateway Model

The architecture uses distributed Anycast Gateway services across all participating VTEPs.

Each VTEP hosting the VLAN advertises the same:

* gateway MAC address
* default gateway IP address

This provides:

* optimal local forwarding
* workload mobility support
* distributed first-hop routing
* deterministic east-west forwarding

---

# 9. Scaling Characteristics

The ingress replication design simplifies multicast operations by removing multicast dependencies from the fabric.

Benefits include:

* simplified operational model
* elimination of PIM
* elimination of RP placement
* elimination of MSDP
* reduced multicast troubleshooting

Trade-offs include:

* higher BUM replication overhead at ingress VTEPs
* increased bandwidth consumption during broadcast replication
* reduced scalability compared to multicast-assisted VXLAN

---

# 10. Recommended Use Cases

The ingress replication tenant model is recommended for:

* small-to-medium tenant scale
* low BUM environments
* management networks
* infrastructure services
* non-multicast workloads
* operationally simplified deployments

---

# 11. Operational Scope

The ingress replication architecture is used exclusively for:

```text id="kpqce9"
VXLAN BUM replication within EVPN overlay domains
```

The design does not require:

* PIM Sparse Mode
* multicast transport trees
* RP infrastructure
* multicast group allocation
* MSDP synchronization

---

# 12. Final Design Summary

| Function              | Technology               |
| --------------------- | ------------------------ |
| Underlay routing      | IS-IS                    |
| Overlay control plane | MP-BGP EVPN              |
| VXLAN encapsulation   | VXLAN                    |
| Tenant segmentation   | VRF                      |
| Gateway model         | Anycast Gateway          |
| BUM replication       | EVPN ingress replication |
| Multicast dependency  | None                     |

---

# 13. Final Architecture Statement

The non-multicast VXLAN EVPN tenant architecture uses EVPN ingress replication for VXLAN BUM traffic handling.

The design eliminates multicast dependency from the tenant overlay by using EVPN-discovered remote VTEP membership for direct ingress replication.

Tenant L3 VNIs are associated to VRFs, while tenant L2 VNIs use ingress-replication protocol bgp for VXLAN BUM transport.

The architecture provides a simplified operational model suitable for non-multicast workloads and smaller-scale tenant deployments.




# VXLAN EVPN Multicast Underlay and Tenant Overlay Design

# 1. Purpose

This document defines the multicast underlay and tenant overlay architecture for the multi-data-centre VXLAN EVPN fabric deployment across DC1, DC2, and DC3.

The design provides:

* scalable VXLAN BUM replication
* resilient multicast source discovery
* deterministic multicast control-plane behavior
* multi-tenant segmentation
* Anycast Gateway functionality
* inter-data-centre multicast source visibility

The architecture uses:

```text
IS-IS      = underlay unicast routing
PIM-SM     = multicast transport control plane
MSDP       = multicast source-active synchronization
BGP EVPN   = overlay MAC/IP control plane
VXLAN      = tenant encapsulation
```

---

# 2. Design Principles

The multicast architecture follows the following principles:

| Principle                     | Design Decision                    |
| ----------------------------- | ---------------------------------- |
| Underlay routing              | IS-IS Level-2 only                 |
| Multicast mode                | PIM Sparse Mode                    |
| RP resiliency                 | Anycast RP                         |
| RP placement                  | Super-Spine layer only             |
| VXLAN replication             | Multicast-assisted BUM replication |
| Tenant isolation              | VRF-based segmentation             |
| Overlay control plane         | MP-BGP EVPN                        |
| Inter-DC multicast visibility | MSDP between RP domains            |
| Spine role                    | Transit only                       |
| Leaf role                     | VTEP edge only                     |

---

# 3. Multicast Underlay Architecture

## 3.1 PIM Sparse Mode

PIM Sparse Mode (PIM-SM) is deployed within the VXLAN underlay fabric to provide multicast transport trees for VXLAN BUM replication.

PIM is enabled only on routed underlay interfaces participating in multicast forwarding.

The multicast underlay is fully independent from tenant VRFs and tenant routing domains.

---

## 3.2 Anycast RP Architecture

Anycast RP is implemented on the Super-Spine layer within each data centre.

Each data centre contains:

* four unique RP loopbacks
* one shared Anycast RP address

The Anycast RP model provides:

* RP redundancy
* RP load distribution
* multicast resiliency during node failure
* deterministic RP placement

---

# 4. RP Addressing Model

## 4.1 Multicast Address Allocation

```yaml
loopbacks:
  multicast_rp: "10.x.6.0/24"

multicast:
  group_range: "239.1.0.0/16"

  anycast_rp:
    dc1: "10.1.6.254"
    dc2: "10.2.6.254"
    dc3: "10.3.6.254"
```

---

## 4.2 DC1 RP Allocation

| Device      | Unique RP Loopback |    Anycast RP |
| ----------- | -----------------: | ------------: |
| DC1-P1-SS01 |        10.1.6.1/32 | 10.1.6.254/32 |
| DC1-P1-SS02 |        10.1.6.2/32 | 10.1.6.254/32 |
| DC1-P2-SS01 |        10.1.6.3/32 | 10.1.6.254/32 |
| DC1-P2-SS02 |        10.1.6.4/32 | 10.1.6.254/32 |

The same addressing pattern is applied to DC2 and DC3.

---

# 5. MSDP Architecture

## 5.1 MSDP Purpose

MSDP is used to synchronize multicast source-active (SA) state between RP domains.

Because multicast forwarding is shared across DC1, DC2, and DC3:

```text
Inter-DC MSDP synchronization is required.
```

MSDP enables:

* multicast source discovery between data centres
* inter-DC ASM multicast forwarding
* Anycast RP source synchronization
* RP redundancy consistency

---

## 5.2 MSDP Design Model

The MSDP architecture uses:

```text
Intra-DC MSDP:
  Full mesh between all local Super-Spine RP nodes

Inter-DC MSDP:
  Dedicated inter-DC MSDP speaker per DC
```

This model minimizes MSDP session scale while preserving inter-DC multicast visibility.

---

## 5.3 Inter-DC MSDP Speakers

| DC  | Inter-DC MSDP Speaker |
| --- | --------------------- |
| DC1 | DC1-P1-SS01           |
| DC2 | DC2-P1-SS01           |
| DC3 | DC3-P1-SS01           |

Only designated inter-DC RP speakers establish cross-DC MSDP sessions.

---

# 6. Device Role Definitions

## 6.1 Super-Spine Role

Super-Spines perform:

* Anycast RP hosting
* MSDP source synchronization
* PIM rendezvous functionality
* multicast control-plane services

Super-Spines do not host tenant VLANs, tenant SVIs, or VXLAN VNIs.

---

## 6.2 Spine Role

Spines provide:

* IS-IS transit forwarding
* PIM multicast transit forwarding

Spines do not participate in:

* RP functionality
* MSDP
* tenant segmentation
* VXLAN VNIs
* Anycast Gateway services

---

## 6.3 Leaf / Border Leaf Role

Leafs and Border Leafs provide:

* VXLAN VTEP functionality
* tenant VLAN termination
* Anycast Gateway services
* VXLAN encapsulation
* EVPN endpoint learning

Leafs participate as multicast edge routers only.

---

# 7. PIM Interface Policy

PIM Sparse Mode must be enabled only on underlay routed interfaces participating in multicast forwarding.

## 7.1 PIM Enabled Interfaces

| Interface Type                   | PIM     |
| -------------------------------- | ------- |
| Underlay routed links            | Enabled |
| RP loopbacks                     | Enabled |
| Spine uplinks                    | Enabled |
| Leaf uplinks                     | Enabled |
| Inter-DC multicast transit links | Enabled |

---

## 7.2 PIM Disabled Interfaces

| Interface Type           | PIM      |
| ------------------------ | -------- |
| Server-facing interfaces | Disabled |
| Tenant SVIs              | Disabled |
| L3 VNI SVIs              | Disabled |
| NVE interfaces           | Disabled |
| Access VLAN interfaces   | Disabled |

---

# 8. VXLAN Tenant Architecture

## 8.1 Tenant Design Model

Each tenant uses:

* one VRF
* one L3 VNI
* one or more L2 VNIs
* Anycast Gateway services

The architecture uses:

```text
L3 VNI = VRF transport only
L2 VNI = multicast-assisted BUM replication
```

---

## 8.2 Tenant Example

| Item            | Value         |
| --------------- | ------------- |
| Tenant          | TENANT-A      |
| VRF             | TENANT-A      |
| L3 VNI          | 50000         |
| L3 VNI VLAN     | 999           |
| Web VLAN        | 10            |
| Web L2 VNI      | 30010         |
| Gateway         | 10.10.10.1/24 |
| Multicast Group | 239.1.1.10    |

---

# 9. Multicast Group Allocation Strategy

The design uses multicast-group aggregation to reduce multicast state scale.

The following model is recommended:

```text
One multicast group per tenant group set
NOT one multicast group per VLAN
```

Example:

| Tenant   | VNIs        | Multicast Group |
| -------- | ----------- | --------------- |
| TENANT-A | 30010–30050 | 239.1.1.10      |
| TENANT-B | 30100–30150 | 239.1.2.10      |
| TENANT-C | 30200–30250 | 239.1.3.10      |

This reduces:

* RP multicast state scale
* (*,G) growth
* (S,G) explosion
* multicast convergence overhead

---

# 10. EVPN Overlay Architecture

The EVPN overlay uses MP-BGP EVPN as the VXLAN control plane.

EVPN provides:

* MAC address advertisement
* IP endpoint advertisement
* ARP suppression
* distributed Anycast Gateway learning
* endpoint mobility handling

---

# 11. Overlay Routing Model

## 11.1 L3 VNI Behavior

L3 VNIs are associated with tenant VRFs only.

L3 VNIs do not require multicast-group assignment.

Example:

```text
member vni 50000 associate-vrf
```

---

## 11.2 L2 VNI Behavior

L2 VNIs use multicast-assisted BUM replication.

Example:

```text
member vni 30010
  mcast-group 239.1.1.10
```

---

# 12. Operational Scope

The multicast underlay is used exclusively for:

```text
VXLAN BUM transport replication
```

The multicast architecture is not used for:

* tenant multicast gateway services
* multicast VRF leaking
* multicast tenant route exchange

unless explicitly enabled in future phases.

---

# 13. Final Design Summary

| Function               | Technology               |
| ---------------------- | ------------------------ |
| Underlay routing       | IS-IS                    |
| Multicast transport    | PIM-SM                   |
| RP redundancy          | Anycast RP               |
| Source synchronization | MSDP                     |
| Overlay control plane  | BGP EVPN                 |
| Tenant encapsulation   | VXLAN                    |
| Tenant segmentation    | VRF                      |
| Gateway model          | Anycast Gateway          |
| BUM replication        | Multicast-assisted VXLAN |

---

# 14. Final Architecture Statement

The VXLAN EVPN fabric uses a multicast-assisted VXLAN underlay architecture based on PIM Sparse Mode with Anycast RP hosted on the Super-Spine layer.

MSDP is deployed between Super-Spine RP nodes to synchronize multicast source-active state within and across DC1, DC2, and DC3.

The design provides resilient inter-data-centre multicast source visibility while maintaining deterministic RP placement and scalable VXLAN BUM replication.

Tenant L2 VNIs are mapped to multicast groups for BUM transport, while L3 VNIs remain VRF-associated and do not participate in multicast group mapping.




