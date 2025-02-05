from functools import cached_property
from pathlib import Path
from typing import Dict, List

from elftools.elf.elffile import ELFFile

from depsurf.btf import Kind, Types, dump_btf_json, dump_btf_txt, gen_min_btf
from depsurf.dep import Dep, DepKind


class BPFProgram:
    DEP_MAPPING: Dict[Dep, List[Dep]] = {}

    def __init__(self, path: Path):
        self.path = path
        self.file = open(path, "rb")
        self.elffile = ELFFile(self.file)

    def __del__(self):
        self.file.close()

    @property
    def name(self):
        return self.path.name.removesuffix(".o").removesuffix(".bpf")

    @property
    def btf_file(self):
        return self.path.with_suffix(".min.btf")

    @property
    def btf_json_file(self):
        return self.path.with_suffix(".min.btf.json")

    @property
    def btf_txt_file(self):
        return self.path.with_suffix(".min.btf.txt")

    @property
    def hook_names(self):
        return [
            section.name
            for section in self.elffile.iter_sections()
            if not section.name.startswith(".")
            and section.name != "license"
            and section.header.sh_type == "SHT_PROGBITS"
        ]

    @property
    def deps_hook(self) -> List[Dep]:
        results = []
        for hook_name in self.hook_names:
            kind = DepKind.from_hook_name(hook_name)
            if "/" in hook_name:
                name = hook_name.rsplit("/", 1)[-1]
            else:
                name = ""

            for prefix in ["sys_enter_", "sys_exit_"]:
                if kind == DepKind.SYSCALL and name.startswith(prefix):
                    name = name[len(prefix) :]

            results.append(Dep(kind, name))

        return results

    @property
    def deps_struct(self) -> list[Dep]:
        gen_min_btf(
            self.path,
            result_path=self.btf_file,
            slient=True,
        )
        dump_btf_json(
            self.btf_file,
            result_path=self.btf_json_file,
            slient=True,
        )
        dump_btf_txt(
            self.btf_file,
            result_path=self.btf_txt_file,
            slient=True,
        )
        struct_types = Types.from_btf_json(self.btf_json_file, Kind.STRUCT)

        results = []
        for name, struct in struct_types.items():
            name = name.split("___")[0]
            if name == "user_pt_regs":
                continue
            results.append(DepKind.STRUCT(name))
            for member in struct["members"]:
                results.append(DepKind.FIELD(f"{name}::{member['name']}"))

        return results

    @cached_property
    def deps(self) -> list[Dep]:
        deps = []
        for dep in set(self.deps_hook + self.deps_struct):
            if dep in BPFProgram.DEP_MAPPING:
                deps.extend(BPFProgram.DEP_MAPPING[dep])
            else:
                deps.append(dep)
        return sorted(deps)


BPFProgram.DEP_MAPPING = {
    # Used by fsdist and fsslower
    # Ref: https://github.com/iovisor/bcc/blob/fef9003e2e2f29c893543d49b762dd413a352f05/libbpf-tools/fsdist.c#L42-L81
    DepKind.FUNC("dummy_file_read"): [DepKind.FUNC("ext4_file_read_iter")],
    DepKind.FUNC("dummy_file_write"): [DepKind.FUNC("ext4_file_write_iter")],
    DepKind.FUNC("dummy_file_open"): [DepKind.FUNC("ext4_file_open")],
    DepKind.FUNC("dummy_file_sync"): [DepKind.FUNC("ext4_sync_file")],
    DepKind.FUNC("dummy_getattr"): [DepKind.FUNC("ext4_file_getattr")],
    # Used by ksnoop
    DepKind.FUNC("foo"): [],
    # Used by funclatency
    DepKind.FUNC("dummy_fentry"): [],
    DepKind.FUNC("dummy_fexit"): [],
    DepKind.FUNC("dummy_kprobe"): [],
    DepKind.FUNC("dummy_kretprobe"): [],
    # Used by readahead
    # https://github.com/iovisor/bcc/blob/1d8daaa395f066b328a56a36fbd40a0de3a7b3c1/libbpf-tools/readahead.c#L79
    DepKind.FUNC("do_page_cache_ra"): [
        DepKind.FUNC("do_page_cache_ra"),
        DepKind.FUNC("__do_page_cache_readahead"),
    ],
    # Used by tracee
    # https://github.com/aquasecurity/tracee/blob/4fc1bbb2b99333be869e49a333fc3dd17c176137/pkg/ebpf/probes/probe_group.go
    # https://github.com/aquasecurity/tracee/blob/4fc1bbb2b99333be869e49a333fc3dd17c176137/pkg/events/core.go
    # https://github.com/aquasecurity/tracee/blob/4fc1bbb2b99333be869e49a333fc3dd17c176137/pkg/ebpf/c/tracee.bpf.c
    DepKind.FUNC("__kernel_write_tail"): [DepKind.FUNC("__kernel_write")],
    DepKind.FUNC("vfs_read_tail"): [DepKind.FUNC("vfs_read")],
    DepKind.FUNC("vfs_readv_tail"): [DepKind.FUNC("vfs_readv")],
    DepKind.FUNC("vfs_write_tail"): [DepKind.FUNC("vfs_write")],
    DepKind.FUNC("vfs_writev_tail"): [DepKind.FUNC("vfs_writev")],
    DepKind.FUNC("empty_kprobe"): [],
    DepKind.FUNC("execute_finished"): [
        DepKind.SYSCALL("execve"),
        DepKind.SYSCALL("execveat"),
    ],
    DepKind.FUNC("send_bin"): [],
    DepKind.FUNC("trace_execute_failed1"): [],
    DepKind.FUNC("trace_execute_failed2"): [],
    DepKind.TRACEPOINT("send_bin_tp"): [],
    DepKind.TRACEPOINT("exec_test"): [],
    DepKind.TRACEPOINT("cgroup_mkdir_signal"): [DepKind.TRACEPOINT("cgroup_mkdir")],
    DepKind.TRACEPOINT("cgroup_rmdir_signal"): [DepKind.TRACEPOINT("cgroup_rmdir")],
    DepKind.TRACEPOINT("sched_process_exec_event_submit_tail"): [
        DepKind.TRACEPOINT("sched_process_exec")
    ],
    DepKind.TRACEPOINT("syscall__accept4"): [DepKind.SYSCALL("accept4")],
    DepKind.TRACEPOINT("sys_dup"): [DepKind.SYSCALL("dup")],
    DepKind.TRACEPOINT("sys_execve"): [DepKind.SYSCALL("execve")],
    DepKind.TRACEPOINT("sys_execveat"): [DepKind.SYSCALL("execveat")],
    DepKind.TRACEPOINT("sys_init_module"): [DepKind.SYSCALL("init_module")],
    DepKind.TRACEPOINT("sys_enter_init"): [],
    DepKind.TRACEPOINT("sys_exit_init"): [],
    DepKind.TRACEPOINT("sys_enter_submit"): [],
    DepKind.TRACEPOINT("sys_exit_submit"): [],
    # DepKind.TRACEPOINT("sys_enter"): [],
    # DepKind.TRACEPOINT("sys_exit"): [],
    DepKind.TRACEPOINT("trace_sys_enter"): [],
    DepKind.TRACEPOINT("trace_sys_exit"): [
        DepKind.SYSCALL("read"),
        DepKind.SYSCALL("write"),
        DepKind.SYSCALL("open"),
        DepKind.SYSCALL("close"),
        DepKind.SYSCALL("stat"),
        DepKind.SYSCALL("fstat"),
        DepKind.SYSCALL("lstat"),
        DepKind.SYSCALL("poll"),
        DepKind.SYSCALL("lseek"),
        DepKind.SYSCALL("mmap"),
        DepKind.SYSCALL("mprotect"),
        DepKind.SYSCALL("munmap"),
        DepKind.SYSCALL("brk"),
        DepKind.SYSCALL("rt_sigaction"),
        DepKind.SYSCALL("rt_sigprocmask"),
        DepKind.SYSCALL("rt_sigreturn"),
        DepKind.SYSCALL("ioctl"),
        DepKind.SYSCALL("pread64"),
        DepKind.SYSCALL("pwrite64"),
        DepKind.SYSCALL("readv"),
        DepKind.SYSCALL("writev"),
        DepKind.SYSCALL("access"),
        DepKind.SYSCALL("pipe"),
        DepKind.SYSCALL("select"),
        DepKind.SYSCALL("sched_yield"),
        DepKind.SYSCALL("mremap"),
        DepKind.SYSCALL("msync"),
        DepKind.SYSCALL("mincore"),
        DepKind.SYSCALL("madvise"),
        DepKind.SYSCALL("shmget"),
        DepKind.SYSCALL("shmat"),
        DepKind.SYSCALL("shmctl"),
        DepKind.SYSCALL("dup"),
        DepKind.SYSCALL("dup2"),
        DepKind.SYSCALL("pause"),
        DepKind.SYSCALL("nanosleep"),
        DepKind.SYSCALL("getitimer"),
        DepKind.SYSCALL("alarm"),
        DepKind.SYSCALL("setitimer"),
        DepKind.SYSCALL("getpid"),
        DepKind.SYSCALL("sendfile"),
        DepKind.SYSCALL("socket"),
        DepKind.SYSCALL("connect"),
        DepKind.SYSCALL("accept"),
        DepKind.SYSCALL("sendto"),
        DepKind.SYSCALL("recvfrom"),
        DepKind.SYSCALL("sendmsg"),
        DepKind.SYSCALL("recvmsg"),
        DepKind.SYSCALL("shutdown"),
        DepKind.SYSCALL("bind"),
        DepKind.SYSCALL("listen"),
        DepKind.SYSCALL("getsockname"),
        DepKind.SYSCALL("getpeername"),
        DepKind.SYSCALL("socketpair"),
        DepKind.SYSCALL("setsockopt"),
        DepKind.SYSCALL("getsockopt"),
        DepKind.SYSCALL("clone"),
        DepKind.SYSCALL("fork"),
        DepKind.SYSCALL("vfork"),
        DepKind.SYSCALL("execve"),
        DepKind.SYSCALL("exit"),
        DepKind.SYSCALL("wait4"),
        DepKind.SYSCALL("kill"),
        DepKind.SYSCALL("uname"),
        DepKind.SYSCALL("semget"),
        DepKind.SYSCALL("semop"),
        DepKind.SYSCALL("semctl"),
        DepKind.SYSCALL("shmdt"),
        DepKind.SYSCALL("msgget"),
        DepKind.SYSCALL("msgsnd"),
        DepKind.SYSCALL("msgrcv"),
        DepKind.SYSCALL("msgctl"),
        DepKind.SYSCALL("fcntl"),
        DepKind.SYSCALL("flock"),
        DepKind.SYSCALL("fsync"),
        DepKind.SYSCALL("fdatasync"),
        DepKind.SYSCALL("truncate"),
        DepKind.SYSCALL("ftruncate"),
        DepKind.SYSCALL("getdents"),
        DepKind.SYSCALL("getcwd"),
        DepKind.SYSCALL("chdir"),
        DepKind.SYSCALL("fchdir"),
        DepKind.SYSCALL("rename"),
        DepKind.SYSCALL("mkdir"),
        DepKind.SYSCALL("rmdir"),
        DepKind.SYSCALL("creat"),
        DepKind.SYSCALL("link"),
        DepKind.SYSCALL("unlink"),
        DepKind.SYSCALL("symlink"),
        DepKind.SYSCALL("readlink"),
        DepKind.SYSCALL("chmod"),
        DepKind.SYSCALL("fchmod"),
        DepKind.SYSCALL("chown"),
        DepKind.SYSCALL("fchown"),
        DepKind.SYSCALL("lchown"),
        DepKind.SYSCALL("umask"),
        DepKind.SYSCALL("gettimeofday"),
        DepKind.SYSCALL("getrlimit"),
        DepKind.SYSCALL("getrusage"),
        DepKind.SYSCALL("sysinfo"),
        DepKind.SYSCALL("times"),
        DepKind.SYSCALL("ptrace"),
        DepKind.SYSCALL("getuid"),
        DepKind.SYSCALL("syslog"),
        DepKind.SYSCALL("getgid"),
        DepKind.SYSCALL("setuid"),
        DepKind.SYSCALL("setgid"),
        DepKind.SYSCALL("geteuid"),
        DepKind.SYSCALL("getegid"),
        DepKind.SYSCALL("setpgid"),
        DepKind.SYSCALL("getppid"),
        DepKind.SYSCALL("getpgrp"),
        DepKind.SYSCALL("setsid"),
        DepKind.SYSCALL("setreuid"),
        DepKind.SYSCALL("setregid"),
        DepKind.SYSCALL("getgroups"),
        DepKind.SYSCALL("setgroups"),
        DepKind.SYSCALL("setresuid"),
        DepKind.SYSCALL("getresuid"),
        DepKind.SYSCALL("setresgid"),
        DepKind.SYSCALL("getresgid"),
        DepKind.SYSCALL("getpgid"),
        DepKind.SYSCALL("setfsuid"),
        DepKind.SYSCALL("setfsgid"),
        DepKind.SYSCALL("getsid"),
        DepKind.SYSCALL("capget"),
        DepKind.SYSCALL("capset"),
        DepKind.SYSCALL("rt_sigpending"),
        DepKind.SYSCALL("rt_sigtimedwait"),
        DepKind.SYSCALL("rt_sigqueueinfo"),
        DepKind.SYSCALL("rt_sigsuspend"),
        DepKind.SYSCALL("sigaltstack"),
        DepKind.SYSCALL("utime"),
        DepKind.SYSCALL("mknod"),
        DepKind.SYSCALL("uselib"),
        DepKind.SYSCALL("personality"),
        DepKind.SYSCALL("ustat"),
        DepKind.SYSCALL("statfs"),
        DepKind.SYSCALL("fstatfs"),
        DepKind.SYSCALL("sysfs"),
        DepKind.SYSCALL("getpriority"),
        DepKind.SYSCALL("setpriority"),
        DepKind.SYSCALL("sched_setparam"),
        DepKind.SYSCALL("sched_getparam"),
        DepKind.SYSCALL("sched_setscheduler"),
        DepKind.SYSCALL("sched_getscheduler"),
        DepKind.SYSCALL("sched_get_priority_max"),
        DepKind.SYSCALL("sched_get_priority_min"),
        DepKind.SYSCALL("sched_rr_get_interval"),
        DepKind.SYSCALL("mlock"),
        DepKind.SYSCALL("munlock"),
        DepKind.SYSCALL("mlockall"),
        DepKind.SYSCALL("munlockall"),
        DepKind.SYSCALL("vhangup"),
        DepKind.SYSCALL("modify_ldt"),
        DepKind.SYSCALL("pivot_root"),
        DepKind.SYSCALL("sysctl"),
        DepKind.SYSCALL("prctl"),
        DepKind.SYSCALL("arch_prctl"),
        DepKind.SYSCALL("adjtimex"),
        DepKind.SYSCALL("setrlimit"),
        DepKind.SYSCALL("chroot"),
        DepKind.SYSCALL("sync"),
        DepKind.SYSCALL("acct"),
        DepKind.SYSCALL("settimeofday"),
        DepKind.SYSCALL("mount"),
        DepKind.SYSCALL("umount2"),
        DepKind.SYSCALL("swapon"),
        DepKind.SYSCALL("swapoff"),
        DepKind.SYSCALL("reboot"),
        DepKind.SYSCALL("sethostname"),
        DepKind.SYSCALL("setdomainname"),
        DepKind.SYSCALL("iopl"),
        DepKind.SYSCALL("ioperm"),
        DepKind.SYSCALL("create_module"),
        DepKind.SYSCALL("init_module"),
        DepKind.SYSCALL("delete_module"),
        DepKind.SYSCALL("get_kernel_syms"),
        DepKind.SYSCALL("query_module"),
        DepKind.SYSCALL("quotactl"),
        DepKind.SYSCALL("nfsservctl"),
        DepKind.SYSCALL("getpmsg"),
        DepKind.SYSCALL("putpmsg"),
        DepKind.SYSCALL("afs"),
        DepKind.SYSCALL("tuxcall"),
        DepKind.SYSCALL("security"),
        DepKind.SYSCALL("gettid"),
        DepKind.SYSCALL("readahead"),
        DepKind.SYSCALL("setxattr"),
        DepKind.SYSCALL("lsetxattr"),
        DepKind.SYSCALL("fsetxattr"),
        DepKind.SYSCALL("getxattr"),
        DepKind.SYSCALL("lgetxattr"),
        DepKind.SYSCALL("fgetxattr"),
        DepKind.SYSCALL("listxattr"),
        DepKind.SYSCALL("llistxattr"),
        DepKind.SYSCALL("flistxattr"),
        DepKind.SYSCALL("removexattr"),
        DepKind.SYSCALL("lremovexattr"),
        DepKind.SYSCALL("fremovexattr"),
        DepKind.SYSCALL("tkill"),
        DepKind.SYSCALL("time"),
        DepKind.SYSCALL("futex"),
        DepKind.SYSCALL("sched_setaffinity"),
        DepKind.SYSCALL("sched_getaffinity"),
        DepKind.SYSCALL("set_thread_area"),
        DepKind.SYSCALL("io_setup"),
        DepKind.SYSCALL("io_destroy"),
        DepKind.SYSCALL("io_getevents"),
        DepKind.SYSCALL("io_submit"),
        DepKind.SYSCALL("io_cancel"),
        DepKind.SYSCALL("get_thread_area"),
        DepKind.SYSCALL("lookup_dcookie"),
        DepKind.SYSCALL("epoll_create"),
        DepKind.SYSCALL("epoll_ctl_old"),
        DepKind.SYSCALL("epoll_wait_old"),
        DepKind.SYSCALL("remap_file_pages"),
        DepKind.SYSCALL("getdents64"),
        DepKind.SYSCALL("set_tid_address"),
        DepKind.SYSCALL("restart_syscall"),
        DepKind.SYSCALL("semtimedop"),
        DepKind.SYSCALL("fadvise64"),
        DepKind.SYSCALL("timer_create"),
        DepKind.SYSCALL("timer_settime"),
        DepKind.SYSCALL("timer_gettime"),
        DepKind.SYSCALL("timer_getoverrun"),
        DepKind.SYSCALL("timer_delete"),
        DepKind.SYSCALL("clock_settime"),
        DepKind.SYSCALL("clock_gettime"),
        DepKind.SYSCALL("clock_getres"),
        DepKind.SYSCALL("clock_nanosleep"),
        DepKind.SYSCALL("exit_group"),
        DepKind.SYSCALL("epoll_wait"),
        DepKind.SYSCALL("epoll_ctl"),
        DepKind.SYSCALL("tgkill"),
        DepKind.SYSCALL("utimes"),
        DepKind.SYSCALL("vserver"),
        DepKind.SYSCALL("mbind"),
        DepKind.SYSCALL("set_mempolicy"),
        DepKind.SYSCALL("get_mempolicy"),
        DepKind.SYSCALL("mq_open"),
        DepKind.SYSCALL("mq_unlink"),
        DepKind.SYSCALL("mq_timedsend"),
        DepKind.SYSCALL("mq_timedreceive"),
        DepKind.SYSCALL("mq_notify"),
        DepKind.SYSCALL("mq_getsetattr"),
        DepKind.SYSCALL("kexec_load"),
        DepKind.SYSCALL("waitid"),
        DepKind.SYSCALL("add_key"),
        DepKind.SYSCALL("request_key"),
        DepKind.SYSCALL("keyctl"),
        DepKind.SYSCALL("ioprio_set"),
        DepKind.SYSCALL("ioprio_get"),
        DepKind.SYSCALL("inotify_init"),
        DepKind.SYSCALL("inotify_add_watch"),
        DepKind.SYSCALL("inotify_rm_watch"),
        DepKind.SYSCALL("migrate_pages"),
        DepKind.SYSCALL("openat"),
        DepKind.SYSCALL("mkdirat"),
        DepKind.SYSCALL("mknodat"),
        DepKind.SYSCALL("fchownat"),
        DepKind.SYSCALL("futimesat"),
        DepKind.SYSCALL("newfstatat"),
        DepKind.SYSCALL("unlinkat"),
        DepKind.SYSCALL("renameat"),
        DepKind.SYSCALL("linkat"),
        DepKind.SYSCALL("symlinkat"),
        DepKind.SYSCALL("readlinkat"),
        DepKind.SYSCALL("fchmodat"),
        DepKind.SYSCALL("faccessat"),
        DepKind.SYSCALL("pselect6"),
        DepKind.SYSCALL("ppoll"),
        DepKind.SYSCALL("unshare"),
        DepKind.SYSCALL("set_robust_list"),
        DepKind.SYSCALL("get_robust_list"),
        DepKind.SYSCALL("splice"),
        DepKind.SYSCALL("tee"),
        DepKind.SYSCALL("sync_file_range"),
        DepKind.SYSCALL("vmsplice"),
        DepKind.SYSCALL("move_pages"),
        DepKind.SYSCALL("utimensat"),
        DepKind.SYSCALL("epoll_pwait"),
        DepKind.SYSCALL("signalfd"),
        DepKind.SYSCALL("timerfd_create"),
        DepKind.SYSCALL("eventfd"),
        DepKind.SYSCALL("fallocate"),
        DepKind.SYSCALL("timerfd_settime"),
        DepKind.SYSCALL("timerfd_gettime"),
        DepKind.SYSCALL("accept4"),
        DepKind.SYSCALL("signalfd4"),
        DepKind.SYSCALL("eventfd2"),
        DepKind.SYSCALL("epoll_create1"),
        DepKind.SYSCALL("dup3"),
        DepKind.SYSCALL("pipe2"),
        DepKind.SYSCALL("inotify_init1"),
        DepKind.SYSCALL("preadv"),
        DepKind.SYSCALL("pwritev"),
        DepKind.SYSCALL("rt_tgsigqueueinfo"),
        DepKind.SYSCALL("perf_event_open"),
        DepKind.SYSCALL("recvmmsg"),
        DepKind.SYSCALL("fanotify_init"),
        DepKind.SYSCALL("fanotify_mark"),
        DepKind.SYSCALL("prlimit64"),
        DepKind.SYSCALL("name_to_handle_at"),
        DepKind.SYSCALL("open_by_handle_at"),
        DepKind.SYSCALL("clock_adjtime"),
        DepKind.SYSCALL("syncfs"),
        DepKind.SYSCALL("sendmmsg"),
        DepKind.SYSCALL("setns"),
        DepKind.SYSCALL("getcpu"),
        DepKind.SYSCALL("process_vm_readv"),
        DepKind.SYSCALL("process_vm_writev"),
        DepKind.SYSCALL("kcmp"),
        DepKind.SYSCALL("finit_module"),
        DepKind.SYSCALL("sched_setattr"),
        DepKind.SYSCALL("sched_getattr"),
        DepKind.SYSCALL("renameat2"),
        DepKind.SYSCALL("seccomp"),
        DepKind.SYSCALL("getrandom"),
        DepKind.SYSCALL("memfd_create"),
        DepKind.SYSCALL("kexec_file_load"),
        DepKind.SYSCALL("bpf"),
        DepKind.SYSCALL("execveat"),
        DepKind.SYSCALL("userfaultfd"),
        DepKind.SYSCALL("membarrier"),
        DepKind.SYSCALL("mlock2"),
        DepKind.SYSCALL("copy_file_range"),
        DepKind.SYSCALL("preadv2"),
        DepKind.SYSCALL("pwritev2"),
        DepKind.SYSCALL("pkey_mprotect"),
        DepKind.SYSCALL("pkey_alloc"),
        DepKind.SYSCALL("pkey_free"),
        DepKind.SYSCALL("statx"),
        DepKind.SYSCALL("io_pgetevents"),
        DepKind.SYSCALL("rseq"),
        DepKind.SYSCALL("pidfd_send_signal"),
        DepKind.SYSCALL("io_uring_setup"),
        DepKind.SYSCALL("io_uring_enter"),
        DepKind.SYSCALL("io_uring_register"),
        DepKind.SYSCALL("open_tree"),
        DepKind.SYSCALL("move_mount"),
        DepKind.SYSCALL("fsopen"),
        DepKind.SYSCALL("fsconfig"),
        DepKind.SYSCALL("fsmount"),
        DepKind.SYSCALL("fspick"),
        DepKind.SYSCALL("pidfd_open"),
        DepKind.SYSCALL("clone3"),
        DepKind.SYSCALL("close_range"),
        DepKind.SYSCALL("openat2"),
        DepKind.SYSCALL("pidfd_getfd"),
        DepKind.SYSCALL("faccessat2"),
        DepKind.SYSCALL("process_madvise"),
        DepKind.SYSCALL("epoll_pwait2"),
        DepKind.SYSCALL("mount_setattr"),
        DepKind.SYSCALL("quotactl_fd"),
        DepKind.SYSCALL("landlock_create_ruleset"),
        DepKind.SYSCALL("landlock_add_rule"),
        DepKind.SYSCALL("landlock_restrict_self"),
        DepKind.SYSCALL("memfd_secret"),
        DepKind.SYSCALL("process_mrelease"),
        DepKind.SYSCALL("waitpid"),
        DepKind.SYSCALL("oldfstat"),
        DepKind.SYSCALL("break"),
        DepKind.SYSCALL("oldstat"),
        DepKind.SYSCALL("umount"),
        DepKind.SYSCALL("stime"),
        DepKind.SYSCALL("stty"),
        DepKind.SYSCALL("gtty"),
        DepKind.SYSCALL("nice"),
        DepKind.SYSCALL("ftime"),
        DepKind.SYSCALL("prof"),
        DepKind.SYSCALL("signal"),
        DepKind.SYSCALL("lock"),
        DepKind.SYSCALL("mpx"),
        DepKind.SYSCALL("ulimit"),
        DepKind.SYSCALL("oldolduname"),
        DepKind.SYSCALL("sigaction"),
        DepKind.SYSCALL("sgetmask"),
        DepKind.SYSCALL("ssetmask"),
        DepKind.SYSCALL("sigsuspend"),
        DepKind.SYSCALL("sigpending"),
        DepKind.SYSCALL("oldlstat"),
        DepKind.SYSCALL("readdir"),
        DepKind.SYSCALL("profil"),
        DepKind.SYSCALL("socketcall"),
        DepKind.SYSCALL("olduname"),
        DepKind.SYSCALL("idle"),
        DepKind.SYSCALL("vm86old"),
        DepKind.SYSCALL("ipc"),
        DepKind.SYSCALL("sigreturn"),
        DepKind.SYSCALL("sigprocmask"),
        DepKind.SYSCALL("bdflush"),
        DepKind.SYSCALL("afs_syscall"),
        DepKind.SYSCALL("llseek"),
        DepKind.SYSCALL("old_select"),
        DepKind.SYSCALL("vm86"),
        DepKind.SYSCALL("old_getrlimit"),
        DepKind.SYSCALL("mmap2"),
        DepKind.SYSCALL("truncate64"),
        DepKind.SYSCALL("ftruncate64"),
        DepKind.SYSCALL("stat64"),
        DepKind.SYSCALL("lstat64"),
        DepKind.SYSCALL("fstat64"),
        DepKind.SYSCALL("lchown16"),
        DepKind.SYSCALL("getuid16"),
        DepKind.SYSCALL("getgid16"),
        DepKind.SYSCALL("geteuid16"),
        DepKind.SYSCALL("getegid16"),
        DepKind.SYSCALL("setreuid16"),
        DepKind.SYSCALL("setregid16"),
        DepKind.SYSCALL("getgroups16"),
        DepKind.SYSCALL("setgroups16"),
        DepKind.SYSCALL("fchown16"),
        DepKind.SYSCALL("setresuid16"),
        DepKind.SYSCALL("getresuid16"),
        DepKind.SYSCALL("setresgid16"),
        DepKind.SYSCALL("getresgid16"),
        DepKind.SYSCALL("chown16"),
        DepKind.SYSCALL("setuid16"),
        DepKind.SYSCALL("setgid16"),
        DepKind.SYSCALL("setfsuid16"),
        DepKind.SYSCALL("setfsgid16"),
        DepKind.SYSCALL("fcntl64"),
        DepKind.SYSCALL("sendfile32"),
        DepKind.SYSCALL("statfs64"),
        DepKind.SYSCALL("fstatfs64"),
        DepKind.SYSCALL("fadvise64_64"),
        DepKind.SYSCALL("clock_gettime32"),
        DepKind.SYSCALL("clock_settime32"),
        DepKind.SYSCALL("clock_adjtime64"),
        DepKind.SYSCALL("clock_getres_time32"),
        DepKind.SYSCALL("clock_nanosleep_time32"),
        DepKind.SYSCALL("timer_gettime32"),
        DepKind.SYSCALL("timer_settime32"),
        DepKind.SYSCALL("timerfd_gettime32"),
        DepKind.SYSCALL("timerfd_settime32"),
        DepKind.SYSCALL("utimensat_time32"),
        DepKind.SYSCALL("pselect6_time32"),
        DepKind.SYSCALL("ppoll_time32"),
        DepKind.SYSCALL("io_pgetevents_time32"),
        DepKind.SYSCALL("recvmmsg_time32"),
        DepKind.SYSCALL("mq_timedsend_time32"),
        DepKind.SYSCALL("mq_timedreceive_time32"),
        DepKind.SYSCALL("rt_sigtimedwait_time32"),
        DepKind.SYSCALL("futex_time32"),
        DepKind.SYSCALL("sched_rr_get_interval_time32"),
    ],
}
