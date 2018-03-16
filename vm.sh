#!/usr/bin/env bash

VM_IMAGE=/opt/billy/pri-path-u14.04.fka-vloop.qcow2
QEMU_DIR=/opt/billy/opnfv/qemu
SOCK_DIR=/usr/local/var/run/openvswitch
HUGE_DIR=/dev/hugepages
MEM=3G

echo $1
if [[ $# != 1 || ! ("$1" =~ ^[0-9]+$) ]]; then
    echo "Usage: $0 <vm_number>"
    exit 1
fi

VM_NAME=us-vhost-vm$1
VHOST_NIC=dpdkvh$1
VHOST_MAC=00:00:00:00:01:$(printf "%02d" $1)
SSH_PORT=$[2000 + $1]

sudo -E taskset -c 3-13 $QEMU_DIR/x86_64-softmmu/qemu-system-x86_64 \
  -name $VM_NAME -cpu host -enable-kvm -m $MEM \
  -object memory-backend-file,id=mem,size=$MEM,mem-path=$HUGE_DIR,share=on \
  -numa node,memdev=mem -mem-prealloc -smp 1 \
  -drive file=$VM_IMAGE \
  \
  -chardev socket,id=char0,path=$SOCK_DIR/$VHOST_NIC,server \
  -netdev type=vhost-user,id=mynet1,chardev=char0,vhostforce \
  -device virtio-net-pci,mac=${VHOST_MAC},netdev=mynet1,mrg_rxbuf=off \
  \
  -net nic \
  -net user,id=ctlnet,net=20.0.0.0/8,host=20.0.0.1,hostfwd=tcp:127.0.0.1:${SSH_PORT}-:22 \
  --nographic -snapshot

#ssh to the VM by 'ssh <vm-user>@localhost -p 2000+<vm-id>'
