import re


start_regex = re.compile ("/\*")
end_regex = re.compile ("\*/")
cpyr_regex = re.compile ("Copyright")

def add_trailer(fd):
    sz = 5
    rew_pos = None
    trailer = ""
    while sz:
        rew_pos = fd.tell()
        l = fd.readline()
        if start_regex.search (l):
            fd.seek(rew_pos)
            return trailer
        trailer += l
        sz -= 1
    return trailer


def next_block(fd, min_sz):
    """
    min_sz: min num lines of comment
    returns "" at eof

    >>> import StringIO
    >>> sbuf = StringIO.StringIO('/*abc\\ndef\\nxyz*/')
    >>> next_block(sbuf, 2)
    '/*abc\\ndef\\nxyz*/'
    """

    """
    >>> sbuf = StringIO.StringIO("abc\n  /* bla \nbla\nbla*/\ndkfj\n")
    IO.StringIO('/*abc\\ndef\\nxyz*/')
    /* bla \\nbla\\nbla*/'
    """

    block = ""
    in_block = False
    l = 1
    sz = 0
    while l:
        l = fd.readline()
        #print l.strip()
        if start_regex.search (l):
            in_block = True
            #print "START ",
        if in_block:
            block += l
            sz += 1
            #print "APPEND"
        if end_regex.search (l) or cpyr_regex.search (l):
            if sz >= min_sz:
                block += add_trailer(fd)
                return block
            in_block = False
            block = ""
            sz = 0

    return ""

def main():
    fd = open ("./doit.c")
    blk = next_block(fd, 5)
    while blk:
        print blk
        blk = next_block(fd, 5)


if __name__ == "__main__":
    main()
