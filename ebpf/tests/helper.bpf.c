#include "vmlinux.h"

#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "GPL";

struct {
  __uint(type, BPF_MAP_TYPE_INODE_STORAGE);
  __uint(map_flags, BPF_F_NO_PREALLOC);
  __type(key, int);
  __type(value, 0);
} inode_storage_map SEC(".maps");

// SEC("xdp")
// SEC("lwt_in")
// SEC("socket")
// SEC("cgroup/dev")
// SEC("lsm/file_open")
// SEC("kprobe/vfs_open")
SEC("uprobe//proc/self/exe:uprobed_sub")
int prog(void* ctx) {
  char buf;
  void* ptr = (void*)0xffffa1b713b5d788;
  int rc = bpf_probe_read_kernel(&buf, 1, ptr);
  bpf_printk("rc: %d", rc);
  return 0;

  //   return bpf_skb_load_bytes(ctx, 0, &buf, 1) == 0;
  // bpf_inode_storage_get(&inode_storage_map, 0x0, 0x0, 0);
  // return 0;

  // return XDP_PASS;
}
