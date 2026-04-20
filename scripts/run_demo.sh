#!/usr/bin/env bash
set -euo pipefail

echo "Terminal 1:"
echo "  ryu-manager sdn_static_routing.ryu_controller"
echo
echo "Terminal 2:"
echo "  sudo python3 topology/static_routing_topology.py"
echo
echo "Then run inside the Mininet CLI:"
echo "  pingall"
echo "  h1 traceroute h2"
echo
echo "Inspect switch flow rules from another terminal:"
echo "  sudo ovs-ofctl -O OpenFlow13 dump-flows s1"

