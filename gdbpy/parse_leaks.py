#!/usr/bin/env python

#malloc,1535364375.55,dp_packet_new_with_headroom,0x2c7d300,576
#free,1535364375.56,dp_packet_delete,0x2c7d300

def find_free(recs, idx):
    """
    recs:[rec, ...]
    idx:int rec[idx] is the idx of the malloc
    """

    addr = recs[idx][3]

    for idx in range(idx, len(recs)):
        if recs[idx][0].find("free") == 0 and  recs[idx][3].find(addr) == 0:
            return idx

    return 0


def main():
    recs = []
    malloc_cnt = 0
    free_cnt = 0
    leak_cnt = 0

    f = open("leaks.rec")
    for l in f:
        recs.append(l.strip().split(","))

    for idx in range(len(recs)):
        if recs[idx][0].find("malloc") == 0:
            malloc_cnt += 1
            freed_at = find_free(recs, idx)
            if not freed_at:
                print "  No free for:", ",".join(recs[idx])
                leak_cnt += 1
            else:
                free_cnt += 1
                print "#%d %s freed at #%d %s" % \
                    (idx, recs[idx], freed_at, recs[freed_at])

    print ("%d mallocs and %d frees" % (malloc_cnt, free_cnt))
    if not leak_cnt:
        print "No Leaks \0/"
    else:
        print "%d leaks" % (leak_cnt)

if __name__ == '__main__':
    main()
