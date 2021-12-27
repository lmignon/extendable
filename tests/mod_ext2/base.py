from ..mod_base.base import Base


class ExtBase(Base, extends=Base):
    def test(self) -> str:
        res = super().test()
        return "mod2." + res
