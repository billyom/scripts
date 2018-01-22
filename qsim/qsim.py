#!/usr/bin/env python


"""
Perform a simulation of two OvS-DPDK rx queues. Each with different offered
loads and calculate packet loss.
"""

import argparse

class FifoQ (object):
    def __init__ (self, name, capacity, ic_rate_cycles_pp):
        self.name = str(name)
        self.capacity = capacity
        self.len = 0
        self.dropped = 0
        self.enqueued = 0
        self.offered = 0
        self.capacity_exceeded = False

        self.ic_rate_cycles_pp = ic_rate_cycles_pp #push a pkt every n cycles; lower is faster
        self.t_last_nic_push_cycles = 0

    def stats (self):
        if self.offered:
            return "dropped %.2f%% ofrd/enq/drp(%s %s %s)" % (self.dropped*100.0/self.offered, self.offered, self.enqueued, self.dropped)
        else:
            return "n/a"

    def clear_stats (self):
        self.dropped = 0
        self.enqueued = 0
        self.offered = 0

    def push (self, num):
        if num < 0:
            raise Exception ("num %d is < 0" % (num))
        dropped = 0
        self.len += num
        if self.len > self.capacity:
            if not self.capacity_exceeded:
                self.capacity_exceeded = True
            dropped = self.len - self.capacity
            self.len = self.capacity
            self.dropped += dropped
        enqueued = num - dropped
        self.enqueued += enqueued
        self.offered += num

        return enqueued

    def pop (self, num):
        """
        Remove num items limited by the number available.
        Return the number actually removed.
        """

        rtn_val = num
        if num > self.len:
            rtn_val = self.len
            self.len = 0
        else:
            self.len -= num

        if self.len < self.capacity_exceeded:
            self.capacity_exceeded = False

        return rtn_val

    def nic_push (self, t_cycles):
        """
        Based on time now and ic pkt rate push the correct number of packets to the q
        """
        pkts = (t_cycles - self.t_last_nic_push_cycles) / self.ic_rate_cycles_pp
        if pkts:
            pkts = self.push (pkts)
            self.t_last_nic_push_cycles = t_cycles
        return pkts

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


def main():
    parser = argparse.ArgumentParser(description='Simulate PMD rxqs')
    parser.add_argument('--pps', dest='pps', type=str,
                       help='Total offered packets per second across all queues.')
    parser.add_argument('--ratio', dest='ratio',  type=str,
                       help='Distribution ratio of packets across queues hi/lo')
    parser.add_argument('--cycles', dest='cycles',  type=int, default=1000,
                       help='CPU cycles to process a single packet')
    parser.add_argument('--duration', dest='duration_s',  type=float, default=3,
                       help='Duration to model (secs)')
    parser.add_argument('--verbose', '-v', dest='verbose',  type=bool,
                       help='Verbose')

    args = parser.parse_args()

    CPU_FREQ_HZ = 2.188e9

    hl_ratio = args.ratio.split(",")
    hl_ratio = [eval(x) for x in hl_ratio]
    hvq_pps, lvq_pps = pro_rate (int(eval(args.pps)), hl_ratio)

    print "pps", hvq_pps, lvq_pps

    hvq_ic_rate_cycles_pp = int(CPU_FREQ_HZ/hvq_pps)
    lvq_ic_rate_cycles_pp = int(CPU_FREQ_HZ/lvq_pps)

    print "packet freq (cycles)", hvq_ic_rate_cycles_pp, lvq_ic_rate_cycles_pp
    print "packet cost (cycles)", args.cycles

    hivolq = FifoQ('hivolq', 2048, hvq_ic_rate_cycles_pp)
    lovolq = FifoQ('lovolq', 2048, lvq_ic_rate_cycles_pp)

    t_cycles = 0     #time in cpu cycles
    BATCH_SZ = 32

    t_cycles_mod_last = 0
    stats_printed = False
    while t_cycles < CPU_FREQ_HZ * args.duration_s:

        #pkts go in...
        hipktsi = hivolq.nic_push(t_cycles)
        lopktsi = lovolq.nic_push(t_cycles)
        pktsi = hipktsi + lopktsi

        #pkts come out...
        hipktso = hivolq.pop(BATCH_SZ)
        lopktso = lovolq.pop(BATCH_SZ)
        cycles = ((hipktso + lopktso) * args.cycles)

        if args.verbose and (pktsi or cycles):
            print t_cycles,
            print ":", hipktsi, hipktso, hivolq.len,
            print " - ", lopktsi, lopktso, lovolq.len

        t_cycles += cycles
        t_cycles += 1 #ensure time moves forward. Else zero-cycle spin; nothing in & nothing out.

        #print and reset stats every simulated second
        t_cycles_mod = t_cycles % CPU_FREQ_HZ
        if  t_cycles_mod < t_cycles_mod_last:
            print "At %.2fs:" % (float(t_cycles)/CPU_FREQ_HZ)
            print hivolq.name, hivolq.stats()
            print lovolq.name, lovolq.stats()
            hivolq.clear_stats()
            lovolq.clear_stats()
            stats_printed = True
        t_cycles_mod_last = t_cycles_mod

    if not stats_printed:
        print "At %.2fs:" % (float(t_cycles)/CPU_FREQ_HZ)
        print hivolq.name, hivolq.stats()
        print lovolq.name, lovolq.stats()
        hivolq.clear_stats()
        lovolq.clear_stats()

if __name__ == '__main__':
    main()
