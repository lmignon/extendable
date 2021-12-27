from extendable import ExtendableMeta


class Base(metaclass=ExtendableMeta):
    def test(self) -> str:
        return "base"
