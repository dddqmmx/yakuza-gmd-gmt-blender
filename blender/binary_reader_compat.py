from enum import Flag, IntEnum


def apply_binary_reader_enum_compat():
    from ..gmt_lib.gmt.util.binary_reader.binary_reader import BinaryReader

    def is_iterable(value) -> bool:
        return hasattr(value, "__iter__") and not isinstance(value, (str, bytes, IntEnum, Flag))

    BinaryReader.is_iterable = staticmethod(is_iterable)
