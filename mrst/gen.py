import datetime
import glob
import os
import re
import shutil
import subprocess
import tempfile
import typing as t

from . import common
from . import cpp


DUMPFILE_RE = re.compile(common.make_include_reg("~dumpfile"))


def _call_pandoc(mark_down_abs_path: str, rst_abs_path: str) -> None:
    cmd = (
        f"pandoc {mark_down_abs_path} --from markdown "
        f"--to rst -s -o {rst_abs_path} --wrap=none"
    )
    subprocess.check_call(cmd, shell=True)


def convert_md_to_rst(lines: t.List[str]) -> t.List[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = os.path.join(tmpdir, "input.md")
        rst_file = os.path.join(tmpdir, "output.rst")
        with open(md_file, "w") as w:
            for line in lines:
                w.write(line)

        _call_pandoc(md_file, rst_file)
        with open(rst_file) as r:
            return [l.rstrip() for l in r.readlines()]


def _read_file(
    input_file: str,
    start: t.Optional[int],
    end: t.Optional[int],
    start_after: t.Optional[str] = None,
    end_before: t.Optional[str] = None,
) -> t.List[str]:
    with open(input_file, "r") as r:
        lines = r.readlines()

    if start_after:
        if start is not None:
            raise ValueError(
                '"start_after" and "start" arguments are mutually exclusive'
            )
        else:
            for i, line in enumerate(lines):
                if line.startswith(start_after):
                    start = i + 1

    if end_before:
        if end is not None:
            raise ValueError(
                '"end_before" and "end" arguments are mutually exclusive'
            )
        else:
            for i, line in enumerate(lines):
                if line.startswith(end_before):
                    end = i

    if start and end:
        subset = lines[start:end]
    elif start:
        subset = lines[start:]
    elif end:
        subset = lines[:end]
    else:
        subset = lines

    return subset


class FileReader:
    def __init__(self, original: str) -> None:
        self._current_source = original

    def __call__(
        self,
        input_file: str,
        start: t.Optional[int],
        end: t.Optional[int],
        **_kwargs: t.Any,
    ) -> t.Tuple[t.List[str], t.Any]:
        full_input_file = os.path.join(
            os.path.dirname(self._current_source), input_file
        )
        lines = _read_file(full_input_file, start, end)
        return lines, FileReader(full_input_file)


def _dump_file(
    input_file: str,
    start: t.Optional[int],
    end: t.Optional[int],
    indent: t.Optional[int],
    section: t.Optional[str],
    start_after: t.Optional[str],
    end_before: t.Optional[str],
    write_stream: t.TextIO,
) -> None:
    print(f" ^---- dumpfile {input_file} {start} {end} {indent} {section}")
    lines = _read_file(
        input_file, start, end, start_after=start_after, end_before=end_before
    )

    if indent:
        prefix = " " * indent
    else:
        prefix = ""

    if input_file.endswith(".md"):
        final_lines = convert_md_to_rst(lines)
    elif input_file.endswith(".hpp") or input_file.endswith(".cpp"):
        final_lines = cpp.translate_cpp_file(
            lines, section, FileReader(input_file)
        )
    else:
        final_lines = [prefix + l.rstrip() for l in lines]

    write_stream.write("\n".join(final_lines))


def _dumpfile_directive(
    current_source: str, matches: str, write_stream: t.TextIO
) -> None:
    kwargs = common.parse_include_file_args(matches)

    full_input_file = os.path.join(
        os.path.dirname(current_source), kwargs["input_file"]
    )

    kwargs["input_file"] = full_input_file
    _dump_file(write_stream=write_stream, **kwargs)


def parse_m_rst(source: str, dst: str) -> None:
    with open(dst, "w") as w:
        with open(source, "r") as f:
            for line in f.readlines():
                if line.startswith("~dumpfile "):
                    _dumpfile_directive(source, line[10:], w)
                else:
                    if "~~current-time~~" in line:
                        line = line.replace(
                            "~~current-time~~", str(datetime.datetime.now())
                        )
                    if "~~git-commit~~" in line:
                        sha = subprocess.check_output(
                            "git rev-parse HEAD",
                            shell=True,
                            cwd=os.path.dirname(source),
                        )
                        line = line.replace(
                            "~~git-commit~~", sha.decode("utf-8")
                        )
                    w.write(f"{line}")


def copy_rst_files(source: str, dst: str) -> None:
    rel = os.path.relpath(dst, source)
    print(rel)
    for file in glob.iglob(f"{source}/**/*", recursive=True):
        if os.path.isfile(file):
            print(file)
            rel_path = file[len(source) :]
            print(rel_path)
            if rel_path.startswith(os.sep):
                rel_path = rel_path[1:]
            print(rel_path)
            to_path = os.path.join(dst, rel_path)
            if file.endswith(".rst"):
                print(f"{file} -> {to_path}")
                shutil.copy(file, to_path)
            elif file.endswith(".mrst"):
                print(f"parse {file} -> {to_path}")
                parse_m_rst(file, to_path)


class Config:
    def __init__(self, source: str, output: str) -> None:
        self.source_dir = source
        self.output_dir = output
        self.gen_source_dir = os.path.join(output, "gen")
        self.build_dir = os.path.join(output, "build")


def generate(config: Config) -> int:
    try:
        shutil.rmtree(config.gen_source_dir)
    except FileNotFoundError:
        pass

    os.makedirs(config.gen_source_dir, exist_ok=True)
    os.makedirs(config.build_dir, exist_ok=True)

    shutil.copy(
        os.path.join(config.source_dir, "conf.py"),
        os.path.join(config.gen_source_dir, "conf.py"),
    )

    copy_rst_files(config.source_dir, config.gen_source_dir)
    return 0
