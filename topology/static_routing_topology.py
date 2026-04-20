"""Mininet topology for validating static SDN routing.

Run after starting the controller:
    sudo python3 topology/static_routing_topology.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.util import dumpNodeConnections

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sdn_static_routing.static_paths import HOSTS


class StaticRoutingTopo(Topo):
    """Four-switch topology with two available core paths."""

    def build(self):
        switches = {
            "s1": self.addSwitch("s1", protocols="OpenFlow13", dpid="0000000000000001"),
            "s2": self.addSwitch("s2", protocols="OpenFlow13", dpid="0000000000000002"),
            "s3": self.addSwitch("s3", protocols="OpenFlow13", dpid="0000000000000003"),
            "s4": self.addSwitch("s4", protocols="OpenFlow13", dpid="0000000000000004"),
        }

        for host in HOSTS.values():
            mininet_host = self.addHost(host.name, ip=f"{host.ip}/24", mac=host.mac)
            self.addLink(mininet_host, switches[host.switch], port2=host.port)

        self.addLink(switches["s1"], switches["s2"], port1=2, port2=1)
        self.addLink(switches["s1"], switches["s3"], port1=3, port2=1)
        self.addLink(switches["s2"], switches["s4"], port1=2, port2=1)
        self.addLink(switches["s3"], switches["s4"], port1=2, port2=2)


def run():
    topo = StaticRoutingTopo()
    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=False,
        autoStaticArp=True,
    )
    net.addController(
        "c0",
        controller=RemoteController,
        ip="127.0.0.1",
        port=6633,
        protocols="OpenFlow13",
    )

    net.start()
    print("\nNode connections:")
    dumpNodeConnections(net.hosts)
    print("\nValidating packet delivery with pingAll:")
    loss = net.pingAll()
    print(f"\nPacket loss: {loss}%")
    print("\nUse 'ovs-ofctl -O OpenFlow13 dump-flows s1' in another terminal to inspect rules.")
    CLI(net)
    net.stop()


if __name__ == "__main__":
    run()
