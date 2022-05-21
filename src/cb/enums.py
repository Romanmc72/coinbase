#!/usr/bin/env python3
"""
Description
-----------
Default string enums represent as the Class.ATTR instead of the actual string,
this fixes that.
"""
from enum import Enum


class StringEnum(str, Enum):
    """An enum where every element is a string and always comes out as a string."""

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.__str__()
