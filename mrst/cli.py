import argparse
import sys
import typing as t

from . import build
from . import gen


def run(args: t.List[str]) -> int:
    parser = argparse.ArgumentParser("Generates Rst files")
    parser.add_argument(
        "--source", required=True, type=str, help="source directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="destination directory for generated source",
    )
    parser.add_argument(
        "--skip-sphinx",
        action="store_true",
        default=False,
        help="If set, generate only, don't call Sphinx.",
    )
    p_args = parser.parse_args(args)

    cfg = gen.Config(p_args.source, p_args.output)
    if p_args.skip_sphinx:
        return gen.generate(cfg)
    else:
        return build.build(cfg)


def main() -> None:
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
