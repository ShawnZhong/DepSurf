from depsurf.issues import IssueEnum


class BaseChange:
    def __init_subclass__(cls, enum: IssueEnum):
        cls.enum = enum

    def format(self):
        raise NotImplementedError

    def __str__(self):
        return f"{self.enum:24}{self.format()}"
