"""Ryu controller that installs static OpenFlow paths.

Run with:
    ryu-manager sdn_static_routing.ryu_controller
"""

from __future__ import annotations

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3

from sdn_static_routing.static_paths import ETH_TYPE_ARP, HOSTS, build_all_flows


SWITCH_DPIDS = {
    "s1": 1,
    "s2": 2,
    "s3": 3,
    "s4": 4,
}

DPID_TO_SWITCH = {dpid: switch for switch, dpid in SWITCH_DPIDS.items()}


class StaticRoutingController(app_manager.RyuApp):
    """Install fixed routes when each switch connects."""

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        instructions = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions,
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, event):
        datapath = event.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        switch = DPID_TO_SWITCH.get(datapath.id)
        if switch is None:
            self.logger.warning("Ignoring unknown datapath id %s", datapath.id)
            return

        # Keep packets off the controller except for table misses used during lab debugging.
        table_miss_match = parser.OFPMatch()
        table_miss_actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, table_miss_match, table_miss_actions)

        installed = 0
        for rule in build_all_flows():
            if rule.switch != switch:
                continue

            actions = [parser.OFPActionOutput(rule.out_port)]
            if rule.eth_type == ETH_TYPE_ARP:
                match = parser.OFPMatch(
                    in_port=rule.in_port,
                    eth_type=rule.eth_type,
                    arp_spa=rule.src_ip,
                    arp_tpa=rule.dst_ip,
                )
            else:
                match = parser.OFPMatch(
                    in_port=rule.in_port,
                    eth_type=rule.eth_type,
                    ipv4_src=rule.src_ip,
                    ipv4_dst=rule.dst_ip,
                )

            self.add_flow(datapath, 100, match, actions)
            installed += 1

        for host in HOSTS.values():
            if host.switch != switch:
                continue
            match = parser.OFPMatch(eth_dst=host.mac)
            actions = [parser.OFPActionOutput(host.port)]
            self.add_flow(datapath, 90, match, actions)
            installed += 1

        self.logger.info("Installed %s static flow rules on %s", installed, switch)

