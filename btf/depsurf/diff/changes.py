from depsurf.btf import get_btf_type_str


class DiffChanges:
    def __init__(self):
        self.changes = []

    def add(self, reason, detail):
        assert isinstance(reason, str)
        assert isinstance(detail, list)
        for t in detail:
            assert isinstance(t, tuple)
        self.changes.append((reason, detail))

    def repr(self, nindent=0):
        indent = "\t" * nindent
        result = ""
        for reason, detail in self.changes:
            result += f"{indent}{reason.value:20} ==> {reason.consequence.value}\n"
            for t in detail:
                if len(t) == 2 and isinstance(t[0], str):
                    k, v = t
                    result += f"{indent}\t{k:24}: {get_btf_type_str(v)}"
                elif len(t) == 2 and isinstance(t[0], list) and isinstance(t[1], list):
                    l1, l2 = t
                    result += f"{indent}\t  {l1}\n"
                    result += f"{indent}\t->{l2}"
                elif len(t) == 2:
                    v1, v2 = t
                    result += (
                        f"{indent}\t{get_btf_type_str(v1)}  ->  {get_btf_type_str(v2)}"
                    )
                elif len(t) == 3:
                    k, v1, v2 = t
                    result += f"{indent}\t{k:24}: {get_btf_type_str(v1)}  ->  {get_btf_type_str(v2)}"
                result += "\n"
        return result

    def print(self, nindent=0):
        print(self.repr(nindent), end="")

    def __repr__(self):
        return self.repr()

    def __iter__(self):
        return iter(self.changes)

    def __bool__(self):
        return bool(self.changes)
