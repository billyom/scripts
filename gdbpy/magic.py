import gdb
import time

records = [] #[str, ...]

class MallocFinBp(gdb.FinishBreakpoint):
    def __init__(self, size):
        gdb.FinishBreakpoint.__init__(self)
        self.size = size

    def stop (self):
        fr = gdb.newest_frame()
        records.append( "m %s %s %s %s" % (time.time(), self.return_value, fr.name(), self.size))
        return False  #True stop, False continue

    def out_of_scope (self):
        print ("something wrong with MallocFinBp!")

class MallocBp(gdb.Breakpoint):
    def stop (self):
        size = gdb.newest_frame().read_var("size")
        print ("size", size)
        MallocFinBp(size)  #default to sets the temp FinishBp to *this* fn call
        return False   #True stop, False continue

class FreeBp(gdb.Breakpoint):
    def stop (self):
        fr = gdb.newest_frame()
        records.append( "f %s %s %s" % (time.time(), fr.read_var("mem"), fr.older().name()))
        return False   #True stop, False continue

MallocBp('xzalloc')
FreeBp('free')
