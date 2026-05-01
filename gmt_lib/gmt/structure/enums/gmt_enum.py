from enum import Enum, IntFlag


class GMTVersion(IntFlag):
    KENZAN = 0x10001
    YAKUZA3 = 0x20000
    YAKUZA5 = 0x20001
    ISHIN = 0x20002


class GMTVectorVersion(Enum):
    NO_VECTOR = 0
    OLD_VECTOR = 1
    DRAGON_VECTOR = 2

    @classmethod
    def from_GMTVersion(cls, version: GMTVersion):
        if version == GMTVersion.ISHIN:
            # This can be OLD_VECTOR as well, but that can't be determined with the version alone
            return GMTVectorVersion.DRAGON_VECTOR

        return GMTVectorVersion.NO_VECTOR


# Using IntFlag to support undocumented formats (patterns etc)
class GMTCurveType(IntFlag):
    ROTATION = 0
    LOCATION = 1
    PATTERN_HAND = 4
    PATTERN_UNK = 5
    PATTERN_FACE = 6


class GMTCurveChannel(IntFlag):
    """X, Y, Z, and ALL are for LOCATION

    XW, YW, ZW, and ALL are for ROTATION

    LEFT_HAND, RIGHT_HAND and UNK_HAND are for PATTERN_HAND

    PATTERN_FACE has unknown values ranging from 0 to more than 5
    """

    ALL = LEFT_HAND = 0
    X = XW = RIGHT_HAND = 1
    Y = YW = UNK_HAND = 2
    ZW = 3
    Z = 4


class GMTCurveFormat(IntFlag):
    ROT_QUAT_XYZ_FLOAT = 1

    # Half float before version 0x20000, scaled shorts everywhere else
    ROT_XYZW_SHORT = 2

    LOC_CHANNEL = 4
    LOC_XYZ = 6

    ROT_XW_FLOAT = 0x10
    ROT_YW_FLOAT = 0x11
    ROT_ZW_FLOAT = 0x12

    # Half float before version 0x20000, scaled shorts everywhere else
    ROT_XW_SHORT = 0x13
    ROT_YW_SHORT = 0x14
    ROT_ZW_SHORT = 0x15

    PATTERN_HAND = 0x1C
    PATTERN_UNK = 0x1D

    ROT_QUAT_XYZ_INT = 0x1E
