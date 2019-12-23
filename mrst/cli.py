import argparse
import sys
import typing as t

from . import build
from . import gen


def run(args: t.List[str]) -> int:
    parser = argparse.ArgumentParser("Generates Rst files")
    parser.add_argument(
        "--source", default=None, type=str, help="source directory"
    )
    parser.add_argument(
        "--output",
        default=None,
        type=str,
        help="destination directory for generated source",
    )
    parser.add_argument(
        "--generate",
        default=False,
        type=bool,
        help="If set, generate only, don't call Sphinx.",
    )
    p_args = parser.parse_args(args)

    cfg = gen.Config(p_args.source, p_args.output)
    if p_args.generate:
        return gen.generate(cfg)
    else:
        return build.build(cfg)


def main() -> None:
    exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
