from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.die import DIE


def disable_dwarf_cache():
    def _get_cached_DIE(self: CompileUnit, offset):
        top_die_stream = self.get_top_DIE().stream
        return DIE(cu=self, stream=top_die_stream, offset=offset)

    CompileUnit._get_cached_DIE = _get_cached_DIE
