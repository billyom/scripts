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
        g_records.append("malloc,%s,%s,%s,%s" % (time.time(),
            fr.older().name(), self.return_value, self.size))
        return False  #True stop, False continue

    def out_of_scope (self):
        print ("something wrong with MallocFinBp!")

class MallocFinBp(gdb.FinishBreakpoint):
    def __init__(self, size):
        gdb.FinishBreakpoint.__init__(self)
        self.size = size

    def stop (self):
        fr = gdb.newest_frame()
        # Finish bp is actually located in the *caller* of the target
        g_records.append("malloc,%s,%s,%s,%s" % (time.time(),
            fr.older().name(), self.return_value, self.size))
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
        g_records.append(("free,%s,%s,%s" % (time.time(), fr.older().name(),
            fr.read_var("mem"))))
        return False   #True stop, False continue

class TargetBp(gdb.Breakpoint):
    def stop (self):
        g_leak_start_cmd.invoke("", False)
        TargetFinBp()  #default is to set the temp FinishBp to *this* fn call
        return False   #True stop, False continue

class TargetFinBp(gdb.FinishBreakpoint):
    def __init__(self):
        gdb.FinishBreakpoint.__init__(self)

    def stop (self):
        g_leak_stop_cmd.invoke("", False)
        return False

    def out_of_scope (self):
        print ("something wrong with TargetFinBp!")

g_xcalloc_bp=MallocBp('xcalloc')
g_xmalloc_bp=MallocBp('xmalloc')
g_free_bp=FreeBp('free')
g_xcalloc_bp.enabled = False
g_xmalloc_bp.enabled = False
g_free_bp.enabled = False

#Create the "leak" commands
class LeakPrefixCommand (gdb.Command):
  "Prefix command for mem leaks."

  def __init__ (self):
    super (LeakPrefixCommand, self).__init__ ("leak",
                         gdb.COMMAND_USER,
                         gdb.COMPLETE_NONE, True)


class LeakDumpCommand (gdb.Command):
    """Show & save recorded alloc/free calls"""

    def __init__ (self):
        super (LeakDumpCommand, self).__init__ ("leak dump",
                                                gdb.COMMAND_USER,
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

class LeakStopCommand (gdb.Command):
    """Stop recording mallocs/frees"""

    def __init__ (self):
        super (LeakStopCommand, self).__init__ ("leak stop",
                                                gdb.COMMAND_USER,
                                                gdb.COMPLETE_NONE)

    def invoke (self, arg, from_tty):
        g_xcalloc_bp.enabled = False
        g_xmalloc_bp.enabled = False
        g_free_bp.enabled = False

class LeakStartCommand (gdb.Command):
    """Restarts recording malloc/frees after previous 'leak stop'"""

    def __init__ (self):
        super (LeakStartCommand, self).__init__ ("leak start",
                                                gdb.COMMAND_USER,
                                                gdb.COMPLETE_NONE)

    def invoke (self, arg, from_tty):
        g_xcalloc_bp.enabled = True
        g_xmalloc_bp.enabled = True
        g_free_bp.enabled = True

class LeakTargetCommand (gdb.Command):
    """Log leaks for a specific fn"""
    target_bp = None

    def __init__ (self):
        super (LeakTargetCommand, self).__init__ ("leak target",
                                                gdb.COMMAND_USER,
                                                gdb.COMPLETE_SYMBOL)

    def invoke (self, arg, from_tty):
        if not arg:
            return
        target = arg.split()[0]
        if LeakTargetCommand.target_bp and \
           LeakTargetCommand.target_bp.is_valid() :
            # overwrite existing leak target
            LeakTargetCommand.target_bp.delete()

        LeakTargetCommand.target_bp = TargetBp(target)
        g_records = []

LeakPrefixCommand()
LeakDumpCommand ()
g_leak_target_cmd = LeakTargetCommand ()
g_leak_start_cmd = LeakStartCommand ()
g_leak_stop_cmd = LeakStopCommand ()
