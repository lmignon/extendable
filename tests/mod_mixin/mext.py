from .m import M


class MExt(M, extends=True):
    def ext(self) -> bool:
        return True
