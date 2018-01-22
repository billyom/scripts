#!/usr/bin/env python

import argparse
import sys
import random
import array
from random import randint

randomizer = 0


def insert_into_emc (emc, flowid, hashes, actually_insert=True):
    """
    @returns: 1 => insert caused and eviction.
    """

    global randomizer
    for h in hashes:
        if emc[h] == 0 and actually_insert:
            emc[h] = flowid
            return 0
        else:
            pass

    #evicting
    emc[hashes[randomizer]] = flowid
    randomizer += 1
    randomizer %= len(hashes)
    return 1


def main():
    """
    Simulate an EMC to discover the expected EMC hit ratio for a given EMC
       configuration and number of flows.

    TODO - Currently it is assumed the probability that a packet is from a
       given flow is equal for all flows i.e. that the PDF of flows is uniform;
       Allow specification of probability distribution function for flows.
    """

    parser = argparse.ArgumentParser(description='Simulate OVS EMC')
    parser.add_argument('--flows', dest='flows', type=int,
                       help='No of packet flows to simulate')
    parser.add_argument('--shift', dest='shift',  type=int,
                       help='EMC capacity is 2**shift')
    parser.add_argument('--segs', dest='segs',  type=int,
                       help='No. of ways/locations at which a given flow can be inserted in EMC.')
    parser.add_argument('--random', dest='random_seed',  type=int, default=None,
                       help='For testing/repeatabiltity allow fixing of the random seed.')
    parser.add_argument('--verbose', '-v', dest='verbose',  type=bool,
                       help='Verbose')

    args = parser.parse_args()

    max_seg_hash = (2**args.shift)-1
    emc_capacity = max_seg_hash + 1

    print "EMC capacity is %d (1<<%d)" % (emc_capacity, args.shift)
    random.seed(args.random_seed)

    # create the flows and their hash
    # flow ids start at 1 as we use flowid==0 to indicate an empty slot
    flowid_to_hashes = {i:[randint(0, max_seg_hash) for j in range(args.segs)] for i in range(1, args.flows+1)}
    emc = array.array('L', (0 for i in range(emc_capacity)))

    # insert the reverse mapping (hash->flowid) into the simualted emc
    for flowid, hashes in flowid_to_hashes.iteritems():
        insert_into_emc(emc, flowid, hashes)

    # for each location in emc show the flowid stored there and the other
    # locations that flow id could've taken
    if args.verbose:
        for i in range(len(emc)):
            print i, emc[i], flowid_to_hashes[emc[i]] if emc[i] else "-"

    # have a peek into the emc to see which flows are in there and which are
    # not (ie which got evicted by a subsequent flow).
    num_empty_slots = sum(1 if flowid == 0 else 0 for flowid in emc)
    num_taken_slots = emc_capacity - num_empty_slots

    #print "num_empty_slots:", num_empty_slots
    print "Predictions based on a uniform flow distribution:"
    print "EMC %.0f%% full. %d of %d" % (100*(num_taken_slots)/emc_capacity,
                                              num_taken_slots,
                                              emc_capacity)
    print "EMC hit rate %.0f%% %d/%d" % (100*(num_taken_slots)/args.flows,
                                         num_taken_slots,
                                         args.flows)


if __name__ == '__main__':
    pass

main()


