import itertools
import random
import numbers
import pprint

primes_and_one = [1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 
31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 
73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 
127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 
179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 
233, 239, 241, 251]

"""
257, 263, 269, 271, 277, 281, 
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
1153, 1163, 1171, 1181, 1187, 1193, 1201, 1213, 1217, 1223, 
1229, 1231, 1237, 1249, 1259, 1277, 1279, 1283, 1289, 1291, 
1297, 1301, 1303, 1307, 1319, 1321, 1327, 1361, 1367, 1373, 
1381, 1399, 1409, 1423, 1427, 1429, 1433, 1439, 1447, 1451, 
1453, 1459, 1471, 1481, 1483, 1487, 1489, 1493, 1499, 1511, 
1523, 1531, 1543, 1549, 1553, 1559, 1567, 1571, 1579, 1583, 
1597, 1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657, 
1663, 1667, 1669, 1693, 1697, 1699, 1709, 1721, 1723, 1733, 
1741, 1747, 1753, 1759, 1777, 1783, 1787, 1789, 1801, 1811, 
1823, 1831, 1847, 1861, 1867, 1871, 1873, 1877, 1879, 1889, 
1901, 1907, 1913, 1931, 1933, 1949, 1951, 1973, 1979, 1987, 
1993, 1997, 1999, 2003, 2011, 2017, 2027, 2029, 2039, 2053, 
2063, 2069, 2081, 2083, 2087, 2089, 2099, 2111, 2113, 2129, 
2131, 2137, 2141, 2143, 2153, 2161, 2179, 2203, 2207, 2213, 
2221, 2237, 2239, 2243, 2251, 2267, 2269, 2273, 2281, 2287, 
2293, 2297, 2309, 2311, 2333, 2339, 2341, 2347, 2351, 2357, 
2371, 2377, 2381, 2383, 2389, 2393, 2399, 2411, 2417, 2423]
"""

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


def column_sum (lofl):
    """
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

