from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, set_ev_cls
from os_ken.ofproto import ofproto_v1_3

from sdn_static_routing.static_paths import ETH_TYPE_ARP, HOSTS, build_all_flows


SWITCH_DPIDS = {
    "s1": 1,
    "s2": 2,
    "s3": 3,
    "s4": 4,
}

DPID_TO_SWITCH = {dpid: switch for switch, dpid in SWITCH_DPIDS.items()}


class StaticRoutingController(app_manager.OSKenApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [
            parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)
        ]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
        )

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, event):
        datapath = event.msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        switch = DPID_TO_SWITCH.get(datapath.id)
        if switch is None:
            return

        # Table miss
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

        # Static flows
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

        # Host rules
        for host in HOSTS.values():
            if host.switch != switch:
                continue

            match = parser.OFPMatch(eth_dst=host.mac)
            actions = [parser.OFPActionOutput(host.port)]

            self.add_flow(datapath, 90, match, actions)
