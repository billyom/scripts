#include <stdio.h>
#include <stdlib.h>

#include "util.h"

void*
fn1(void)
{
	return xzalloc(64);
}

void
main (void)
{
	void *p;
	p = fn1();
	p = xmemdup(p, 64);
	p = fn1();
	free(p);
}
