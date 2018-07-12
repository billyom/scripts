#include <stdio.h>
#include <stdlib.h>

#include "util.h"

void*
fn1(void)
{
	xzalloc(64);
}


void
main (void)
{
	void *p;
	p = fn1();
	p = fn1();
	free(p);
}
