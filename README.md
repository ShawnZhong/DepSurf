```python
from bcc import BPF

text = R"""
void trace() {
    bpf_trace_printk("Hello, World!\n");
};
"""

b = BPF(text=text)
b.attach_kprobe(event="???", fn_name="trace")

while 1:
    b.trace_print(fmt="{5}")
```

```py
print(b.disassemble_func("trace"))
```


```sh
cat /proc/kallsyms | grep execv
```



```c
void trace() {
    bpf_trace_printk("Hello, World!\n");
};
```

```c
void trace() {
    while(1) bpf_trace_printk("Hello, World!\n");
};
```

https://github.com/torvalds/linux/blob/master/fs/exec.c#L2108
```c
SYSCALL_DEFINE3(execve,
                const char __user *, filename,
                const char __user *const __user *, argv,
                const char __user *const __user *, envp)
{
        return do_execve(getname(filename), argv, envp);
}
```

https://github.com/torvalds/linux/blob/master/fs/exec.c#L2031-L2038
```c
static int do_execve(struct filename *filename,
        const char __user *const __user *__argv,
        const char __user *const __user *__envp)
{
        struct user_arg_ptr argv = { .ptr.native = __argv };
        struct user_arg_ptr envp = { .ptr.native = __envp };
        return do_execveat_common(AT_FDCWD, filename, argv, envp, 0);
}
```

https://github.com/torvalds/linux/blob/master/fs/exec.c#L1887-L1890
```c
static int do_execveat_common(int fd, struct filename *filename,
                              struct user_arg_ptr argv,
                              struct user_arg_ptr envp,
                              int flags)
```

```c
#include <uapi/linux/ptrace.h>
void trace(struct pt_regs *ctx) { // PT stands for program trace
    char **filename = (char **)ctx->regs[1]; // non-portable
    bpf_trace_printk("filename = %s\n", *filename);
};
```

```c
#include <uapi/linux/ptrace.h>
void trace(struct pt_regs *ctx) {
    char **filename = (char **) PT_REGS_PARM2(ctx);
    bpf_trace_printk("filename = %s\n", *filename);
};
```


```c
#include <uapi/linux/ptrace.h>
void trace(struct pt_regs *ctx, int dfd, char **filename) {
    bpf_trace_printk("dfd = %d, filename = %s\n", dfd, *filename);
};
```

https://man7.org/linux/man-pages/man7/bpf-helpers.7.html

```c
#include <uapi/linux/ptrace.h>
void trace(struct pt_regs *ctx, int dfd, char **filename) {
    u64 ts = bpf_ktime_get_ns();

    bpf_trace_printk("ts = %ld, dfd = %d, filename = %s\n", ts, dfd, *filename);

    char comm[128];
    bpf_get_current_comm(&comm, sizeof(comm));

    u64 pid_tgid = bpf_get_current_pid_tgid();
    
    // pid is the lower 32 bits, corresponding to tid in userspace
    u32 pid = pid_tgid;

    // tgid is the higher 32 bits, corresponding to pid in userspace
    u32 tgid = pid_tgid >> 32;

    bpf_trace_printk("comm = %s, pid = %d, tgid = %d\n", comm, pid, tgid);
};
```


```python
from bcc import BPF
import time

text = R"""
#include <uapi/linux/ptrace.h>

struct key_t {
    char comm[16];
};

BPF_HASH(map, struct key_t, u64);

void trace(struct pt_regs *ctx, int dfd, char **filename) {
    struct key_t key;
    for (int i = 0; i < 16; i++) {
        key.comm[i] = (*filename)[i];
    }
    map.increment(key);
};
"""

b = BPF(text=text)
b.attach_kprobe(event="do_execveat_common", fn_name="trace")

while 1:
    for k, v in b["map"].items():
        print(k.comm, v.value)
    print("----")
    time.sleep(1)

```

```c
void trace_ret(struct pt_regs *ctx) {
    u64 ts = bpf_ktime_get_ns();
    u64 ret = PT_REGS_RC(ctx);
    bpf_trace_printk("ret = %ld, ts = %ld\n", ret, ts);
};
```

```c
#include <uapi/linux/ptrace.h>

BPF_HASH(map, u32, u64);

void trace(struct pt_regs *ctx, int dfd, char **filename) {
    u32 pid = bpf_get_current_pid_tgid();
    u64 start = bpf_ktime_get_ns();
    map.update(&pid, &start);
    bpf_trace_printk("start = %ld, filename = %s\n", start, *filename);
};

void trace_ret(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid();
    u64 *start = map.lookup(&pid);
    if (start == 0) return;
    u64 end = bpf_ktime_get_ns();
    u64 delta = end - *start;
    bpf_trace_printk("  end = %ld, delta = %ld\n", end, delta);
    map.delete(&pid);
};
```

We want to add a tracepoint to the `do_execveat_common` function. 

To add a new event, add the following to `trace/events/sched.h`
```c
TRACE_EVENT(sched_exec, // defines the function named `trace_sched_exec`
    TP_PROTO(struct filename *filename), // defines the function prototype

    TP_ARGS(filename), // defines the function arguments

    TP_STRUCT__entry( // defines the struct `trace_event_sched_exec`
        __field(char *, filename)
    ),
    TP_fast_assign( // defines the function body
        memcpy(__entry->filename, filename->name, sizeof(filename->name));
    )
)
```

https://github.com/torvalds/linux/commit/4ff16c25e2cc48cbe6956e356c38a25ac063a64d


```sh
sudo find /sys/kernel/tracing -name "*exec*"
```

```sh
sudo cat /sys/kernel/tracing/events/sched/sched_process_exec/format
```

```c
TRACEPOINT_PROBE(sched, sched_process_exec) {
   bpf_trace_printk("%d\n", args->pid);
}
```


```c
#include <linux/binfmts.h>

RAW_TRACEPOINT_PROBE(sched_process_exec) {
   // TP_PROTO(struct task_struct *p, pid_t old_pid, struct linux_binprm *bprm)
   struct linux_binprm *bprm = (struct linux_binprm *)ctx->args[2];
   bpf_trace_printk("%s\n", bprm->filename);
}
```
