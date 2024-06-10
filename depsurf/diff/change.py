from depsurf.issues import IssueEnum


class BaseChange:
    def __init_subclass__(cls, enum: IssueEnum):
        cls.enum = enum

    def format(self):
        return str(self.enum)

    def __str__(self):
        return f"{self.enum:24}{self.format()}"
