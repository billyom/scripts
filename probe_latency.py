#!/usr/bin/env python
import sys
import os.path
import operator

gPurpose = """Parse the output of 'perf script' for specified pairs of events. Foreach CPU 
count the pairs of events and calucate the average and max latency between the
pairs.

For example:
    perf record -e probe:int_start -e probe:int_end -aR sleep 10
    perf script
            pmd9 17593 [013] 98248.350745: probe:int_start: (ffffffff8163c980)
            pmd9 17593 [013] 98248.350749:   probe:int_end: (ffffffff8163c9cc)
            ...
    perf script | probe_latency.py int_start int_end
        CPU: 013
            #latencies 10
            avg lat. 3.80000419682e-06
            max lat. 5.00000896864e-06 at 98254.35062
"""


def main ():
    if len(sys.argv) != 3:
        print ("\nUsage: perf script | %s <start_sym> <end_sym>\n" %
            (os.path.basename(sys.argv[0])))
        print gPurpose
        sys.exit(1)

    cpu_to_all_lats = {} #{cpuid:[(start tstamp, end_tstamp), ...], ...}
    cpu_to_lat = {} #{cpuid:[start tstamp, end_tstamp], ...}
    start_sym = sys.argv[1]
    end_sym = sys.argv[2]

    f = sys.stdin
    
    for l in f:
        l = l.strip()
        #print l
        # parse and clean
        th, pid, cpuid, tstamp, sym, addr = l.split()
        cpuid = cpuid[1:-1]
        tstamp = float(tstamp[:-1])
        sym = sym[len("probe:"):-1]
        addr = addr[1:-1]
        #print th, pid, cpuid, tstamp, sym, addr
   
        # get timestamps for start_sym and corresponding end_sym on the same
        # cpuid; then store the pair in cpu_to_all_lats
        lat = cpu_to_lat.get(cpuid, [None, None])
        if sym == start_sym:
            lat[0] = tstamp
            #print "start sym"
        elif sym == end_sym and lat[0]:
            #don't store end_sym tstamp unless there is a start_sym tstamp
            lat[1] = tstamp
            #print "end sym"

        if lat[0] and lat[1]:
            # we have a tstamp pair for this cpu
            if not cpu_to_all_lats.get(cpuid, None):
                #first entry for this cpuid
                #print "first pair"
                cpu_to_all_lats[cpuid] = [lat]
            else:
                #subsequent entry for this cpuid
                #print "subsequent pair"
                cpu_to_all_lats[cpuid].append(lat)
            # reset for next pair
            cpu_to_lat[cpuid] = [None, None]
        else:
            # store the partial tstamp pair
            cpu_to_lat[cpuid] = lat
            

    f.close()

    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(cpu_to_all_lats)
    for cpuid in cpu_to_all_lats.keys():
        lats = [lat[1]-lat[0] for lat in cpu_to_all_lats[cpuid]]
        max_idx, max_lat = max(enumerate(lats), key=operator.itemgetter(1))
        print "CPU:", cpuid
        print "\t#latencies", len(cpu_to_all_lats[cpuid])
        print "\tavg lat.", sum(lats)/len(lats)
        print "\tmax lat.", lats[max_idx], "at", cpu_to_all_lats[cpuid][max_idx][0]
        print

        
    
if __name__ == "__main__":
    main()
