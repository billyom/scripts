#!/usr/bin/env python
# get TRex APIs
from trex_stl_lib.api import *

import time
import cmd
import re
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

class MyCmd(cmd.Cmd):
    def __init__(self, client):
        cmd.Cmd.__init__(self)
        self.client = client
        self.dist = [1, 1, 1, 1]
        self.stats_time = time.time()

    def do_start(self, line):
        """start <total offered rate kpps>
        Start traffic. Total kpps across all ports. e.g 'start 10'
        """
        (argc, argv) = self._parse(line)
        if (argc != 1):
            self.do_help('start')
            return 0

        rate_mbps = int(argv[0])
        rates = pro_rate (rate_mbps, self.dist)

        self._do_clear()

        for port, rate in enumerate(rates):
            if rate == 0:
                continue
            start_line = "-f stl/bom.py -m %skpps --port %d --force" % (rate, port)
            #start_line = "-f stl/bom.py --port %d --force" % (port)
            print start_line
            rc = self.client.start_line(start_line)
            if rc.bad():
                print rc
                break
            self._print_warnings()

    def do_dist(self, line):
        """Set traffic dist across 4 ports e.g. 'dist 2 1 1 1' """
        try:
            dist_list = re.split(" |,", line)
            dist_list = [int(s.strip()) for s in dist_list if s]
            if len (dist_list) != 4:
                raise Exception ("dist len must be 4")
            for i in dist_list:
                if type(i) is not int:
                    raise Exception ("dist items must be ints")
            self.dist = dist_list
        except (Exception), ex:
            print ex
        print "Dist ratio is", self.dist

    def do_stop(self, line):
        """Stop all traffic"""
        rc = self.client.stop(rx_delay_ms=100) #returns None

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

        flow_connections = [(0, 1), (1, 0), (2, 3), (3, 2)] #[(tx_port, rx_port), ...]

        for tx_port, rx_port in flow_connections:
            try:
                opackets = stats[tx_port]['opackets']
                ipackets = stats[rx_port]['ipackets']
                offered_kpps = int (opackets / 1000 / stats_duration)
                rxd_kpps = int (ipackets / 1000 / stats_duration)
                #dropped_kpps = int (stats['latency']...['err_cntrs']['dropped'] #only refers to latency pkts
                dropped_cnt = opackets - ipackets
                dropped_kpps = dropped_cnt / 1000 / stats_duration
                dropped_pc = dropped_cnt * 100 / opackets
                warn_str = " (rxd# > txd# !)" if ipackets > opackets else "" #often seen - is a TRex bug?
                print "%d->%d offered %d dropped %d rxd %d (kpps) => %d%% loss%s" % \
                    (tx_port, rx_port, offered_kpps, dropped_kpps,
                        rxd_kpps, dropped_pc, warn_str)
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
