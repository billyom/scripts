#!/usr/bin/env bash

# Invoke with -h for help.

# Example output from appctl dpctl/show -s
#netdev@ovs-netdev:
#        lookups: hit:672873135 missed:4 lost:0
#        flows: 4
#        port 0: ovs-netdev (tap)
#                RX packets:0 errors:0 dropped:0 overruns:0 frame:0
#                TX packets:0 errors:0 dropped:0 aborted:0 carrier:0
#                collisions:0
#                RX bytes:0  TX bytes:0
#        port 1: br0 (tap)
#                RX packets:0 errors:0 dropped:0 overruns:0 frame:0
#                TX packets:267887 errors:0 dropped:267889 aborted:0 carrier:0
#                collisions:0
#                RX bytes:0  TX bytes:16598532 (15.8 MiB)
#        port 2: dpdk_0 (dpdk: configured_rx_queues=1, configured_rxq_descriptors=2048, configured_tx_queues=2, configured_txq_descriptors=2048, mtu=1500, requested_rx_queues=1, requested_rxq_descriptors=2048, requested_tx_queues=2, requested_txq_descriptors=2048, rx_csum_offload=true)
#                RX packets:168219892 errors:0 dropped:827777839 overruns:? frame:?
#                TX packets:168221972 errors:0 dropped:0 aborted:? carrier:?
#                collisions:?
#                RX bytes:63743854784 (59.4 GiB)  TX bytes:10766206208 (10.0 GiB)
#        port 3: dpdk_1 (dpdk: configured_rx_queues=1, configured_rxq_descriptors=2048, configured_tx_queues=2, configured_txq_descriptors=2048, mtu=1500, requested_rx_queues=1, requested_rxq_descriptors=2048, requested_tx_queues=2, requested_txq_descriptors=2048, rx_csum_offload=true)
#                RX packets:168221972 errors:0 dropped:827753825 overruns:? frame:?
#                TX packets:168219904 errors:0 dropped:0 aborted:? carrier:?
#                collisions:?
#                RX bytes:63742451008 (59.4 GiB)  TX bytes:10766073088 (10.0 GiB)
#        port 4: dpdk_2 (dpdk: configured_rx_queues=1, configured_rxq_descriptors=2048, configured_tx_queues=2, configured_txq_descriptors=2048, mtu=1500, requested_rx_queues=1, requested_rxq_descriptors=2048, requested_tx_queues=2, requested_txq_descriptors=2048, rx_csum_offload=true)
#                RX packets:168215508 errors:0 dropped:827726844 overruns:? frame:?
#                TX packets:168215778 errors:0 dropped:0 aborted:? carrier:?
#                collisions:?
#                RX bytes:63740310528 (59.4 GiB)  TX bytes:10765809088 (10.0 GiB)
#        port 5: dpdk_3 (dpdk: configured_rx_queues=1, configured_rxq_descriptors=2048, configured_tx_queues=2, configured_txq_descriptors=2048, mtu=1500, requested_rx_queues=1, requested_rxq_descriptors=2048, requested_tx_queues=2, requested_txq_descriptors=2048, rx_csum_offload=true)
#                RX packets:168215767 errors:0 dropped:827698864 overruns:? frame:?
#                TX packets:168215508 errors:0 dropped:0 aborted:? carrier:?
#                collisions:?
#                RX bytes:63738536384 (59.4 GiB)  TX bytes:10765792512 (10.0 GiB)

function show_help()
{
    echo "$(basename $0) - monitor o/p from 'sudo ./utilities/ovs-appctl dpctl/show -s'"
    echo "    -i list interfaces to monitor e.g -i \"iface1 iface2\""
    echo "    -u report in packets not 1000s of packets"
    return 0
}

#TODO need to account for processing overhead to calulate rates more accurately
# - Currently pps, bps overstated by ~2-4%. Loss% unaffected.
DELAY=5

IFACES=(dpdk_0 dpdk_1 dpdk_2 dpdk_3)
KUNITS=1       #present in kpps, kbps
unit_pfx="k"
VERBOSE=0

while getopts "h?uvi:" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    u)  KUNITS=0
        ;;
    i)  IFACES=($OPTARG)
        ;;
    v)  VERBOSE=1
        ;;
    esac
done

if (($KUNITS == 0)); then
    unit_pfx=""
fi

echo "ifaces: ${IFACES[*]}"

dpctl_show_file=$(mktemp "${TMPDIR:-/tmp/}$(basename $0).XXXXXXXXXXXX")
dpctl_show_t0=${dpctl_show_file}_t0
dpctl_show_t1=${dpctl_show_file}_t1

if (( $VERBOSE )); then
    echo $dpctl_show_t0
    echo $dpctl_show_t1
fi

sudo ./utilities/ovs-appctl dpctl/show -s > $dpctl_show_t0

while :
do
    sleep $DELAY
    (( $VERBOSE )) && date --rfc-3339=ns
    sudo ./utilities/ovs-appctl dpctl/show -s > $dpctl_show_t1

    echo $(date) and previous $DELAY secs
    for iface in ${IFACES[*]}
    do
        drops_t0=$(sed -n "/port [0-9]\+: $iface/,/port [0-9]\+:/ s/^.*RX packets.*dropped:\([0-9]\+\).*$/\1/p" < $dpctl_show_t0)
        pps_t0=$(sed -n "/port [0-9]\+: $iface/,/port [0-9]\+:/ s/^.*RX packets:\([0-9]\+\) errors.*$/\1/p" < $dpctl_show_t0)
        bytes_t0=$(sed -n "/port [0-9]\+: $iface/,/port [0-9]\+:/ s/^.*RX bytes:\([0-9]\+\) .*$/\1/p" < $dpctl_show_t0)
        drops_t1=$(sed -n "/port [0-9]\+: $iface/,/port [0-9]\+:/ s/^.*RX packets.*dropped:\([0-9]\+\).*$/\1/p" < $dpctl_show_t1)
        pps_t1=$(sed -n "/port [0-9]\+: $iface/,/port [0-9]\+:/ s/^.*RX packets:\([0-9]\+\) errors.*$/\1/p" < $dpctl_show_t1)
        bytes_t1=$(sed -n "/port [0-9]\+: $iface/,/port [0-9]\+:/ s/^.*RX bytes:\([0-9]\+\) .*$/\1/p" < $dpctl_show_t1)

        #if [[ -z $drops_t0 || -z $pps_t0 || -z ... ]]; then error continue.
        drops_pps=$[($drops_t1 - $drops_t0) / $DELAY]
        rxd_pps=$[($pps_t1 - $pps_t0) / $DELAY]
        rxd_bps=$[($bytes_t1 - $bytes_t0) * 8 / $DELAY]
        offered_pps=$[$drops_pps + $rxd_pps]

        if (( $offered_pps == 0 )); then
            echo "$iface Offered rate is zero pps"
            continue
        fi

        if (( $KUNITS )); then
            drops_pps=$[$drops_pps/1000]
            rxd_pps=$[$rxd_pps/1000]
            rxd_bps=$[$rxd_bps/1000]
            offered_pps=$[$offered_pps/1000]
        fi

        echo -n "$iface rxd ${rxd_bps} ${unit_pfx}bps. offered ${offered_pps} "
        echo -n "dropped $drops_pps rxd ${rxd_pps} ${unit_pfx}pps "
        echo    "=> $[$drops_pps*100/$offered_pps]% loss"
    done

    cp $dpctl_show_t1 $dpctl_show_t0
    (( $VERBOSE )) && date --rfc-3339=ns
done
