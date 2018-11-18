from . import build
from . import gen


def build(source: str, output: str) -> int:
    return build.build(gen.Config(source, output))
