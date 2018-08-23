import gdb
import time

g_records = [] #[str, ...]

class MallocFinBp(gdb.FinishBreakpoint):
    def __init__(self, size):
        gdb.FinishBreakpoint.__init__(self)
        self.size = size

    def stop (self):
        fr = gdb.newest_frame()
        g_records.append( "malloc %s %s %s %s" % (time.time(), self.return_value, fr.name(), self.size))
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
        #need to compile with -static-libgcc or 'mem' will not be available
        g_records.append( "free %s %s %s" % (time.time(), fr.read_var("mem"), fr.older().name()))   
        return False   #True stop, False continue
        
MallocBp('xzalloc')
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
        print (g_records)

LeakRecordCommand ()

