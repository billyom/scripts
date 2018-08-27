# Resource leak detection using gdb python hooks

For free/malloc memory leaks you might be as well off to use mtrace [1].

This method could still be useful for other resource leaks or rte_mem leaks
unless that has it's own leak detection framework.

* Bullet point

```
  format-as-code
```

## References

[1] https://raw.githubusercontent.com/sugchand/ovs-dpdk-memleek
[2] https://sourceware.org/gdb/wiki/PythonGdbTutorial
[3] https://sourceware.org/gdb/onlinedocs/gdb/Breakpoints-In-Python.html#Breakpoints-In-Python
[4] https://sourceware.org/gdb/onlinedocs/gdb/Commands-In-Python.html
