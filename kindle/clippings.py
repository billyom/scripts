#!/usr/bin/env python
# coding=utf-8
# Reorder the entries in kindle's MyClippings.txt from chronological 
# order into several files (one per book) in which the notes & highlights 
# are ordered by their location with in the books text.
#
#TODO 
# Update txt output option
# add --mediawiki output option
# preserve unicode chars
# Test 'My Clippings' containing:
#   Highlight-
#   Highlight with note-
#   Orphan single-line note-
#   Orphan multiline note-
#   Chpt highligh w single-line note-
#   Chpt highligh w Multiline note-
#
# 
#
#

import re
import sys
import codecs
import logging
from optparse import OptionParser

g_loc_regex = re.compile (u"Your\s+(?P<type>(Highlight)|(Note)|(Bookmark))( on Page (?P<page>\d+))?.*Location (?P<loc_s>\d+)(\-)?((?P<loc_e>\d+))?")
#- Your             Highlight on Page 2 | Location 58-59 | Added on Saturday, 21 July 12 17:54:08


class Title (object):
    def __init__(self, title):
        self.title = title
        self.notes = []
        self.highlights = []
        self.entries = []
        
    def add_note(self, note):
        self.notes.append(note)
        
    def add_hl (self, hl):
        self.highlights.append(hl)

    def defrob(self):
        """
        Move notes that 'belong' to a highlight into that hl.
        """
        
        orphan_notes = [] #notes that do not belong to a highlight
        for note in self.notes:
            for hl in self.highlights:
                if hl.loc_e and hl.loc_s <= note.loc_s <= hl.loc_e:
                    hl.add_note(note) #note 'belongs' to this hl
                    break
                elif not hl.loc_e and hl.loc_s <= note.loc_s <= hl.loc_s + 1:
                    # Title probably created from a .csv and lacks end locations for highlights.
                    hl.add_note(note) #note 'belongs' to this hl
                    break
            else:
                #this notes location did not correspond with any highlight
                orphan_notes.append(note)
                    
        self.notes = orphan_notes
        self.entries = []
        self.entries.extend(self.notes)
        self.entries.extend(self.highlights)
        self.entries.sort()
        #self.notes.sort()
        #self.highlights.sort()
        
        
        
class Note (object):
    def __init__(self, loc_s, page, txt):
        self.loc_s = loc_s
        self.page = page
        self.chpt_level = 0
        txt = txt.lstrip() #remove any leading spaces
        txt = txt.rstrip(' \n')
        print "Note: '%s'" % txt
        if txt[:4].lower() in ['chap', 'chpt']: 
            self.chpt_level = 1
            txt = txt[4:]
            txt = txt.lstrip()
        if txt[:3].lower() in ['sub', 'sec']: 
            self.chpt_level = 2
            txt = txt[4:]
            txt = txt.lstrip()
        self.txt = txt            
                
    def __cmp__(self, that):
        return cmp(self.loc_s, that.loc_s)

        
class Highlight (object):
    def __init__(self, loc_s, loc_e, page, txt):
        self.loc_s = loc_s
        self.loc_e = loc_e
        self.page = page
        self.txt = txt            
        self.notes = []
        self.chpt_level = 0
        
    def add_note(self, note):
        self.chpt_level = note.chpt_level
        if not note.txt or note.txt.isspace():
            #don't add empty notes (a note can be empty it only contains the magic chapter marker
            return
        
        if filter(lambda n: n.txt == note.txt, self.notes):
            #don't add a duplicate notes
            return
                        
        self.notes.append(note)
        
    def __cmp__(self, that):
        return cmp(self.loc_s, that.loc_s)

def print_title_text(title):
    s = u"="*len(title.title)
    s += u"\n%s\n" % title.title
    s += u"="*len(title.title)
    print s.encode('utf-8', 'ignore')
    
    if title.entries:
        #ie title had it's entries&highlights merged
        print_entries_text(title.entries)
    else:
        print_entries_text(title.highlights)
        print_entries_text(title.notes)
    print "\n\n"
    
def print_entries_text(entries):
    #print "print_entries_text", len(entries)
    for entry in entries:
        s = u""
        if isinstance(entry, Highlight):
            if entry.chpt_level == 1:
                s += u'\nCHAPTER: %s' % entry.txt
            elif entry.chpt_level == 2:
                s += u'\nSECTION: %s' % entry.txt
            else:
                s += u'\n"...%s..."' % entry.txt
                if entry.page:
                    s += u" (Page %d)" % entry.page
                else:
                    s += u" (loc. %d" % entry.loc_s
                    if entry.loc_e:
                        s += u"-%d" % entry.loc_e
                    s += u")"
            for n, note in enumerate(entry.notes):
                s += u"\n\tNote #%d: %s " % (n+1, note.txt.replace("\n", "\n\t"))
        elif isinstance(entry, Note):
            s += u"\nNOTE:\t%s (%d)" % (entry.txt.replace("\n", "\n\t"), entry.loc_s)
            
        print s.encode('utf-8', 'ignore')
            
            
def print_title_mediawiki(title):
    s = u"''%s''\n" % title.title
    print s.encode('utf-8', 'ignore')
    
    if title.entries:
        #ie title had it's entries&highlights merged
        print_entries_mediawiki(title.entries)
    else:
        print_entries_mediawiki(title.highlights)
        print_entries_mediawiki(title.notes)
    print "\n\n"
    
def print_entries_mediawiki(entries):
    #print "print_entries_mediawiki", len(entries)
    for entry in entries:
        s = u""
        if isinstance(entry, Highlight):
            if entry.chpt_level == 1:
                s += u'\n\n==%s==' % entry.txt
                for n, note in enumerate(entry.notes):
                    s += u"\n''%s''" % (note.txt.replace("\n", "''\n\n''"))
            elif entry.chpt_level == 2:
                s += u'\n\n===%s===' % entry.txt
                for n, note in enumerate(entry.notes):
                    s += u"\n''%s''" % (note.txt.replace("\n", "''\n\n''"))
            else:
                s += u'\n\n"...%s..."' % entry.txt
                if entry.page:
                    s += u" (Page %d)" % entry.page
                else:
                    s += u" (loc. %d" % entry.loc_s
                    if entry.loc_e:
                        s += u"-%d" % entry.loc_e
                    s += u")"
                for n, note in enumerate(entry.notes):
                    s += u"\n:''%s''" % (note.txt.replace("\n", "''\n''"))
        elif isinstance(entry, Note):
            s += u"\n\n''%s (loc. %d)''" % (entry.txt.replace("\n", "''\n''"), entry.loc_s)
            
        print s.encode('utf-8', 'ignore')
        
        
def print_titles_text(titles):
    for title in titles.values():
        print_title(title)

def get_title_author_from_csv(f):
    """
    Given a file with the lines:
        "Your Kindle Notes For:",,,
        "STALIN: THE COURT OF THE RED TSAR",,,
        "by Simon Sebag Montefiore",,,
        "Free Kindle instant preview:",,,
        "http://a.co/4wnnCN3",,,
    Return ("STALIN: THE COURT OF THE RED TSAR", "by Simon Sebag Montefiore")
    
    Also advance the file pointer to the start of the clippings proper.
    """
    regex = re.compile (u"\"(?P<words>.*)\"")
    l = f.readline()
    while l.find("Your Kindle Notes For") < 0:
        l = f.readline()
    l = f.readline()
    mo = regex.match(l)
    if not mo:
        raise Exception("Failed to find title line in .csv file")
    title_str = mo.group('words')
    l = f.readline()
    mo = regex.match(l)
    if not mo:
        raise Exception("Failed to find author line in .csv file")
    author_str = mo.group('words')

    while l.find("Annotation Type") < 0:
        l = f.readline()
    
    return title_str, author_str

def parse_clippings_txt(f, titles):
    """
    f:File open File obj to a Kindle clippings.txt file
    titles:{title:ustr -> Title} OUT
    """
    current_block = []
    for l in f:
        if l.find("====") == 0:
            #end of the block - analyse block
            try:
                title_str = current_block[0].strip()  #TODO remove sometimes leading u'\ufeff'
                #title_str = title_str.encode('ascii', 'ignore') #for now just collapse to ascii

                mo = g_loc_regex.search(current_block[1], re.IGNORECASE)
                if not mo: raise Exception("regex failed")
                
                loc_s = int(mo.group('loc_s')) #there is always a starting location
                loc_e = None
                page = None
                try:
                    #end location may or may not exist
                    loc_e = int(mo.group('loc_e'))
                except:
                    pass
                try:
                    #page may or may not exist
                    page = int(mo.group('page'))
                except:
                    pass
                txt = u"\n".join(current_block[3:]) #collapse the text down to single string w embedded '\n's
                
                title = g_titles.setdefault(title_str, Title(title_str))  #retrieve/create title to store note/highlight
                            
                type = mo.group('type').lower()
                if mo.group('type').lower() == u'note': 
                    note = Note(loc_s, page, txt)
                    title.add_note(note)
                if mo.group('type').lower() == u'highlight': 
                    hl = Highlight(loc_s, loc_e, page, txt)
                    title.add_hl(hl)                
            except Exception, ex:
                logging.exception(ex)
                
            current_block = []
        else:
            #not end of block yet - add line to current block 
            current_block.append(l.strip())

def parse_csv(f, titles):
    """
    f:File open File obj to a clippings file downloaded from kindle cloud
    titles:{title:ustr -> Title} OUT
    """
    title_str, author_str = get_title_author_from_csv(f)
    title = Title(title_str + " " + author_str)
    titles[title_str] = title
    
    loc_regex = re.compile (u"\"(?P<type>.*)\",\"Location (?P<loc_s>\d+)\",\"(?P<starred>.*)\",\"(?P<txt>.*)\"")

    for l in f:
        if l[0] == "#":
            continue
        try:
            parts=[]
            start_idx=1         # skip leading "
            for i in range (3): # four fields => three '","' delimiters
                idx = l.find('","', start_idx)
                parts.append(l[start_idx:idx].strip())
                start_idx = idx + 3
            parts.append(l[start_idx:(l.find('"', start_idx))]) #fourth field runs up to but not including final '"'
            print parts
            #parts[0] = parts[0][1:]
            loc_s = int(parts[1].split()[1])
            txt = parts[3]
            if parts[0].lower().find("note") >= 0:
                title.add_note(Note(loc_s, None, txt))
            else:
                title.add_hl(Highlight(loc_s, None, None, txt))
        except (Exception), ex:
            print "Failed to parse '%s'" % l
            logging.exception(ex)
        
        """
        try:
            mo = loc_regex.search(l, re.IGNORECASE)
            if not mo:
                raise Exception("regex failed")
            
            loc_s = int(mo.group('loc_s')) #there is always a starting location
            txt = mo.group('txt')
            type = mo.group('type').lower()
            if mo.group('type').lower() == u'note': 
                note = Note(loc_s, page, txt)
                title.add_note(note)
            if mo.group('type').lower().find(u'highlight') == 0:
                hl = Highlight(loc_s, None, page, txt)
                title.add_hl(hl)                
        except Exception, ex:
            logging.exception(ex)
        """

gUsage = """
Reorder the entries in kindle's My Clippings.txt for a book from chronological 
order into an output where the notes & highlights 
are ordered by their location within the book."""

def main ():        
    #process cli
    # impl cli usgage 'clippings book [--clippings my_clippings_file] [--mediawiki] > output_file'

    parser = OptionParser(usage="usage: %prog  book [--clippings my_clippings_file] [--mediawiki] > output_file" + gUsage)
    parser.add_option("-c", "--clippings", default="My Clippings.txt",
                      dest="clippings",
                      help="The kindle clippings file. Defaults to '%default'")
    parser.add_option("-m", "--mediawiki", default=False,
                      action="store_true", dest="mediawiki",
                      help="Create output in mediawiki format.")
                      
    (options, args) = parser.parse_args()
    
    if (len(args) != 1):
        print >> sys.stderr, "The book argument is required. Use -h to see help."
        sys.exit(1)
    
    requested_book = args[0]
    g_titles = {} #title:ustr -> Title

    f = codecs.open (options.clippings, 'r', 'utf-8')
    if options.clippings[-4:] == ".csv":
        parse_csv(f, g_titles)
    else:
        parse_clippings_txt(f, g_titles)
        
    for title in g_titles.values():
        title.defrob()
        
    for book_name in g_titles.keys():
        if book_name.lower().find(requested_book.lower()) >=0:
            if options.mediawiki:
                print_title_mediawiki(g_titles[book_name])
            else:
                print_title_text(g_titles[book_name])
            sys.exit(0)
    
    print >> sys.stderr, "Could not find any clippings from a title matching '%s'!" % requested_book
    print >> sys.stderr, "Clippings file refers to the following titles:" 
    for book_name in g_titles.keys():        
        print >> sys.stderr, "\t", book_name.encode('ascii', 'replace')

    sys.exit(1)
    
if __name__ == '__main__':
    main()