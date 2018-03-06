#!/usr/bin/env python
# get TRex APIs
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
233, 239, 241, 251]


from operator import mul

def n_as_product_of_primes (n, num_primes):
    """
    >>> n_as_product_of_primes (200, 4)
    ([1, 3, 5, 13], 5)
    """

    best_diff = None
    best_combo = None

    for combo in itertools.combinations(primes_and_one, num_primes):
        product = reduce(mul, combo, 1)
        diff = abs(product - n)
        if diff < best_diff or not best_diff:
            best_diff = diff
            best_combo = combo #print combo, product, diff
        if best_diff == 0:
            break

    return list(best_combo), best_diff


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
        tuple_len = 4 # src ip, src port, dst ip, dst port

        stream_to_num_flows = pro_rate(total_num_flows, dist)
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

        num_streams = 5
        streams = self.create_streams(num_streams, total_kpps, total_num_flows)
        stream_ids = self.client.add_streams(streams, ports=[0])
        self.client.start(ports=[0], force=True)
        self._print_warnings()


    def do_stop(self, line):
        """Stop all traffic"""
        rc = self.client.stop(rx_delay_ms=100) #returns None


    def do_clear(self, line):
        """Clear stats"""
        self._do_clear()


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


"""
num_flows = 1000000
dist=[1024, 512, 256, 128, 64, 32, 16, 8, 4, 2, 1]
num_buckets = len(dist)
tuple_len = 4

bucket_to_num_flows = pro_rate(num_flows, dist)
print "flows per bucket:", bucket_to_num_flows, "total:", sum(bucket_to_num_flows)

bucket_to_tuple_span = []
for bucket_no, num_flows in enumerate (bucket_to_num_flows):
    primes, diff = n_as_product_of_primes (num_flows, tuple_len)
    random.shuffle(primes)
    bucket_to_tuple_span.append(primes)
    print "bucket#:", bucket_no, "req. #flows:", num_flows, "tuple_spans:", primes, "diff: ", diff

span_base = [0, 0, 0, 0]
tuple_ranges = tuple_spans_to_ranges (bucket_to_tuple_span, span_base)

pp = pprint.PrettyPrinter(indent=4)
pp.pprint (tuple_ranges)
"""
