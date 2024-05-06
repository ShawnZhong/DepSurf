from elftools.elf.elffile import ELFFile


class Sections:
    def __init__(self, elffile: ELFFile):
        self.elffile = elffile
        self.data = self.get_section_info(elffile)

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

    def __getitem__(self, name):
        return self.elffile.get_section_by_name(name)

    def _repr_html_(self):
        return self.data.to_html(formatters={"addr": hex, "offset": hex, "size": hex})
