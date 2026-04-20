# Static Routing Using an SDN Controller

## Aim

The aim of this project is to implement static routing in a software-defined network by installing flow rules from a controller. The controller defines fixed forwarding paths and pushes OpenFlow entries to switches so packets follow the selected route without relying on traditional distributed routing protocols.

## Tools Used

- Ryu SDN controller
- Mininet network emulator
- Open vSwitch with OpenFlow 1.3
- Python unit tests for route regression

## Network Design

The network contains four OpenFlow switches and four hosts:

```text
          h3
          |
h1 -- s1 -- s2 -- s4 -- h2
      |           |
      s3 --------+
      |
      h4
```

There are two possible physical paths between `h1` and `h2`:

- `s1 -> s2 -> s4`
- `s1 -> s3 -> s4`

The controller intentionally selects `s1 -> s2 -> s4` as the static route. This demonstrates SDN behavior because forwarding is determined by controller-installed rules rather than automatic switch learning.

## Static Routing Table

| Source and destination | Controller-selected path |
| --- | --- |
| h1 <-> h2 | s1 -> s2 -> s4 |
| h1 <-> h3 | s1 -> s2 |
| h1 <-> h4 | s1 -> s3 |
| h2 <-> h3 | s4 -> s2 |
| h2 <-> h4 | s4 -> s3 |
| h3 <-> h4 | s2 -> s1 -> s3 |

## Flow Rule Behavior

For each host pair, the controller installs both ARP and IPv4 rules. Each rule matches:

- input port
- Ethernet type
- source IP address
- destination IP address

For ARP traffic, the controller matches `arp_spa` and `arp_tpa`. For IPv4 traffic, it matches `ipv4_src` and `ipv4_dst`.

For `h1 -> h2`, the installed forwarding behavior is:

| Switch | Match input | Output port | Next hop |
| --- | --- | --- | --- |
| s1 | s1-eth1 | s1-eth2 | s2 |
| s2 | s2-eth1 | s2-eth2 | s4 |
| s4 | s4-eth1 | s4-eth3 | h2 |

The reverse direction `h2 -> h1` uses the same selected path in reverse:

| Switch | Match input | Output port | Next hop |
| --- | --- | --- | --- |
| s4 | s4-eth3 | s4-eth1 | s2 |
| s2 | s2-eth2 | s2-eth1 | s1 |
| s1 | s1-eth2 | s1-eth1 | h1 |

## Validation

Packet delivery is validated in Mininet using:

```bash
pingall
h1 ping -c 3 h2
```

Successful pings confirm that ARP resolution and IPv4 forwarding work across the installed static routes. Flow entries can be inspected with:

```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
sudo ovs-ofctl -O OpenFlow13 dump-flows s2
sudo ovs-ofctl -O OpenFlow13 dump-flows s4
```

The expected result is that `h1 -> h2` traffic leaves `s1` through port 2, leaves `s2` through port 2, and leaves `s4` through port 3.

## Regression Test

The project includes a regression test in `tests/test_static_paths.py`. The main test locks the required route:

```text
h1 -> h2 = s1 -> s2 -> s4
```

If the route is accidentally changed to another path, the test fails. This ensures the selected static path remains unchanged after rule reinstall or code updates.

Run the test with:

```bash
python3 -m unittest discover -s tests
```

## Conclusion

The project demonstrates static routing using an SDN controller. The controller defines deterministic paths, installs OpenFlow rules manually, supports ARP and IPv4 forwarding, validates packet delivery in Mininet, and includes regression coverage to protect the required path behavior.

