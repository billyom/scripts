#break ovs_mutex_unlock thread 2 if l_=&dpdkhw_flow_mutex
#commands
#silent
#where 2
#cont
#end

layout src
set print pretty on
source magic.py
leak start
run
leak dump leaks.rec
