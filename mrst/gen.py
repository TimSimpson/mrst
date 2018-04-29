import glob
import os
import re
import shutil
import subprocess
import tempfile
import typing as t

from . import cpp


DUMPFILE_RE = re.compile('~dumpfile "([^"]*)" ?(.*)$')


def _call_pandoc(mark_down_abs_path: str, rst_abs_path: str) -> None:
    cmd = (f'pandoc {mark_down_abs_path} --from markdown '
           f'--to rst -s -o {rst_abs_path} --wrap=none')
    subprocess.check_call(cmd, shell=True)


def convert_md_to_rst(lines: t.List[str]) -> t.List[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        md_file = os.path.join(tmpdir, 'input.md')
        rst_file = os.path.join(tmpdir, 'output.rst')
        with open(md_file, 'w') as w:
            for line in lines:
                w.write(line)

        _call_pandoc(md_file, rst_file)
        with open(rst_file) as r:
            return [l.rstrip() for l in r.readlines()]


def _dump_file(input_file: str,
               start: t.Optional[int],
               end: t.Optional[int],
               indent: t.Optional[int],
               section: t.Optional[str],
               write_stream: t.TextIO) -> None:
    print(f' ^---- dumpfile {input_file} {start} {end} {indent} {section}')
    with open(input_file, 'r') as r:
        lines = r.readlines()

    if start and end:
        subset = lines[start: end]
    elif start:
        subset = lines[start:]
    else:
        subset = lines

    if indent:
        prefix = ' ' * indent
    else:
        prefix = ''

    if input_file.endswith('.md'):
        final_lines = convert_md_to_rst(subset)
    elif input_file.endswith('.hpp') or input_file.endswith('.cpp'):
        final_lines = cpp.translate_cpp_file(subset, section)
    else:
        final_lines = [prefix + l.rstrip() for l in subset]

    write_stream.write('\n'.join(final_lines))


def _dumpfile_directive(current_source: str,
                        matches: t.Match[str],
                        write_stream: t.TextIO) -> None:
    input_file, rest = matches.groups()
    args = rest.split(' ')
    kwargs: t.Dict[str, t.Any] = {
        'start': None,
        'end': None,
        'indent': None,
        'section': None,
    }
    pos_arg_indices = ['start', 'end', 'indent']
    pos_arg_index = 0
    for arg in args:
        if '=' in arg:
            name, value = arg.split('=', 1)
        else:
            name = pos_arg_indices[pos_arg_index]
            pos_arg_index += 1
            value = arg

        if name not in kwargs:
            raise RuntimeError(
                f'Unknown dumpfile arg: {name}')
        if kwargs[name] is not None:
            raise RuntimeError(
                f'dumpfile arg {name} set twice')

        kwargs[name] = value

    if kwargs['end'] == '~':
        kwargs['end'] = None

    def intify(arg_name: str) -> None:
        if kwargs[arg_name]:
            kwargs[arg_name] = int(kwargs[arg_name])
        else:
            kwargs[arg_name] = 0

    intify('start')
    intify('end')
    intify('indent')

    full_input_file = os.path.join(
        os.path.dirname(current_source), input_file)
    print(kwargs)
    _dump_file(full_input_file, write_stream=write_stream, **kwargs)


def parse_m_rst(source: str, dst: str) -> None:
    with open(dst, 'w') as w:
        with open(source, 'r') as f:
            for line in f.readlines():
                matches = DUMPFILE_RE.match(line)
                if matches:
                    _dumpfile_directive(source, matches, w)
                else:
                    w.write(f'{line}')


def copy_rst_files(source: str, dst: str) -> None:
    rel = os.path.relpath(dst, source)
    print(rel)
    for file in glob.iglob(f'{source}/**/*', recursive=True):
        if os.path.isfile(file):
            print(file)
            rel_path = file[len(source):]
            print(rel_path)
            if rel_path.startswith(os.sep):
                rel_path = rel_path[1:]
            print(rel_path)
            to_path = os.path.join(dst, rel_path)
            if file.endswith('.rst'):
                print(f'{file} -> {to_path}')
                shutil.copy(file, to_path)
            elif file.endswith('.mrst'):
                print(f'parse {file} -> {to_path}')
                parse_m_rst(file, to_path)


class Config:

    def __init__(self, source: str, output: str) -> None:
        self.source_dir = source
        self.output_dir = output
        self.gen_source_dir = os.path.join(output, 'gen')
        self.build_dir = os.path.join(output, 'build')


def generate(config: Config) -> int:
    try:
        shutil.rmtree(config.gen_source_dir)
    except FileNotFoundError:
        pass

    os.makedirs(config.gen_source_dir, exist_ok=True)
    os.makedirs(config.build_dir, exist_ok=True)

    shutil.copy(os.path.join(config.source_dir, 'conf.py'),
                os.path.join(config.gen_source_dir, 'conf.py'),)

    copy_rst_files(config.source_dir, config.gen_source_dir)
    return 0
