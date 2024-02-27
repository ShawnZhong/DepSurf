from enum import Enum


class Kind(str, Enum):
    INT = "INT"
    PTR = "PTR"
    ARRAY = "ARRAY"
    STRUCT = "STRUCT"
    UNION = "UNION"
    ENUM = "ENUM"
    FWD = "FWD"
    TYPEDEF = "TYPEDEF"
    VOLATILE = "VOLATILE"
    CONST = "CONST"
    RESTRICT = "RESTRICT"
    FUNC = "FUNC"
    FUNC_PROTO = "FUNC_PROTO"
    VAR = "VAR"
    DATASEC = "DATASEC"
    FLOAT = "FLOAT"
    DECL_TAG = "DECL_TAG"
    TYPE_TAG = "TYPE_TAG"
    ENUM64 = "ENUM64"
