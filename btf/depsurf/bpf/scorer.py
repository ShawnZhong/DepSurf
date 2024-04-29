import logging

from collections import defaultdict

from depsurf.diff import GenericCauses


from depsurf.btf import Kind


class Causes:
    def __init__(self):
        self.nums = defaultdict(int)
        self.counts = defaultdict(int)

    def add(self, cause, num=1):
        self.nums[cause] += num
        self.counts[cause] += 1

    def clear(self):
        self.nums.clear()
        self.counts.clear()

    def merge(self, other):
        for cause, weight in other.nums.items():
            self.nums[cause] += weight
            self.counts[cause] += other.counts[cause]

    def print(self, nindent=0):
        if not self.nums:
            return
        indent = "\t" * nindent
        print(f"{indent}Summary")
        for cause, count in sorted(self.counts.items(), key=lambda x: -x[1]):
            num = self.nums[cause]
            consequence = cause.consequence
            print(
                f"{indent}\t{cause.value:20} {num:4} times"
                # f" ({num:4} occurrences)"
                f" ==> {consequence.value:10}"
            )


class Scorer:
    def __init__(self):
        self.imgs = None
        # self.subroutine_info = subroutine_info
        self.causes = Causes()

    def analyze(self, hooks, structs, nindent=1):
        self.causes.clear()
        for hook_type, hook_name in hooks:
            self.analyze_single(Kind.FUNC, hook_name, hook_type, nindent=nindent)
        for struct in structs:
            self.analyze_single(Kind.STRUCT, struct, "struct", nindent=nindent)
        return self.causes

    def analyze_single(self, kind, name, t, nindent):
        indent = "\t" * nindent
        print(f"{indent}{t}: {name}")
        if t not in ["kprobe", "tracepoint", "struct"]:
            print(f"\t\tUnsupported hook type: {t}")
            return

        if t == "tracepoint":
            for prefix in ["sys_enter_", "sys_exit_"]:
                if name.startswith(prefix):
                    # TODO: this is a hack, we should have a better way to handle this
                    name = f"__x64_sys_{name[len(prefix):]}"
                    break
            else:
                # TODO this is a hack, we should have a better way to handle this
                # name = f"perf_trace_{name}"
                name = f"__traceiter_{name}"

        versions = self.analyze_availability(kind, name, nindent=nindent + 1)
        if not versions:
            return

        # if t == "kprobe":
        #     self.analyze_func(name, nindent=nindent + 1)

        self.analyze_changes(kind, name, nindent=nindent + 1)

    def analyze_availability(self, kind, name, nindent):
        indent = "\t" * nindent
        versions = self.imgs.get_versions(kind, name)

        if len(versions) == 0:
            if name.startswith("dummy") or name == "foo":
                print(f"\t\tFunction {name} is a dummy function")
                return
            logging.warning(f"Function {name} not found in any version")

        versions_str = ""

        for v in self.imgs.all_versions:
            if v in versions:
                versions_str += "✅"
            else:
                c = {
                    Kind.FUNC: GenericCauses.FUNC_UNAVAIL,
                    Kind.STRUCT: GenericCauses.STRUCT_UNAVAIL,
                }[kind]
                self.causes.add(c)
                versions_str += "❌"

        percent = len(versions) / len(self.imgs) * 100
        print(
            f"{indent}Availability: {versions_str} "
            f"({len(versions)}/{len(self.imgs)} = {percent:.0f}%)\n"
            f"{indent}\tVersions: {', '.join(versions)}"
        )
        return versions

    def analyze_func(self, name, nindent):
        indent = "\t" * nindent
        d = self.subroutine_info.get(name)
        if d is None:
            print(f"{indent}Funcion symbol: {name} not found in DWARF")
            return

        assert len(d) == 1
        info = list(d.values())[0]
        if info.external:
            print(f"{indent}Linkage: Non-static ✅")
        else:
            print(f"{indent}Linkage: Static 💥")
            self.causes.add(GenericCauses.STATIC_FN)

        def make_str(l):
            # return "\n\t\t\t\t" + "\n\t\t\t\t".join(l)
            return f"{len(l)} ({', '.join(l)})"

        caller_inline = make_str(info.caller_inline)
        caller_func = make_str(info.caller_func)
        if len(info.caller_inline) > 0:
            if len(info.caller_func) > 0:
                print(f"{indent}Inline: Partial 💥")
                print(f"{indent}\tInline callers: {caller_inline}")
                print(f"{indent}\tFunc callers: {caller_func}")
                self.causes.add(GenericCauses.PARTIAL_INLINE)
            else:
                print(f"{indent}Inline: Full 💥")
                print(f"{indent}\tInline callers: {caller_inline}")
                self.causes.add(GenericCauses.FULL_INLINE)
        else:
            print(f"{indent}Inline: None ✅")
            if info.caller_func:
                print(f"{indent}\tFunc callers: {caller_func}")

    def analyze_changes(self, kind, name, nindent):
        indent = "\t" * nindent
        changes_list = self.imgs.get_changes(kind, name)
        if not changes_list:
            print(f"{indent}Changes: None ✅")
            return

        print(f"{indent}Changes: {len(changes_list)} versions 💥")

        for v1, v2, changes in changes_list:
            print(f"{indent}\t{v1} -> {v2} 💥")
            changes.print(nindent=nindent + 2)
            for reason, detail in changes:
                self.causes.add(reason, len(detail))
