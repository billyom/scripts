#!/usr/bin/env python

import os
import re
import sys
import subprocess
import datetime  
import time
import shutil
from optparse import OptionParser

gUsage = """

  Recursivly find all .nef & .jpg files files under src_dir.
  Copy them to dest_dir/<year>/<month>/file<date_time> where
  year/month and date_time are based on the files creation time.
  
  Files under directories named '.picasaoriginals' are never copied.
   
  The intermediate dirs year & month will be created as required but
  dest_dir must exist already.
   
  No files are ever overwritten.
  Source files that already have a date formatted name are copied with no name change.
  
  TODO: use date from EXIF info instead of file date.
  TODO: do not copy files older than the newest file under the target dir"""


def dirwalk(dir, prune_list):
    """
    A Generator Function that returns each filename in a directory tree.
    @see http://code.activestate.com/recipes/105873/"""

    for f in os.listdir(dir):
        fullpath = os.path.join(dir,f)
        if os.path.isdir(fullpath) and not os.path.islink(fullpath) and not f in prune_list:
            for x in dirwalk(fullpath, prune_list):  # recurse into subdir
                yield x
        else:
            yield fullpath

 
def main():
    # process cli
    parser = OptionParser(usage="usage: %prog src_dir dest_dir " + gUsage)
    parser.add_option("", "--nointer", default=False,
                      action="store_true", dest="nointer",
                      help="Do not create intermediate year/month dirs. Copy into dest_dir/.")
    parser.add_option("", "--nostamp", default=False,
                      action="store_true", dest="nostamp",
                      help="Do not datestamp dest filename.")
    parser.add_option("", "--dryrun", default=False,
                      action="store_true", dest="dryrun",
                      help="Print what would be done but don't do anything")
    parser.add_option("", "--date", default="",
                      dest="date",
                      help="Do not copy files dated _before_ this date. yyyymmdd")
    (gOptions, gArgs) = parser.parse_args()
    
    if (len(gArgs) != 2):
        print "Need exactly 2 args."
        sys.exit(1)
 
    src_dir = gArgs[0]    
    dest_dir = gArgs[1]
        
    # check src & dst dirs exist
    if not os.path.isdir(src_dir):
        print "%s does not exist or is not a directory. Exiting." % (src_dir)
        return 1
        
    if not os.path.isdir(dest_dir):
        print "%s does not exist or is not a directory. Exiting." % (dest_dir)
        return 1
      
    if gOptions.date.lower() == 'none':
        # copy all files regardless of time
        latest_time_in_dest = 0.0
        print ("Cut-off time set to 'none'. Copying all files regardless of date")    
    elif gOptions.date:
        # use cli supplied cutoff date
        latest_time_in_dest = time.mktime(time.strptime(gOptions.date, "%Y%m%d"))
        print ("Skipping files earlier than %s." % time.ctime(latest_time_in_dest))
    else:
        # cut-off time is that of most recent file in dest_dir
        # TODO there is scope for badness here if a file in dest dir
        # has been edited (should use jpeg time)
        latest_time_in_dest = 0.0
        # latest_tstamp_in_dest = ""
        for src_file in dirwalk (dest_dir, prune_list=['.picasaoriginals', 'NKSC_PARAM']):
            mo = re.search ("(\d{4}_\d{2}_\d{2}[A-Z][a-z]{2}\d{4}).*((\.jpg$)|(\.jpeg$)|(\.nef$))",
                src_file, re.IGNORECASE)
            if mo:
                # have a file we are interested - check date
                timestamp = mo.group(1)
                # print mo.group(0), mo.group(1)            
                as_tm = time.strptime(timestamp, "%H%M_%S_%d%b%Y")  #eg 1315_59_07Apr2010
                # time.gmtime(os.path.getmtime (src_file))
                as_time = time.mktime(as_tm)
                if as_time > latest_time_in_dest:
                    latest_time_in_dest = as_time
                    # latest_tstamp_in_dest = timestamp
    			
        print "Files up to %s already appear to be copied. Skipping earlier files." % time.ctime(latest_time_in_dest)    
        answer = raw_input("continue? ")
        if not answer.lower() in ["y", "yes"]:
            print "Ok, I'm outta here!"
            sys.exit(0)
		
    # recurse into src_dir
    for src_file in dirwalk (src_dir, prune_list=['.picasaoriginals', 'NKSC_PARAM']):
        if os.path.getmtime(src_file) <= latest_time_in_dest:
            print "Skipping", src_file, "Before cutoff time."
            continue
            
        if re.search ("(\.jpg$)|(\.jpeg$)|(\.nef$)", src_file, re.IGNORECASE):
            # have a file we are interested - create the trailing date str            
            date_str = ""
            if not gOptions.nostamp:
                date_str = time.strftime ("_%H%M_%S_%d%b%Y", time.localtime(os.path.getmtime (src_file)))
            
            # copy into intermediate dirs if reqd
            inter_dir = ""
            if (gOptions.nointer):
                pass 
            else:
                inter_dir = time.strftime ("\\%Y\\%B\\", time.localtime(os.path.getmtime (src_file)))
                
            # split /path/to/dsc.123.jpg filename into main  at ext
            file_basename = os.path.basename(src_file)   
            file_ext = file_basename.split(".")[-1]
            file_base = ".".join(file_basename.split(".")[0:-1])
            print "file_base:", file_base
            if re.search("\d{4}_\d{2}_\d{2}[A-Z][a-z]{2}\d{4}", file_base, re.IGNORECASE):
                #looks like this file already has a datestamped name - don't append another stamp
                date_str = ""
                
            # final dst file name
            dst_file = dest_dir + "\\" + inter_dir + file_base + date_str + "." + file_ext 
            dst_dir = os.path.dirname(dst_file)
            
            # ensure dest dir exists
            if not os.path.isdir(dst_dir):
                print "Creating %s..." % (dst_dir)
                if not gOptions.dryrun:
                    os.makedirs (dst_dir)
                    
            if os.path.isfile(dst_file):
                print "Skipping %s. %s already exists! " % (src_file, dst_file)
                continue
          
            print "copying %s to %s..." % (src_file, dst_file)
            if gOptions.dryrun:
                continue
                
            shutil.copy2(src_file, dst_file) # copy2 -> preserve creation time and permissions
          
    return 0
    
if __name__ == "__main__":
    sys.exit(main()) 
