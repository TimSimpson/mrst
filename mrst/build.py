import subprocess

from . import gen


def sphinx_build(config: gen.Config, op: str = "html") -> int:
    cmd = f"sphinx-build -M {op} {config.gen_source_dir} {config.build_dir}"
    return subprocess.call(cmd, shell=True)


def build(config: gen.Config) -> int:
    return gen.generate(config) or sphinx_build(config)
