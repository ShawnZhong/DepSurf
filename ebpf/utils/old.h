// #include "vmlinux.h"
//
// #include <bpf/bpf_helpers.h>
// #include <bpf/bpf_tracing.h>
//
// #define pgoff_t unsigned long
//
// #define COMM_SIZE 16
// #define NAME_SIZE 32
//
// const volatile unsigned long long target_tid = -1;
// const volatile char target_comm[COMM_SIZE] = "";
// const volatile char target_name[NAME_SIZE] = "";
//
// static bool is_str_eq(const char *str1, const volatile char *str2, int size)
// {
//     for (int i = 0; i < size; i++) {
//         if (str1[i] == '\0') break;
//         if (str1[i] != str2[i]) return false;
//     }
//     return true;
// }
//
// static bool is_target_comm() {
//     if (target_comm[0] == '\0') return true;
//     char comm[COMM_SIZE];
//     bpf_get_current_comm(&comm, sizeof(comm));
//     return is_str_eq(comm, target_comm, sizeof(comm));
// }
//
// static bool is_target_tid() {
//     return (target_tid == -1) || (bpf_get_current_pid_tgid() == target_tid);
// }
//
// static bool is_target_proc() { return is_target_tid() && is_target_comm(); }
//
// static bool is_target_name(const char *name) {
//     if (name == NULL) return false;
//     if (target_name[0] == '\0') return true;
//     return is_str_eq(name, target_name, sizeof(target_name));
// }
//
//
// static struct inode *get_inode_from_file(struct file *file) {
//     struct inode *inode;
//     bpf_probe_read(&inode, sizeof(inode), &file->f_inode);
//     return inode;
// }
//
// static int get_ino_from_inode(struct inode *inode) {
//     int ino;
//     bpf_probe_read(&ino, sizeof(ino), &inode->i_ino);
//     return ino;
// }
//
// static struct dentry *get_dentry_from_file(struct file *file) {
//     struct dentry *dentry;
//     bpf_probe_read(&dentry, sizeof(dentry), &file->f_path.dentry);
//     return dentry;
// }
//
// static char *get_name_from_dentry(struct dentry *dentry) {
//     static char d_iname[32];
//     bpf_probe_read(&d_iname, sizeof(d_iname), &dentry->d_iname);
//     return d_iname;
// }
//
// static char *get_dname_from_file(struct file *file) {
//     struct dentry *dentry = get_dentry_from_file(file);
//     if (dentry == NULL) return NULL;
//
//     return get_name_from_dentry(dentry);
// }
//
// #if 0
//
// static void print_flags(unsigned int f) {
//     if (f & FAULT_FLAG_WRITE) bpf_printk("WRITE");
//     if (f & FAULT_FLAG_MKWRITE) bpf_printk("MKWRITE");
//     if (f & FAULT_FLAG_ALLOW_RETRY) bpf_printk("ALLOW_RETRY");
//     if (f & FAULT_FLAG_RETRY_NOWAIT) bpf_printk("RETRY_NOWAIT");
//     if (f & FAULT_FLAG_KILLABLE) bpf_printk("KILLABLE");
//     if (f & FAULT_FLAG_TRIED) bpf_printk("TRIED");
//     if (f & FAULT_FLAG_USER) bpf_printk("USER");
//     if (f & FAULT_FLAG_REMOTE) bpf_printk("REMOTE");
//     if (f & FAULT_FLAG_INSTRUCTION) bpf_printk("INSTRUCTION");
//     if (f & FAULT_FLAG_INTERRUPTIBLE) bpf_printk("INTERRUPTIBLE");
// }
//
// static void print_fault_reason(vm_fault_t f) {
//     if (f & VM_FAULT_OOM) bpf_printk("OOM");
//     if (f & VM_FAULT_SIGBUS) bpf_printk("SIGBUS");
//     if (f & VM_FAULT_MAJOR) bpf_printk("MAJOR");
//     if (f & VM_FAULT_WRITE) bpf_printk("WRITE");
//     if (f & VM_FAULT_HWPOISON) bpf_printk("HWPOISON");
//     if (f & VM_FAULT_HWPOISON_LARGE) bpf_printk("HWPOISON_LARGE");
//     if (f & VM_FAULT_SIGSEGV) bpf_printk("SIGSEGV");
//     if (f & VM_FAULT_NOPAGE) bpf_printk("NOPAGE");
//     if (f & VM_FAULT_LOCKED) bpf_printk("LOCKED");
//     if (f & VM_FAULT_RETRY) bpf_printk("RETRY");
//     if (f & VM_FAULT_FALLBACK) bpf_printk("FALLBACK");
//     if (f & VM_FAULT_DONE_COW) bpf_printk("DONE_COW");
//     if (f & VM_FAULT_NEEDDSYNC) bpf_printk("NEEDDSYNC");
//     if (f & VM_FAULT_HINDEX_MASK) bpf_printk("HINDEX_MASK");
// }
//
//
// struct {
//   __uint(type, BPF_MAP_TYPE_HASH);
//   __uint(max_entries, 8192);
//   __type(key, tid_t);
//   __type(value, unsigned long);
// } address_map SEC(".maps");
//
// SEC("kprobe/handle_mm_fault")
// int BPF_KPROBE(handle_mm_fault, struct vm_area_struct *vma,
//                unsigned long address, unsigned int flags,
//                struct pt_regs *regs) {
//   // only record the first fault
//   if (flags & FAULT_FLAG_TRIED) return 0;
//
//   if (!is_target_proc()) return 0;
//
//   char *d_iname = get_dname(vma);
//   if (!is_target_name(d_iname)) return 0;
//
//   print_flags(flags);
//
//   tid_t tid = bpf_get_current_pid_tgid();
//
//   bpf_printk("handle_mm_fault: tid %d, address %px, name %s", tid, address,
//              d_iname);
//
//   bpf_map_update_elem(&address_map, &tid, &address, BPF_ANY);
//   return 0;
// }
//
// SEC("kretprobe/handle_mm_fault")
// int BPF_KRETPROBE(handle_mm_fault_ret, vm_fault_t fault_ret) {
//   // ignore retry
//   if (fault_ret & VM_FAULT_RETRY) return 0;
//
//   if (!is_target_proc()) return 0;
//
//   tid_t tid = bpf_get_current_pid_tgid();
//   unsigned long *val = bpf_map_lookup_elem(&address_map, &tid);
//   if (val == NULL) return 0;
//   bpf_map_delete_elem(&address_map, &tid);
//
//   void *address = (void *)(*val & 0xfffffffffffff000);
//
//   bpf_printk("handle_mm_fault_ret: tid %d, address %px, ret %d", tid,
//   address,
//              fault_ret);
//
//   static char page[4096];
//   {
//     long ret = bpf_probe_read_user(page, sizeof(page), address);
//     if (ret != 0) {
//       bpf_printk("handle_mm_fault_ret: read_kernel(%px) failed: %d", address,
//                  ret);
//     } else {
//       bpf_printk("handle_mm_fault_ret: read_kernel(%px) succeeded", address);
//     }
//   }
//
//   for (int i = 0; i < sizeof(page); i++) {
//     if (page[i] == '\n') continue;
//     page[i] = page[i] + 1;
//   }
//
//   {
//     long ret = bpf_probe_write_user(address, page, sizeof(page));
//     if (ret != 0) {
//       bpf_printk("handle_mm_fault_ret: write_user(%px) failed: %d", address,
//                  ret);
//     } else {
//       bpf_printk("handle_mm_fault_ret: write_user(%px) succeeded", address);
//     }
//   }
//
//   return 0;
// }
//
// SEC("fentry/handle_mm_fault")
// int BPF_PROG(handle_mm_fault, struct vm_area_struct *vma,
//              unsigned long address, unsigned int flags,
//              struct pt_regs *regs) {
//     // only record the first fault
//     if (flags & FAULT_FLAG_TRIED) return 0;
//
//     if (!is_target_proc()) return 0;
//
//
//     char *d_iname = get_dname_from_file(vma->vm_file);
//     if (!is_target_name(d_iname)) return 0;
//
//     struct inode *inode = get_inode_from_file(vma->vm_file);
//     int ino = get_ino_from_inode(inode);
//
//     bpf_printk("handle_mm_fault: \"%s\", ino %d, address %px",
//                d_iname, ino, address);
//
//     return 0;
// }
//
// SEC("fentry/add_to_page_cache_lru")
// int BPF_PROG(add_to_page_cache_lru, struct page *page, struct address_space
// *mapping, pgoff_t offset, gfp_t gfp_mask) {
//     if (!is_target_proc()) return 0;
//
//     int ino = get_ino_from_inode(mapping->host);
//
//
//     bpf_printk("add_to_page_cache_lru: ino %d, pgoff %d", ino, offset);
//
//     return 0;
// }
// #endif
////
////struct {
////    __uint(type, BPF_MAP_TYPE_ARRAY);
////    __type(key, u32);
////    __type(value, u32);
////    __uint(max_entries, 1);
////} enter_open_map SEC(".maps");
////
////
////static __always_inline void count(void *map) {
////    u32 key = 0;
////    u32 *ptr = bpf_map_lookup_elem(map, &key);
////
////    if (ptr) {
////        *ptr += 1; // non-atomic increment
////        if (*ptr < 1000) {
////            bpf_printk("count %d", *ptr);
////        }
////    } else {
////        u32 init_val = 1;
////        bpf_map_update_elem(map, &key, &init_val, BPF_NOEXIST);
////        bpf_printk("init %d", init_val);
////    }
////}
//
////SEC("tracepoint/syscalls/sys_enter_sched_getparam")
////int trace_enter_open_at(void *ctx) {
////    count(&enter_open_map);
////    return 0;
////}
//
// char LICENSE[] SEC("license") = "Dual BSD/GPL";
//
//
// SEC("tracepoint/syscalls/sys_enter_newfstatat")
// int enter_fstatfs(struct trace_event_raw_sys_enter *ctx, int i, int j, int k,
// int x){
//  return 0;
//}
