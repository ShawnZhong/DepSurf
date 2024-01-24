#pragma once

#include "vmlinux.h"

#include "utils/is_target.h"
#include "utils/write_user.h"

SEC("tracepoint/syscalls/sys_enter_newfstatat")
int enter_fstatfs(struct trace_event_raw_sys_enter *ctx) {
  if (!is_target_proc()) return 0;

  if (ctx->args[0] != 123456) {
    return 0;
  }
  write_user(ctx->args[2]);

  return 0;
}
