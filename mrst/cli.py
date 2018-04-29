import argparse
import sys

from . import build
from . import gen


def main() -> None:
    parser = argparse.ArgumentParser('Generates Rst files')
    parser.add_argument('--source', default=None, type=str,
                        help='source directory')
    parser.add_argument('--output', default=None, type=str,
                        help='destination directory for generated source')
    parser.add_argument('--generate', default=False, type=bool,
                        help='If set, generate only, don\'t call Sphinx.')
    args = parser.parse_args()

    cfg = gen.Config(args.source, args.output)
    if args.generate:
        sys.exit(gen.generate(cfg))
    else:
        sys.exit(build.build(cfg))


if __name__ == "__main__":
    main()
