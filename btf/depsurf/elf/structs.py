from elftools.construct import Struct, ULInt8, ULInt16, ULInt32

btf_header_t = Struct(
    "btf_header",
    ULInt16("magic"),
    ULInt8("version"),
    ULInt8("flags"),
    ULInt32("hdr_len"),
    # type
    ULInt32("type_off"),
    ULInt32("type_len"),
    # string
    ULInt32("str_off"),
    ULInt32("str_len"),
)

btf_ext_header_t = Struct(
    "btf_ext_header",
    ULInt16("magic"),
    ULInt8("version"),
    ULInt8("flags"),
    ULInt32("hdr_len"),
    # func
    ULInt32("func_info_off"),
    ULInt32("func_info_len"),
    # line
    ULInt32("line_info_off"),
    ULInt32("line_info_len"),
    # core
    ULInt32("core_relo_off"),
    ULInt32("core_relo_len"),
)

rec_size_t = ULInt32("rec_size")

btf_ext_info_sec_t = Struct(
    "btf_ext_info_sec",
    ULInt32("sec_name_off"),
    ULInt32("num_info"),
)

bpf_core_relo_t = Struct(
    "bpf_core_relo",
    ULInt32("insn_off"),
    ULInt32("type_id"),
    ULInt32("access_str_off"),
    ULInt32("kind"),
)
