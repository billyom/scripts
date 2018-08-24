import gdb
import time

g_records = [] #[str, ...]

class MallocFinBp(gdb.FinishBreakpoint):
    def __init__(self, size):
        gdb.FinishBreakpoint.__init__(self)
        self.size = size

    def stop (self):
        fr = gdb.newest_frame()
        # Finish bp is actually located in the *caller* of the target
        g_records.append("malloc,%s,%s,%s,%s" % (time.time(), fr.older().name(), self.return_value, self.size))
        return False  #True stop, False continue

    def out_of_scope (self):
        print ("something wrong with MallocFinBp!")

class MallocBp(gdb.Breakpoint):
    def stop (self):
        size = gdb.newest_frame().read_var("size")
        MallocFinBp(size)  #default to sets the temp FinishBp to *this* fn call
        return False   #True stop, False continue

class FreeBp(gdb.Breakpoint):
    def stop (self):
        fr = gdb.newest_frame()
        #need to compile with -static-libgcc or 'mem' will not be available
        g_records.append(("free,%s,%s,%s" % (time.time(), fr.older().name(), fr.read_var("mem"))))
        return False   #True stop, False continue

MallocBp('xcalloc')
MallocBp('xmalloc')
FreeBp('free')

class LeakPrefixCommand (gdb.Command):
  "Prefix command for mem leaks."

  def __init__ (self):
    super (LeakPrefixCommand, self).__init__ ("leak",
                         gdb.COMMAND_SUPPORT,
                         gdb.COMPLETE_NONE, True)

LeakPrefixCommand()


class LeakRecordCommand (gdb.Command):
    """Show alloc/free g_records"""

    def __init__ (self):
        super (LeakRecordCommand, self).__init__ ("leak records",
                                                       gdb.COMMAND_SUPPORT,
                                                       gdb.COMPLETE_FILENAME)

    def invoke (self, arg, from_tty):
        f = None
        if arg:
            f = open(arg.split()[0], 'w')
        for rec in g_records:
            print (rec)
            if f:
                f.write(rec)
                f.write("\n")
        if f:
            f.close()

LeakRecordCommand ()

