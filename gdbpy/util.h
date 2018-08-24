#ifndef UTIL_H
#define UTIL_H

void * xzalloc(size_t size);
void * xcalloc(size_t count, size_t size);
void * xzalloc(size_t size);
void * xmalloc(size_t size);
void * xrealloc(void *p, size_t size);
void * xmemdup(const void *p_, size_t size);
char * xmemdup0(const char *p_, size_t length);
char * xstrdup(const char *s);

#endif

