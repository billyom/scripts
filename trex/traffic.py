from trex_stl_lib.api import *

class STLImix(object):

    def __init__ (self):
        # default IP range
        self.ip_range = {'src': {'start': "16.0.0.1", 'end': "16.0.0.13"},
                         'dst': {'start': "48.0.0.1",  'end': "48.0.0.1"}}

        # default IMIX properties
        self.imix_table = [ {'size': 60,   'pps': 28,  'isg':0 },
                            {'size': 590,  'pps': 16,  'isg':0.1 },
                            {'size': 1514, 'pps': 4,   'isg':0.2 } ]

    def create_stream (self, size, pps, isg, vm , pg_id):
        # Create base packet and pad it to size
        base_pkt = Ether()/IP()/UDP()
        pad = max(0, size - len(base_pkt)) * 'x'

        pkt = STLPktBuilder(pkt = base_pkt/pad,
                            vm = vm)

        traffic_stream = STLStream(isg = isg,
                         packet = pkt,
                         mode = STLTXCont(pps = pps))

        latency_stream = STLStream(isg = isg,
                         packet = pkt,
                         mode = STLTXCont(pps = 100), #setting 1000 give "factor must be positive" - wtf
                         flow_stats=STLFlowLatencyStats(pg_id = pg_id))
        return [traffic_stream, latency_stream]


    def get_streams (self, direction, port_id):

        direction=0

        if direction == 0:
            src = self.ip_range['src']
            dst = self.ip_range['dst']
        else:
            src = self.ip_range['dst']
            dst = self.ip_range['src']

        #ensure diff packets on diff ports to avoid EMC thrashing.
        sport_range = 17
        sport_min = 1 + sport_range * port_id
        sport_max = sport_min + sport_range - 1
        #print "sport: %d - %d" % (sport_min, sport_max)

        # construct the base packet for the profile
    	vm = STLScVmRaw( [ STLVmFlowVar(name="mac_dst",
                                    min_value=1,
                                    max_value=10,
                                    size=1, op="inc",step=1),
                       STLVmWrFlowVar(fv_name="mac_dst",
                                          pkt_offset= 5),
                       STLVmFixChecksumHw(l3_offset = "IP",
			 l4_offset = "UDP",
			 l4_type  = CTRexVmInsFixHwCs.L4_TYPE_UDP )
                        ]
                       )
        """
        vm = STLVM()

        # define vars
        vm.var(name="src",min_value=src['start'],max_value=src['end'],size=4,op="inc")
        vm.var(name="dst",min_value=dst['start'],max_value=dst['end'],size=4,op="inc")
        vm.var(name="srcport",min_value=sport_min,max_value=sport_max,size=2,op="inc")

        # write them
        vm.write(fv_name="src",pkt_offset= "IP.src")
        vm.write(fv_name="dst",pkt_offset= "IP.dst")
        vm.write(fv_name="srcport",pkt_offset= "UDP.sport")

        # fix checksum
        #vm.fix_chksum() #with this only the very first pkt has valid udp csum
	#fix_cksum_hw voodoo from syn_attack_fix_cs_hw.py - valid udp sum fro all pkts \o/
        vm.fix_chksum_hw(l3_offset="IP",
			 l4_offset = "UDP",
			 l4_type  = CTRexVmInsFixHwCs.L4_TYPE_UDP )
        """

        # create imix streams
        #return [self.create_stream(x['size'], x['pps'],x['isg'] , vm) for x in self.imix_table]
        return self.create_stream(230, 1, 0, vm, port_id+10)


# dynamic load - used for trex console or simulator
def register():
    return STLImix()


