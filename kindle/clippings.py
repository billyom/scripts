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

import re
import sys
import codecs
import logging
from optparse import OptionParser
from collections import OrderedDict

g_loc_regex = re.compile (u"Your\s+(?P<type>(Highlight)|(Note)|(Bookmark))( on Page (?P<page>\d+))?.*[Ll]ocation (?P<loc_s>\d+)(\-)?((?P<loc_e>\d+))?")
#- Your             Highlight on Page 2 | Location 58-59 | Added on Saturday, 21 July 12 17:54:08
#- Your             Highlight on page 5 | location 79-71 | Added on Sunday, 14 October 2018 23:35:18'

def re_test(bla):
    """
    >>> str = '- Your             Highlight on Page 2 | Location 58-59 | Added on Saturday, 21 July 12 17:54:08'
    >>> mo = g_loc_regex.search(str, re.IGNORECASE)
    >>> loc_s = int(mo.group('loc_s'))
    58
    """
    None

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

    def crossref(self):
        """
        Populates entries element, which associates Notes with correct Highlight
        and in order of occurence in the Title.
        
        To be called once all Notes and Highlights have been added.
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
        #print "Note: '%s'" % txt
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

def print_title_text(title, f):
    s = u"="*len(title.title)
    s += u"\n%s\n" % title.title
    s += u"="*len(title.title)
    #print s.encode('utf-8', 'ignore')
    f.write(s)
    
    if title.entries:
        #ie title had it's entries&highlights merged
        print_entries_text(title.entries, f)
    else:
        print_entries_text(title.highlights, f)
        print_entries_text(title.notes, f)
    
def print_entries_text(entries, f):
    """
    Given a list of Notes & Highlights prints them in
    mediawiki markup to file f.
    """
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
            
        #print s.encode('utf-8', 'ignore')
        f.write(s)
            
            
def print_title_mediawiki(title, f):
    s = u"''%s''\n" % title.title
    #print s.encode('utf-8', 'ignore')
    f.write(s)
    
    if title.entries:
        #ie title had it's entries & highlights merged
        print_entries_mediawiki(title.entries, f)
    else:
        print_entries_mediawiki(title.highlights, f)
        print_entries_mediawiki(title.notes, f)
    
    
def print_entries_mediawiki(entries, f):
    """
    Given a list of Notes & Highlights prints them in
    mediawiki markup to file f.
    """
    
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
            #s += u"\n\n''%s (loc. %d)''" % (entry.txt.replace("\n", "''\n''"), entry.loc_s)
            s += u"\n\n''%s''" % (entry.txt.replace("\n", "''\n''"))
            
        #print s.encode('cp1252', 'ignore')
        f.write(s)
        
        
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
    line_no = 0
    regex = re.compile (u"\"(?P<words>.*)\"")
    l = f.readline()
    line_no += 1
    while l.find("Your Kindle Notes For") < 0:
        l = f.readline()
        line_no += 1
    l = f.readline()
    line_no += 1
    mo = regex.match(l)
    if not mo:
        raise Exception("Failed to find title line in .csv file")
    title_str = mo.group('words')
    l = f.readline()
    line_no += 1
    mo = regex.match(l)
    if not mo:
        raise Exception("Failed to find author line in .csv file")
    author_str = mo.group('words')

    while l.find("Annotation Type") < 0:
        l = f.readline()
        line_no += 1
    
    return title_str, author_str, line_no

def parse_clippings_txt(f, titles):
    """
    Parse a clippings.txt file. 
    
    Creates a Title for each book found. Extracts the Notes and Highlights for the Title and 
    adds them to the Title.
    
    f:File An open File obj to a Kindle clippings.txt file
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
                if not mo:
                    raise Exception("regex failed '%s'" % current_block[1])
                
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
                
                title = titles.setdefault(title_str, Title(title_str))  #retrieve/create title to store note/highlight
                            
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
    Parses a clippings csv file.
    
    Creates a Title for each book found. Extracts the Notes and Highlights for the Title and 
    adds them to the Title.
    
    f:File open File obj to a clippings file downloaded from kindle cloud
    titles:{title:ustr -> Title} OUT
    """
    title_str, author_str, line_no = get_title_author_from_csv(f)
    title = Title(title_str + " " + author_str)
    titles[title_str] = title
    
    loc_regex = re.compile (u"\"(?P<type>.*)\",\"Location (?P<loc_s>\d+)\",\"(?P<starred>.*)\",\"(?P<txt>.*)\"")
    
    try:
        for l in f:
            line_no += 1
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
                loc_s = int(parts[1].split()[1])
                txt = parts[3].strip()
                #print line_no, txt
                if parts[0].lower().find("note") >= 0:
                    title.add_note(Note(loc_s, None, txt))
                else:
                    title.add_hl(Highlight(loc_s, None, None, txt))
            except (Exception), ex:
                print "Failed to parse '%s'" % l
                logging.exception(ex)
    except (Exception), ex:
        print "Failed to get line! line# %d" % line_no
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

def choose_book(titles):
    """
    Present a list of title to the user and let them choose one.
    
    titles:{title:ustr -> Title}
    
    returns: title:ustr
    """
    
    print("Select Book:")
    for idx, title in enumerate(titles.keys()):
        print("%(idx)d. %(title)s" % locals())
    choice_txt = raw_input("Enter number or part of title: ").lower()

    choice_int = None    
    try:
        choice_int = int(choice_txt)
    except:
        pass
        
    if (choice_int):
        # User entered a number. Pick the corresponding title from displayed list.
        title = titles.keys()[choice_int]
    else:
        # User entered a string. Find the first title that matches.        
        title = filter(lambda t: t.lower().find(choice_txt) >= 0, titles.keys())[0]
            
    return title
    

gUsage = """
Reorder the entries in kindle's My Clippings.txt for a book from chronological 
order into an output where the notes & highlights 
are ordered by their location within the book."""

def main ():        
    #process cli
    # impl cli usgage 'clippings book [--clippings my_clippings_file] [--txt] > output_file'

    parser = OptionParser(usage="usage: %prog  book [--clippings my_clippings_file] [--txt] > output_file" + gUsage)
    parser.add_option("-c", "--clippings", default="My Clippings.txt",
                      dest="clippings",
                      help="The kindle clippings file. Defaults to '%default'")
    parser.add_option("-t", "--txt", default=True,
                      action="store_false", dest="mediawiki",
                      help="Create output in plain text format. Default is mediawiki format.")
                      
    (options, args) = parser.parse_args()
        
    titles = OrderedDict()    #title:ustr -> Title

    # Clippings can be either .txt or .csv. Call the correct parse fn.
    if options.clippings[-4:] == ".csv":
        f = codecs.open (options.clippings, 'r', 'utf-8')
        parse_csv(f, titles)
    else:
        # TODO - seems to be no rhyme or reason to the encoding of the clippings file!
        f = codecs.open (options.clippings, 'r', 'utf-8', 'replace')  #cp500, cp850, cp858, cp1140, cp1252, iso8859_15, mac_roman,             
        parse_clippings_txt(f, titles)
        
    if (len(args) != 1):
        requested_book = choose_book(titles)
    else:
        requested_book = args[0]
        
    print "Writing", requested_book, "to", "'title.mw/.txt'..."
        
    for book_name in titles.keys():
        if book_name.lower().find(requested_book.lower()) >=0:
            titles[book_name].crossref()
            if options.mediawiki:
                f = codecs.open("./title.mw", 'w', 'utf-8', 'replace')
                print_title_mediawiki(titles[book_name], f)
                f.close()
            else:
                f = codecs.open("./title.txt", 'w', 'utf-8', 'replace')
                print_title_text(titles[book_name], f)
                f.close()
            sys.exit(0)
    
    print >> sys.stderr, "Could not find any clippings from a title matching '%s'!" % requested_book
    print >> sys.stderr, "Clippings file refers to the following titles:" 
    for book_name in titles.keys():        
        print >> sys.stderr, "\t", book_name.encode('ascii', 'replace')

    sys.exit(1)
    
if __name__ == '__main__':
    main()
