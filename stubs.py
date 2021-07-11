# coding: utf-8
import sys

if sys.version_info >= (3, 8):
    from typing import Final, Literal
else:
    from typing import Any

    class _Final:
        @staticmethod
        def __getitem__(item: type) -> type:
            return item

    class _Literal:
        @staticmethod
        def __getitem__(*items: Any) -> object:
            return type(items[0]) if items else Any


    Final = _Final()
    Literal = _Literal()

if sys.version_info >= (3, 10):
    from typing import NoneType
else:
    NoneType = type(None)

__all__ = ['Final', 'Literal', 'NoneType']
