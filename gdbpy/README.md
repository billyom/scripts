# Resource leak detection using gdb's python hooks

For free/malloc memory leaks you might be as well off to use mtrace [1].

This method could still be useful for other resource leaks or rte_mem leaks
unless that has it's own leak detection framework.

# Usage

```
  $ gcc -g ... -o a.out             # must compile with debug info
  $ sudo gdb a.out                  # start gdb on target program
  gdb> source magic.py              # creates BPs for various resource alloc/free fns
                                    # also creates new command 'leak start|stop|target|dump'
  gdb> leak start                   # turns on the BPs
  gdb> run
  gdb> leak records leaks.rec       # write records for each alloc/free to leak.rec
  gdb> quit
  $ ./parse_leaks.py                # parses leaks.rec and matches malloc/free pairs
```

# OvS memory fns

	xrealloc ----------------> realloc //straight shim
	xzalloc  --> xcalloc ----> calloc  //calloc (3) zero's alloc'd mem
	                   '-----> malloc  //if size and count are both 0 then mallocs one byte
	                                     //prob to ensure that sz=0 alloc is still freeable?
	xmemdup  --> xmalloc ----> malloc  //alloc and copies from src 
	xmemdup0 ----^                     //allocs and zero's extra byte for null-term

# Gotchas
```
Python Exception <class 'ValueError'> Variable 'size' not found.:

Breakpoint N, 0x000000.... in FN ()
```

* Probably haven't compiled with debug info. So scripts can't get the 'size' argument to allocation fn. 


## References

[1] https://raw.githubusercontent.com/sugchand/ovs-dpdk-memleek
[2] https://sourceware.org/gdb/wiki/PythonGdbTutorial
[3] https://sourceware.org/gdb/onlinedocs/gdb/Breakpoints-In-Python.html#Breakpoints-In-Python
[4] https://sourceware.org/gdb/onlinedocs/gdb/Commands-In-Python.html
