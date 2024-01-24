from bcc import BPF

text = """
#include <linux/ptrace.h>
int trace(struct pt_regs *ctx) {
    bpf_trace_printk("close fd: %d", PT_REGS_PARM3(ctx));
    return 0;
}
"""

b = BPF(text=text)
b.attach_kprobe(event="close_fd", fn_name="trace")
b.trace_print()
