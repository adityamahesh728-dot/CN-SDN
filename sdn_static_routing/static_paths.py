"""Static route and flow-rule definitions for the SDN mini project.

The controller imports this module to install OpenFlow rules. Tests import the
same definitions so a route change is caught before the controller is run.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations


ETH_TYPE_ARP = 0x0806
ETH_TYPE_IPV4 = 0x0800


@dataclass(frozen=True)
class Host:
    name: str
    ip: str
    mac: str
    switch: str
    port: int


@dataclass(frozen=True)
class FlowRule:
    switch: str
    in_port: int
    out_port: int
    src_ip: str
    dst_ip: str
    eth_type: int


HOSTS: dict[str, Host] = {
    "h1": Host("h1", "10.0.0.1", "00:00:00:00:00:01", "s1", 1),
    "h2": Host("h2", "10.0.0.2", "00:00:00:00:00:02", "s4", 3),
    "h3": Host("h3", "10.0.0.3", "00:00:00:00:00:03", "s2", 3),
    "h4": Host("h4", "10.0.0.4", "00:00:00:00:00:04", "s3", 3),
}


# Link ports as seen from the source switch.
LINK_PORTS: dict[tuple[str, str], int] = {
    ("s1", "s2"): 2,
    ("s2", "s1"): 1,
    ("s1", "s3"): 3,
    ("s3", "s1"): 1,
    ("s2", "s4"): 2,
    ("s4", "s2"): 1,
    ("s3", "s4"): 2,
    ("s4", "s3"): 2,
}


# Static controller-selected paths. These are intentionally fixed, even when
# another route also exists, so the behavior is deterministic for regression.
ROUTES: dict[tuple[str, str], list[str]] = {
    ("h1", "h2"): ["s1", "s2", "s4"],
    ("h1", "h3"): ["s1", "s2"],
    ("h1", "h4"): ["s1", "s3"],
    ("h2", "h3"): ["s4", "s2"],
    ("h2", "h4"): ["s4", "s3"],
    ("h3", "h4"): ["s2", "s1", "s3"],
}


def get_route(src_host: str, dst_host: str) -> list[str]:
    """Return the static switch path between two hosts."""
    if src_host == dst_host:
        raise ValueError("source and destination hosts must be different")

    direct = ROUTES.get((src_host, dst_host))
    if direct is not None:
        return list(direct)

    reverse = ROUTES.get((dst_host, src_host))
    if reverse is not None:
        return list(reversed(reverse))

    raise KeyError(f"no static route for {src_host} -> {dst_host}")


def all_host_pairs() -> list[tuple[str, str]]:
    """Return each unordered host pair once."""
    return list(combinations(sorted(HOSTS), 2))


def build_unidirectional_flows(
    src_host: str,
    dst_host: str,
    eth_type: int = ETH_TYPE_IPV4,
) -> list[FlowRule]:
    """Build switch flow rules for one host-to-host direction."""
    src = HOSTS[src_host]
    dst = HOSTS[dst_host]
    route = get_route(src_host, dst_host)
    rules: list[FlowRule] = []

    for index, switch in enumerate(route):
        previous_hop = src.name if index == 0 else route[index - 1]
        next_hop = dst.name if index == len(route) - 1 else route[index + 1]

        in_port = src.port if previous_hop == src.name else LINK_PORTS[(switch, previous_hop)]
        out_port = dst.port if next_hop == dst.name else LINK_PORTS[(switch, next_hop)]

        rules.append(
            FlowRule(
                switch=switch,
                in_port=in_port,
                out_port=out_port,
                src_ip=src.ip,
                dst_ip=dst.ip,
                eth_type=eth_type,
            )
        )

    return rules


def build_all_flows() -> list[FlowRule]:
    """Build ARP and IPv4 rules for every static host pair, both directions."""
    rules: list[FlowRule] = []
    for src_host, dst_host in all_host_pairs():
        for eth_type in (ETH_TYPE_ARP, ETH_TYPE_IPV4):
            rules.extend(build_unidirectional_flows(src_host, dst_host, eth_type))
            rules.extend(build_unidirectional_flows(dst_host, src_host, eth_type))
    return rules

