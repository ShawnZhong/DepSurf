from .change import ConfigChange


def diff_config(old, new):
    if old != new:
        return [ConfigChange(old, new)]
    return []
