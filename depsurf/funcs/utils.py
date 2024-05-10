from elftools.dwarf.die import DIE
from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.dwarfinfo import DWARFInfo


def get_name(die: DIE):
    name = die.attributes.get("DW_AT_name")
    if name is None:
        return None
    return name.value.decode("ascii")


def disable_dwarf_cache():
    def _get_cached_DIE(self: CompileUnit, offset):
        top_die_stream = self.get_top_DIE().stream
        return DIE(cu=self, stream=top_die_stream, offset=offset)

    CompileUnit._get_cached_DIE = _get_cached_DIE
    DWARFInfo._cached_CU_at_offset = DWARFInfo._parse_CU_at_offset
