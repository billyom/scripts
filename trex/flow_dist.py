#!/usr/bin/env python

# Create l

from trex_stl_lib.api import *

import time
import cmd
import re

import itertools
import random
import numbers
import pprint

def pro_rate (total, ratios):
    """
    Split a total in a ratio.

    >>> pro_rate (100, [85, 11, 3, 1])
    [85, 11, 3, 1]

    >>> pro_rate (2, [50, 50])
    [1, 1]

    >>> pro_rate (106, [41, 31, 21, 11])
    [41, 31, 21, 11]

    """
    sum_ratios = sum(ratios)
    return [(total*ratio)/sum_ratios for ratio in ratios]

primes_and_one = [1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
127, 131, 137, 139, 149, 151, 157, 163, 167, 173,
179, 181, 191, 193, 197, 199, 211, 223, 227, 229,
233, 239, 241, 251, 257, 263, 269, 271, 277, 281,
283, 293, 307, 311, 313, 317, 331, 337, 347, 349,
353, 359, 367, 373, 379, 383, 389, 397, 401, 409,
419, 421, 431, 433, 439, 443, 449, 457, 461, 463,
467, 479, 487, 491, 499, 503, 509, 521, 523, 541,
547, 557, 563, 569, 571, 577, 587, 593, 599, 601,
607, 613, 617, 619, 631, 641, 643, 647, 653, 659,
661, 673, 677, 683, 691, 701, 709, 719, 727, 733,
739, 743, 751, 757, 761, 769, 773, 787, 797, 809,
811, 821, 823, 827, 829, 839, 853, 857, 859, 863,
877, 881, 883, 887, 907, 911, 919, 929, 937, 941,
947, 953, 967, 971, 977, 983, 991, 997, 1009, 1013,
1019, 1021, 1031, 1033, 1039, 1049, 1051, 1061, 1063, 1069,
1087, 1091, 1093, 1097, 1103, 1109, 1117, 1123, 1129, 1151,
1153, 1163, 1171, 1181, 1187, 1193, 1201, 1213, 1217, 1223]


from operator import mul

def n_as_product_of_primes (n, num_primes):
    """
    >>> n_as_product_of_primes (200, 4)
    ([1, 1, 1, 199], 1)

    >>> n_as_product_of_primes (1, 4)
    ([1, 1, 1, 1], 0)

    >>> n_as_product_of_primes (30, 4)
    ([1, 2, 3, 5], 0)

    >>> n_as_product_of_primes (1000000, 4)
    ([2, 31, 127, 127], 2)
    """

    best_diff = None
    best_combo = None

    for combo in itertools.combinations_with_replacement(primes_and_one, num_primes):
        product = reduce(mul, combo, 1)
        diff = abs(product - n)
        if diff < best_diff or not best_diff:
            best_diff = diff
            best_combo = combo #print combo, product, diff
        if best_diff == 0:
            break

    best_combo = list(best_combo)
    best_combo.sort()              # ensure output is stable for doctests
    return best_combo, best_diff


def column_sum (lofl):
    """
    DEPRECATED - use [sum (x) for x in zip(list1, list2, ...)]

    For a list of lists of numbers return a list whose ith element are the sum
    of the ith elements of each of the lists.

    >>> column_sum ([[2, 3, 5, 7], [7, 5, 3, 2]])
    [9, 8, 8, 9]

    >>> column_sum ([[2, 3, 5, 7], [7, 5, 3, 2], [1, 1, 1, 1]])
    [10, 9, 9, 10]

    >>> column_sum ([[2, 3], [7, 2], [1, 8]])
    [10, 13]
    """
    #print lofl
    result = []
    l_len = len(lofl[0])
    for i in range(l_len):
        sum = 0
        for l in lofl:
            if len(l) != l_len:
                raise Exception ("All lists need to be same length")
            if not isinstance (l[i], numbers.Number):
                raise Exception ("All list elems need to be a number")
            sum += l[i]
        result.append(sum)
    return result


def tuple_spans_to_ranges (tuple_spans, span_base):
    """
    tuple_spans: a list of lists. Each element indicates in each list the desired *length of the range* for that dimension in that tuple.
    span_base: the range_starts to be used in the returned ranges for the first tuple.

    >>> tuple_spans_to_ranges ( [[5, 3, 1, 13], [13, 5, 3, 1], [3, 5, 13, 1]], [0, 0, 0, 0])
    [[(0, 4), (0, 2), (0, 0), (0, 12)], [(5, 17), (3, 7), (1, 3), (13, 13)], [(18, 20), (8, 12), (4, 16), (14, 14)]]
    """

    l_of_ranges = [] #[[(range_first, range_last), ...], [...], ...]
    cuml = span_base[:]
    for curr in tuple_spans:
        range_end = [sum (x) for x in zip(cuml, curr)]
        range_end = [x-1 for x in range_end]
        l_of_ranges.append(zip(cuml, range_end))
        cuml = [sum (x) for x in zip(cuml, curr)]

    return l_of_ranges

def ip_inc (ip_addr_tuple, inc):
    """
    >>> ip_inc ((0, 0, 0, 0), 255)
    '0.0.0.255'

    >>> ip_inc ((0, 0, 0, 0), 256)
    '0.0.1.0'

    >>> ip_inc ((0, 0, 255, 513), 256)
    '0.1.2.1'
    """

    ip = list (ip_addr_tuple)
    ip[3] += inc

    for idx in range(len(ip)-1, -1, -1):
        carry, normalized = ip[idx]/256, ip[idx]%256
        ip[idx] = normalized
        if carry:
            ip[idx-1] += carry

    return ".".join([str(x) for x in ip])



class MyCmd(cmd.Cmd):
    def __init__(self, client):
        cmd.Cmd.__init__(self)
        self.client = client
        self.stats_time = time.time()


    def create_streams(self, num_streams, total_kpps, total_num_flows):
        """
        Create several streams with to arrived at the kpps and num_flows.

        Each stream will have equal kpps but different number of flows.
        """

        # each stream will have half the number of flows as the previous stream
        dist = [2**(x-1) for x in range(num_streams, 0, -1)]
        #tuple_len = 4 # src ip, src port, dst ip, dst port
        tuple_len = 2 # src ip, src port
        stream_to_num_flows = pro_rate(total_num_flows, dist)

	# the pro-rated dist follows the dist curve exactly but the total
        # may be out by one or two. Make this up for small
	# numbers of flows by adjusting the
	num_flows_delta = total_num_flows - sum(stream_to_num_flows)
	if (total_num_flows <= 100):
		stream_to_num_flows[0] += num_flows_delta

        # remove streams with no flows (can happend for low numbers of flows)
        stream_to_num_flows = [x for x in stream_to_num_flows if x > 0]
        num_streams = len(stream_to_num_flows)
        print "flows per stream:", stream_to_num_flows, "total:", sum(stream_to_num_flows)

        stream_to_tuple_span = []
	random.seed((num_streams, total_kpps, total_num_flows)) # always mix up tuple ranges repeatably
        for stream_no, total_num_flows in enumerate (stream_to_num_flows):
            primes, diff = n_as_product_of_primes (total_num_flows, tuple_len)
            random.shuffle(primes)
            stream_to_tuple_span.append(primes)
            print "stream#:", stream_no, "req. #flows:", total_num_flows, "tuple_spans:", primes, "diff: ", diff

        span_base = [0, 0, 0, 0]
        tuple_ranges = tuple_spans_to_ranges(stream_to_tuple_span, span_base)


        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint (tuple_ranges)

        # IP range
        src_ip_start = (16, 0, 0, 0)
        dst_ip_start = (48, 0, 0, 0)
        SRC_IP = 0
        SRC_PORT = 1
        DST_IP = 2
        DST_PORT = 3
        RANGE_START = 0
        RANGE_END = 1

	# This is hack to fill in a fixed dst ip & port
        # usu just keep tuple_len above set to 4
	trmod = []
	for tr in tuple_ranges:
            trmod.append ([tr[0], tr[1], (0, 1), (0, 1)])
        tuple_ranges = trmod

        # finally create the streams
        streams = []
        for stream_no, tuple_range in enumerate(tuple_ranges):
            print "stream#:", stream_no, "src:",                           \
                ip_inc(src_ip_start, tuple_range[SRC_IP][RANGE_START]),    \
                "-",                                                       \
                ip_inc(src_ip_start, tuple_range[SRC_IP][RANGE_END]),      \
                ":", tuple_range[SRC_PORT][RANGE_START], "-",              \
                tuple_range[SRC_PORT][RANGE_END],                          \
                "dst",                                                     \
                ip_inc(dst_ip_start, tuple_range[DST_IP][RANGE_START]),    \
                "-",                                                       \
                ip_inc(dst_ip_start, tuple_range[DST_IP][RANGE_END]),      \
                ":", tuple_range[DST_PORT][RANGE_START], "-",              \
                tuple_range[DST_PORT][RANGE_END]

            # construct the variable part of the packet
            vm = STLVM()

            # define vars
            vm.var(name="src",                                                       \
                   min_value=ip_inc(src_ip_start, tuple_range[SRC_IP][RANGE_START]), \
                   max_value=ip_inc(src_ip_start, tuple_range[SRC_IP][RANGE_END]),   \
                   size=4,op="inc")
            vm.var(name="dst",                                                       \
                   min_value=ip_inc(dst_ip_start, tuple_range[DST_IP][RANGE_START]), \
                   max_value=ip_inc(dst_ip_start, tuple_range[DST_IP][RANGE_END]),   \
                   size=4,op="inc")
            vm.var(name="srcport", min_value=tuple_range[SRC_PORT][RANGE_START],     \
                    max_value=tuple_range[SRC_PORT][RANGE_END],                      \
                    size=2,op="inc")
            vm.var(name="dstport", min_value=tuple_range[DST_PORT][RANGE_START],     \
                    max_value=tuple_range[DST_PORT][RANGE_END],                      \
                    size=2,op="inc")


            # write vars
            vm.write(fv_name="src",pkt_offset= "IP.src")
            vm.write(fv_name="dst",pkt_offset= "IP.dst")
            vm.write(fv_name="srcport",pkt_offset= "UDP.sport")
            vm.write(fv_name="dstport",pkt_offset= "UDP.dport")

	    # ensure valid csum - voodoo from syn_attack_fix_cs_hw.py
            vm.fix_chksum_hw(l3_offset="IP",
			    l4_offset = "UDP",
			    l4_type  = CTRexVmInsFixHwCs.L4_TYPE_UDP )

            # construct the fixed part of the packet
            size = 64
            pps = total_kpps*1000/num_streams
            isg = 0

            base_pkt = Ether()/IP()/UDP()
            pad = max(0, size - len(base_pkt)) * 'x'

            pkt = STLPktBuilder(pkt = base_pkt/pad,
                                vm = vm)

            streams.append(STLStream(isg = isg,
                            packet = pkt,
                            mode = STLTXCont(pps = pps)))

        return streams



    def do_start(self, line):
        """start kpps #flows
        """
        (argc, argv) = self._parse(line)
        try:
            total_num_flows = int(argv[1])
            total_kpps = int(argv[0])
        except:
            self.do_help('start')
            return 0

        self._do_clear()

        num_streams = 8
        streams = self.create_streams(num_streams, total_kpps, total_num_flows)
        stream_ids = self.client.add_streams(streams, ports=[0])
        self.client.start(ports=[0], force=True)
        self._print_warnings()


    def do_stop(self, line):
        """Stop all traffic"""
        rc = self.client.stop(rx_delay_ms=100) #returns None
	self._print_warnings()
        rc = self.client.remove_all_streams()
	self._print_warnings()


    def do_stats(self, line):
        """Display pertinent stats"""

        pp = pprint.PrettyPrinter(indent=4)
        stats = self.client.get_stats()
        now = time.time()
        stats_duration = now - self.stats_time
        print "Stats from last %0.1fs" % (stats_duration)

        (argc, argv) = self._parse(line)
        if (argc == 1):
            pp.pprint(stats)
            self._do_clear()
            self._print_warnings()
            return 0

        flow_connections = [(0, 1)] #, (1, 0), (2, 3), (3, 2)] #[(tx_port, rx_port), ...]

        for tx_port, rx_port in flow_connections:
            try:
                offered_kpps = int (stats[tx_port]['opackets'] / 1000 / stats_duration)
                rxd_kpps = int (stats[rx_port]['ipackets'] / 1000 / stats_duration)
                #dropped_kpps = int (stats['latency']...['err_cntrs']['dropped'] #only refers to latency pkts
                dropped_cnt = stats[tx_port]['opackets'] - stats[rx_port]['ipackets']
                dropped_kpps = dropped_cnt / 1000 / stats_duration
                dropped_pc = dropped_cnt * 100 / stats[tx_port]['opackets']

                print "%d->%d offered %d dropped %d rxd %d (kpps) => %d%% loss" % \
                    (tx_port, rx_port, offered_kpps, dropped_kpps,
                        rxd_kpps, dropped_pc)
            except:
                #Most likely we haven't stated traffic on this port pair
                print "%d->%d no stats (no traffic?)" % (tx_port, rx_port)

        op_str = ""
        for tx_port, rx_port in flow_connections:
            try:
                x = stats['latency'][tx_port + 10]['latency']
                op_str += "%d %d %d " % (x['average'], x['jitter'], x['total_max'])
                print "%d->%d average %d jitter %d total_max %d (us)" % \
                    (tx_port, rx_port, x['average'], x['jitter'], x['total_max'])
            except:
                #Most likely we haven't stated traffic on this port pair
                print "%d->%d no stats (no traffic?)" % (tx_port, rx_port)
        print op_str

        # print full latency stats
        #for port_id in self.client.get_all_ports():
        #    #stl/bom.py sets pg_id=port_id+10
        #    print "pg_id: %d" % (port_id + 10)
        #    pp.pprint(stats['latency'][port_id + 10]['latency'])

        self._do_clear()
        self._print_warnings()


    def do_clear(self, line):
        """Clear stats"""
        self._do_clear()
        print "Stats cleared."


    def _do_clear(self):
        self.client.clear_stats() #returns None
        self.stats_time = time.time()


    def do_quit(self, line):
        return 1


    def emptyline(self):
        return


    def _parse(self, line):
        argv = line.split()
        argc = len(argv)
        return (argc, argv)


    def _print_warnings(self):
        for w in self.client.get_warnings():
            print w
            print type (w)


def main():
    # connect to the server
    c = STLClient(server = '127.0.0.1')

    try:
        # connect to the server
        c.connect()

        # fetch the TRex server version
        ver = c.get_server_version()

        print(ver)
        res = c.reset()
        res = c.set_port_attr(c.get_all_ports(), promiscuous=True)
        MyCmd(c).cmdloop()

    except STLError as e:
        print(e)

    finally:
        c.disconnect()


if __name__ == '__main__':
    main()


