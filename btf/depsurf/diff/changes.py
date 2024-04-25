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

    @property
    def reasons(self):
        return [reason for reason, _ in self.changes]

    def __add__(self, other: "DiffChanges"):
        result = DiffChanges()
        result.changes = self.changes + other.changes
        return result

    def str(self, nindent=0):
        indent = "\t" * nindent
        result = ""
        for reason, detail in self.changes:
            result += f"{indent}{reason.value:20} ==> {reason.consequence.value}\n"
            for t in detail:
                if len(t) == 2 and isinstance(t[0], str):
                    k, v = t
                    if isinstance(v, dict):
                        result += f"{indent}\t{k:24}: {get_btf_type_str(v)}"
                    elif isinstance(v, int):
                        result += f"{indent}\t{k:24}: {v}"
                    else:
                        raise ValueError(f"Unknown type: {v}")
                elif len(t) == 2 and isinstance(t[0], list) and isinstance(t[1], list):
                    l1, l2 = t
                    result += f"{indent}\t  {l1}\n"
                    result += f"{indent}\t->{l2}"
                elif len(t) == 2:
                    v1, v2 = t
                    if isinstance(v1, dict) and isinstance(v2, dict):
                        result += f"{indent}\t{get_btf_type_str(v1)}  ->  {get_btf_type_str(v2)}"
                    elif isinstance(v1, int) and isinstance(v2, int):
                        result += f"{indent}\t{v1}  ->  {v2}"
                    else:
                        raise ValueError(f"Unknown type: {v1} or {v2}")
                elif len(t) == 3:
                    k, v1, v2 = t
                    if isinstance(v1, dict) and isinstance(v2, dict):
                        result += f"{indent}\t{k:24}: {get_btf_type_str(v1)}  ->  {get_btf_type_str(v2)}"
                    elif isinstance(v1, int) and isinstance(v2, int):
                        result += f"{indent}\t{k:24}: {v1}  ->  {v2}"
                    else:
                        raise ValueError(f"Unknown type: {v1} or {v2}")

                result += "\n"
        return result

    def print(self, nindent=0):
        print(self.str(nindent), end="")

    def __str__(self):
        return self.str()

    def __repr__(self):
        return str(list(map(str, self.changes)))

    def __iter__(self):
        return iter(self.changes)

    def __bool__(self):
        return bool(self.changes)
