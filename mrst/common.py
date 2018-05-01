import typing as t


def make_include_reg(prefix: str) -> str:
    return f'{prefix} "([^"]*)" ?(.*)$'


def parse_include_file_args(matches: t.Match[str]) -> dict:
    input_file, rest = matches.groups()
    args = rest.split(' ')
    kwargs: t.Dict[str, t.Any] = {
        'input_file': input_file,
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

    return kwargs
