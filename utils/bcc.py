from enum import StrEnum


class Category(StrEnum):
    CPU = "CPU"
    PROC = "Process"
    MEMORY = "Memory"
    BLOCK = "Block Device"
    FILESYSTEM = "Filesystem"
    NETWORK = "Network"
    USERSPACE = "Userspace"
    OTHER = "Other"


BCC_CATEGORY = {
    "argdist": Category.OTHER,
    "bashreadline": Category.USERSPACE,
    "bindsnoop": Category.NETWORK,
    "biolatency": Category.BLOCK,
    "biolatpcts": Category.BLOCK,
    "biopattern": Category.BLOCK,
    "biosnoop": Category.BLOCK,
    "biotop": Category.BLOCK,
    "bitesize": Category.BLOCK,
    "btrfsdist": Category.FILESYSTEM,
    "btrfsslower": Category.FILESYSTEM,
    "cachestat": Category.FILESYSTEM,
    "cachetop": Category.FILESYSTEM,
    "capable": Category.OTHER,
    "compactsnoop": Category.MEMORY,
    "cpudist": Category.CPU,
    "cpuunclaimed": Category.CPU,
    "criticalstat": Category.CPU,
    "dbslower": Category.USERSPACE,
    "dbstat": Category.USERSPACE,
    "dcsnoop": Category.FILESYSTEM,
    "dcstat": Category.FILESYSTEM,
    "deadlock": Category.OTHER,
    "dirtop": Category.FILESYSTEM,
    "drsnoop": Category.MEMORY,
    "execsnoop": Category.PROC,
    "exitsnoop": Category.PROC,
    "ext4dist": Category.FILESYSTEM,
    "ext4slower": Category.FILESYSTEM,
    "filegone": Category.FILESYSTEM,
    "filelife": Category.FILESYSTEM,
    "fileslower": Category.FILESYSTEM,
    "filetop": Category.FILESYSTEM,
    "funccount": Category.OTHER,
    "funcinterval": Category.OTHER,
    "funclatency": Category.OTHER,
    "funcslower": Category.OTHER,
    "gethostlatency": Category.USERSPACE,
    "hardirqs": Category.CPU,
    "inject": Category.OTHER,
    "killsnoop": Category.PROC,
    "klockstat": Category.OTHER,
    "kvmexit": Category.PROC,
    "llcstat": Category.CPU,
    "mdflush": Category.BLOCK,
    "memleak": Category.MEMORY,
    "mountsnoop": Category.FILESYSTEM,
    "mysqld_qslower": Category.USERSPACE,
    "netqtop": Category.NETWORK,
    "nfsdist": Category.FILESYSTEM,
    "nfsslower": Category.FILESYSTEM,
    "offcputime": Category.CPU,
    "offwaketime": Category.CPU,
    "oomkill": Category.MEMORY,
    "opensnoop": Category.FILESYSTEM,
    "pidpersec": Category.PROC,
    "ppchcalls": Category.OTHER,
    "profile": Category.CPU,
    "readahead": Category.FILESYSTEM,
    "runqlat": Category.CPU,
    "runqlen": Category.CPU,
    "runqslower": Category.CPU,
    "shmsnoop": Category.PROC,
    "slabratetop": Category.MEMORY,
    "sofdsnoop": Category.NETWORK,
    "softirqs": Category.CPU,
    "solisten": Category.NETWORK,
    "sslsniff": Category.NETWORK,
    "stackcount": Category.OTHER,
    "statsnoop": Category.FILESYSTEM,
    "swapin": Category.MEMORY,
    "syncsnoop": Category.FILESYSTEM,
    "syscount": Category.OTHER,
    "tcpaccept": Category.NETWORK,
    "tcpcong": Category.NETWORK,
    "tcpconnect": Category.NETWORK,
    "tcpconnlat": Category.NETWORK,
    "tcpdrop": Category.NETWORK,
    "tcplife": Category.NETWORK,
    "tcpretrans": Category.NETWORK,
    "tcprtt": Category.NETWORK,
    "tcpstates": Category.NETWORK,
    "tcpsubnet": Category.NETWORK,
    "tcpsynbl": Category.NETWORK,
    "tcptop": Category.NETWORK,
    "tcptracer": Category.NETWORK,
    "threadsnoop": Category.PROC,
    "trace": Category.OTHER,
    "ttysnoop": Category.OTHER,
    "vfscount": Category.FILESYSTEM,
    "vfsstat": Category.FILESYSTEM,
    "virtiostat": Category.FILESYSTEM,
    "wakeuptime": Category.CPU,
    "xfsdist": Category.FILESYSTEM,
    "xfsslower": Category.FILESYSTEM,
    "zfsdist": Category.FILESYSTEM,
    "zfsslower": Category.FILESYSTEM,
    # libbpf-tools
    "biostacks": Category.BLOCK,
    "cpufreq": Category.CPU,
    "fsdist": Category.FILESYSTEM,
    "fsslower": Category.FILESYSTEM,
    "futexctn": Category.PROC,
    "javagc": Category.USERSPACE,
    "ksnoop": Category.OTHER,
    "numamove": Category.MEMORY,
    "sigsnoop": Category.PROC,
    "tcppktlat": Category.NETWORK,
}
