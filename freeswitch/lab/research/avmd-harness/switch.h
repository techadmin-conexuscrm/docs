/* LAB ONLY: the few FreeSWITCH types and calls mod_avmd's detector code needs. */
#ifndef LAB_SWITCH_H
#define LAB_SWITCH_H
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
typedef void switch_core_session_t; typedef void switch_thread_t; typedef void switch_mutex_t;
typedef void switch_thread_cond_t; typedef int64_t switch_time_t;
#define switch_core_session_alloc(s, n) calloc(1, (n))
#define ISNAN(x) (isnan(x))
#define ISINF(x) (isinf(x))
#endif
