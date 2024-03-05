class Averager:
    def __init__(self):
        self.sum = 0
        self.count = 0

    def __iadd__(self, other):
        if isinstance(other, Averager):
            self.sum += other.sum
            self.count += other.count
        elif isinstance(other, (int, float)):
            self.sum += other
            self.count += 1
        else:
            raise TypeError(f"unsupported type: {type(other)}")
        return self

    def get(self):
        import math

        if self.count == 0:
            return math.nan
        return self.sum / self.count
