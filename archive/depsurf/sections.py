from pathlib import Path
from elftools.elf.elffile import ELFFile


class Sections:
    def __init__(self, path: Path):
        with open(path, "rb") as fin:
            self.data = self.get_section_info(ELFFile(fin))

    @staticmethod
    def get_section_info(elffile: ELFFile):
        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "name": s.name,
                    **{
                        k.removeprefix("sh_"): v
                        for k, v in s.header.items()
                        if k not in ("sh_name", "sh_addr")
                    },
                    "addr": s.header.sh_addr,
                    # "data": s.data()[:15],
                }
                for s in elffile.iter_sections()
            ]
        ).set_index("name")
        return df

    def _repr_html_(self):
        return self.data.to_html(formatters={"addr": hex, "offset": hex, "size": hex})
