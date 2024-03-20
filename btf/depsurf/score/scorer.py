from collections import defaultdict
from enum import Enum

from ..diff import Consequence
from ..btf import Kind


class GenericChange(str, Enum):
    FUNC_ADD = "Function added"
    FUNC_UNAVAIL = "Function unavailable"
    STRUCT_ADD = "Struct added"
    STRUCT_UNAVAIL = "Struct unavailable"
    STATIC_FN = "Static function"
    PARTIAL_INLINE = "Partial inline"
    FULL_INLINE = "Full inline"

    @property
    def consequence(self):
        return {
            self.FUNC_ADD: Consequence.RUNTIME,
            self.FUNC_UNAVAIL: Consequence.RUNTIME,
            self.STRUCT_ADD: Consequence.COMPILER,
            self.STRUCT_UNAVAIL: Consequence.COMPILER,
            self.STATIC_FN: Consequence.RUNTIME,
            self.PARTIAL_INLINE: Consequence.SLIENT,
            self.FULL_INLINE: Consequence.RUNTIME,
        }[self]


class KernelImages:
    def __init__(self, paths):
        from ..btf import BTF

        self.btfs = [BTF(p) for p in paths]

    @property
    def all_versions(self):
        return [btf.short_version for btf in self.btfs]

    def __len__(self):
        return len(self.all_versions)

    def get_changes(self, kind, name):
        from ..diff import get_diff_fn

        result = []
        for btf1, btf2 in zip(self.btfs, self.btfs[1:]):
            t1 = btf1.get(kind, name)
            t2 = btf2.get(kind, name)
            if t1 is None and t2 is not None:
                c = {
                    Kind.FUNC: GenericChange.FUNC_ADD,
                    Kind.STRUCT: GenericChange.STRUCT_ADD,
                }[kind]
                result.append((btf1.short_version, btf2.short_version, [c]))
                continue
            if t1 is not None and t2 is None:
                c = {
                    Kind.FUNC: GenericChange.FUNC_UNAVAIL,
                    Kind.STRUCT: GenericChange.STRUCT_UNAVAIL,
                }[kind]
                result.append((btf1.short_version, btf2.short_version, [c]))
                continue
            if t1 is None and t2 is None:
                continue
            diff_fn = get_diff_fn(kind)
            reasons = diff_fn(t1, t2).reasons()
            if reasons:
                result.append((btf1.short_version, btf2.short_version, reasons))
        return result

    def get_versions(self, kind, name):
        result = []
        for btf in self.btfs:
            t = btf.get(kind, name)
            if t is not None:
                result.append(btf.short_version)
        return result


class Causes:
    def __init__(self):
        self.weights = defaultdict(float)
        self.counts = defaultdict(int)

    def add(self, cause, weight):
        self.weights[cause] += weight
        self.counts[cause] += 1

    def clear(self):
        self.weights.clear()
        self.counts.clear()

    def merge(self, other):
        for cause, weight in other.weights.items():
            self.weights[cause] += weight
            self.counts[cause] += other.counts[cause]

    def print(self, nindent=0):
        indent = "\t" * nindent
        score = 0
        for cause, weight in sorted(self.weights.items(), key=lambda x: -x[1]):
            count = self.counts[cause]
            consequence = cause.consequence
            print(
                f"{indent}{cause.value:20} {weight:6.2f}"
                f" ({count:4} times)"
                f" -> {consequence.value:10}"
                f" (x{consequence.weight})"
                f" = {weight * consequence.weight:.2f}"
            )
            score += weight * consequence.weight
        print(f"{indent}Score: {score:.2f}")
        return score


class Scorer:
    def __init__(self, imgs: KernelImages, subroutine_info):
        self.imgs = imgs
        self.subroutine_info = subroutine_info
        self.causes = Causes()

    def get_stable_score(self, hooks, structs):
        self.causes.clear()
        for hook_type, hook_name in hooks:
            self.analyze_single_dep(Kind.FUNC, hook_name, hook_type)
        for struct in structs:
            self.analyze_single_dep(Kind.STRUCT, struct, "struct")
        return self.causes

    def print_func_change(self, name):
        d = self.subroutine_info.get(name)
        if d is not None:
            assert len(d) == 1
            info = list(d.values())[0]
            if info.external:
                print(f"\t\tNon-static Function: ✅")
            else:
                print(f"\t\tStatic Function: 💥")
                self.causes.add(GenericChange.STATIC_FN, weight=1)
            if len(info.caller_inline) > 0:
                if len(info.caller_func) > 0:
                    print(f"\t\tPartial inline: 💥")
                    print(f"\t\t\tInline callers: {info.caller_inline}")
                    print(f"\t\t\tFunc callers: {info.caller_func}")
                    self.causes.add(GenericChange.PARTIAL_INLINE, weight=1)
                else:
                    print(f"\t\tFull inline: 💥")
                    print(f"\t\t\tInline callers: {info.caller_inline}")
                    self.causes.add(GenericChange.FULL_INLINE, weight=1)
            else:
                print(f"\t\tNo callers inlined: ✅")
                print(f"\t\t\tCallers: {info.caller_func}")
        else:
            print(f"\t\tNot found")

    def print_changes(self, kind, name):
        from ..diff import StructChange

        changes = self.imgs.get_changes(kind, name)
        result = []
        for v1, v2, reasons in changes:
            desc = []
            for c in reasons:
                if c == StructChange.LAYOUT:
                    continue

                self.causes.add(c, weight=1)
                desc.append(c.value)
            if desc:
                result.append(f"{v1:5} -> {v2:5}: {desc}")
        if not result:
            print(f"\t\tChanges: None")
        else:
            num_total = len(self.imgs.all_versions) - 1
            num_same = num_total - len(result)
            percent = num_same / num_total * 100
            print(f"\t\tUnchanged ({num_same}/{num_total} = {percent:.0f}%):")
            for r in result:
                print(f"\t\t\t💥 {r}")

    def analyze_single_dep(self, kind, name, t):
        print(f"\t{t}: {name}")
        if t not in ["kprobe", "tracepoint", "struct"]:
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

        versions = self.imgs.get_versions(kind, name)
        versions_str = ""

        unavailable_versions = []

        for v in self.imgs.all_versions:
            if v in versions:
                versions_str += "✅"
            else:
                unavailable_versions += [v]
                versions_str += "❌"

        len_avail = len(versions)
        if len_avail == 0 and (name.startswith("dummy") or name.startswith("foo")):
            return

        for v in unavailable_versions:
            c = {
                Kind.FUNC: GenericChange.FUNC_UNAVAIL,
                Kind.STRUCT: GenericChange.STRUCT_UNAVAIL,
            }[kind]
            self.causes.add(c, weight=1 / len(self.imgs))

        percent = len_avail / len(self.imgs) * 100
        print(
            f"\t\tAvailable versions: {versions_str} ({len_avail}/{len(self.imgs)} = {percent:.0f}%)"
        )

        if not versions:
            return

        if t == "kprobe":
            self.print_func_change(name)

        self.print_changes(kind, name)
