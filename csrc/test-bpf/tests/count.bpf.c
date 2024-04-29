
#include "vmlinux.h"
// Must be included first

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct {
  __uint(type, BPF_MAP_TYPE_ARRAY);
  __type(key, u32);
  __type(value, u32);
  __uint(max_entries, 1);
} enter_open_map SEC(".maps");

static __always_inline void count(void *map) {
  u32 key = 0;
  u32 *ptr = bpf_map_lookup_elem(map, &key);

  if (ptr) {
    *ptr += 1;  // non-atomic increment
    if (*ptr < 1000) {
      bpf_printk("count %d", *ptr);
    }
  } else {
    u32 init_val = 1;
    bpf_map_update_elem(map, &key, &init_val, BPF_NOEXIST);
    bpf_printk("init %d", init_val);
  }
}

SEC("tracepoint/syscalls/sys_enter_sched_getparam")
int trace_enter_open_at(void *ctx) {
  count(&enter_open_map);
  return 0;
}
