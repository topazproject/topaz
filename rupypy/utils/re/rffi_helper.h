#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "oniguruma.h"
    
struct re_data {
    int r;
    char *pattern;
    char *str;
    int flags;
    int num_regs;
    int *beg;
    int *end;
    /* we will need some encoding_data pointer when we have
       implemented the Encoding Object. I suggest that this
       will be tied to the oniguruma lib in a similar way, as
       is the case with the regexp module. */
    /* the following are onig-related vars: */
    regex_t *reg;
    OnigErrorInfo *einfo;
    OnigRegion *region;
};

int compile(struct re_data *data);
int search(struct re_data *data);
int cleanup(struct re_data *data);
char *get_encoding(struct re_data *data);
