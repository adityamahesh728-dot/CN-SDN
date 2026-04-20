import unittest

from sdn_static_routing.static_paths import (
    ETH_TYPE_ARP,
    ETH_TYPE_IPV4,
    HOSTS,
    build_all_flows,
    build_unidirectional_flows,
    get_route,
)


class StaticPathTests(unittest.TestCase):
    def test_h1_to_h2_path_is_regression_locked(self):
        self.assertEqual(get_route("h1", "h2"), ["s1", "s2", "s4"])

    def test_reverse_path_uses_same_switches_in_reverse_order(self):
        self.assertEqual(get_route("h2", "h1"), ["s4", "s2", "s1"])

    def test_h1_to_h2_flow_ports_match_documented_route(self):
        rules = build_unidirectional_flows("h1", "h2", ETH_TYPE_IPV4)
        self.assertEqual(
            [(rule.switch, rule.in_port, rule.out_port) for rule in rules],
            [("s1", 1, 2), ("s2", 1, 2), ("s4", 1, 3)],
        )

    def test_all_rules_include_arp_and_ipv4(self):
        rules = build_all_flows()
        eth_types = {rule.eth_type for rule in rules}
        self.assertEqual(eth_types, {ETH_TYPE_ARP, ETH_TYPE_IPV4})

    def test_every_rule_has_known_hosts_and_non_looping_ports(self):
        valid_ips = {host.ip for host in HOSTS.values()}
        for rule in build_all_flows():
            self.assertIn(rule.src_ip, valid_ips)
            self.assertIn(rule.dst_ip, valid_ips)
            self.assertNotEqual(rule.in_port, rule.out_port)


if __name__ == "__main__":
    unittest.main()

