from elftools.dwarf.die import DIE
import logging


def get_die_location_impl(die: DIE, file_entry, include_directory):
    assert "DW_AT_decl_file" in die.attributes, die
    decl_file = die.attributes["DW_AT_decl_file"].value

    entry = file_entry[decl_file - 1]
    directory = include_directory[entry.dir_index - 1]
    name = entry.name.decode("ascii")

    if type(directory) == bytes:
        directory = directory.decode("ascii")

    # return directory / name

    return f"{directory}/{name}"

    # line = die.attributes["DW_AT_decl_line"].value
    # column = die.attributes["DW_AT_decl_column"].value

    # return f"{directory}/{name}:{line}:{column}"


def get_die_location(die: DIE):
    line_prog = die.dwarfinfo.line_program_for_CU(die.cu)
    file_entry = line_prog.header.file_entry
    include_directory = line_prog.header.include_directory

    return get_die_location_impl(die, file_entry, include_directory)


def get_name(die: DIE):
    if "DW_AT_name" in die.attributes:
        return die.attributes["DW_AT_name"].value.decode("ascii")
    elif "DW_AT_abstract_origin" in die.attributes:
        func_die = die.get_DIE_from_attribute("DW_AT_abstract_origin")
        return get_name(func_die)
    else:
        logging.warning(f"Cannot find name for DIE \n{get_die_backtrace(die)}")
        return None


def get_die_backtrace(die: DIE) -> str:
    if die is None:
        return ""

    name = get_name(die) if "DW_AT_name" in die.attributes else "<?>"
    location = get_die_location(die) if "DW_AT_decl_file" in die.attributes else "<?>"

    return f"{name} @ {location}\n{die}\n{get_die_backtrace(die.get_parent())}"


INLINE_STR = {
    0: "Not declared inline nor inlined by the compiler",
    1: "Not declared inline but inlined by the compiler",
    2: "Declared inline but not inlined by the compiler",
    3: "Declared inline and inlined by the compiler",
}


def get_name_with_inline(die: DIE):
    name = get_name(die)
    inline = die.attributes.get("DW_AT_inline")
    if inline is not None and inline.value != 0:
        return f"{name} ({INLINE_STR[inline.value]})"
    else:
        return name
