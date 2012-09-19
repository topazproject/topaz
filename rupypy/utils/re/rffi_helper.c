#include "rffi_helper.h"
    
/* expects ->pattern and ->flags to be set by the caller */
int compile(struct re_data *data)
{
    int onig_option = 0;
        
    if(data->flags & 2)
        onig_option |= ONIG_OPTION_EXTEND;
    if(data->flags & 4)
        onig_option |= ONIG_OPTION_IGNORECASE;
    if(data->flags & 8)
        onig_option |= ONIG_OPTION_MULTILINE;
    
    data->einfo = (OnigErrorInfo *)malloc(sizeof(OnigErrorInfo));
        
    /* do not know about the other flags */
        
    data->r = onig_new(&data->reg,
                       (const OnigUChar *)data->pattern,
                       (const OnigUChar *)(data->pattern + strlen(data->pattern)),
                       onig_option,
                       ONIG_ENCODING_ASCII,
                       ONIG_SYNTAX_DEFAULT,
                       data->einfo);
    data->region = onig_region_new();
    return data->r;
}
    
/* expects ->str to be set by the caller, 
   and data to be initialized beforehand (by calling compile)*/
int search(struct re_data *data)
{
    const OnigUChar *start, *range, *end;
    int onig_option = 0;
        
    if(data->flags & 2)
        onig_option |= ONIG_OPTION_EXTEND;
    if(data->flags & 4)
        onig_option |= ONIG_OPTION_IGNORECASE;
    if(data->flags & 8)
        onig_option |= ONIG_OPTION_MULTILINE;
        
    end = (const OnigUChar *)(data->str + strlen(data->str));
    start = (const OnigUChar *)data->str;
    range = end;
        
    data->r = onig_search(data->reg, start, end, 
                       start, range, data->region,
                       onig_option);
    /* just to reduce the nessecary rffi code */
    data->num_regs = data->region->num_regs;
    data->beg = data->region->beg;
    data->end = data->region->end;
    
    if(data->beg[0] == -1 && data->end[0] == -1)
        return 0;   
    return 1;
}

char *get_encoding(struct re_data *data)
{
    OnigEncodingType* enc = (OnigEncodingType*)onig_get_encoding(data->reg);
    return (char *)enc->name;
}

int cleanup(struct re_data *data)
{
    onig_region_free(data->region, 1);
    onig_free(data->reg);
    free(data);
    return 0;
}
