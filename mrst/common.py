import typing as t


def make_include_reg(prefix: str) -> str:
    return f'{prefix} '  # "([^"]*)" ?(.*)$'


def _split_args(args: str) -> t.List[str]:
    index = 0
    result = []
    while index < len(args):
        while len(args) > index and args[index] == ' ':
            index += 1

        if len(args) <= index:
            break

        if args[index] == '=':
            result.append('=')
            index += 1
        elif args[index] == '"':
            index += 1
            start_index = index
            while len(args) > index and args[index] != '"':
                if args[index] == '\\':
                    if len(args) > index + 1 and args[index + 1] == '"':
                        index += 2
                else:
                    index += 1
            result.append(args[start_index: index].replace('\\"', '"'))
            index += 1
        else:
            start_index = index
            while len(args) > index and args[index] not in [' ', '=']:
                index += 1
            result.append(args[start_index: index])

    return result


def parse_include_file_args(input: str) -> dict:
    # rest = matches.groups()
    args = _split_args(input.strip())
    if len(args) < 1:
        raise ValueError('Expected at least one arg.')
    print(f'args={args}')
    kwargs: t.Dict[str, t.Any] = {
        'input_file': args[0],
        'start': None,
        'end': None,
        'indent': None,
        'section': None,
        'start_after': None,
        'end_before': None,
    }
    pos_arg_indices = ['start', 'end', 'indent']
    pos_arg_index = 0
    index = 1
    while len(args) > index:
        if len(args) > (index + 1) and args[index + 1] == '=':
            if len(args) > (index + 2):
                name = args[index]
                value = args[index + 2]
                if name not in kwargs:
                    raise RuntimeError(f'Unknown dumpfile arg: \"{name}\"')
                elif kwargs[name] is not None:
                    raise RuntimeError(
                        f'dumpfile arg {name} set twice')
                kwargs[name] = value
                index += 3
                pos_arg_index = -1
            else:
                raise RuntimeError(
                    'Syntax error: "=" is expected to be followed by an '
                    'argument (this is a name / value pair sitch).'
                    f'Line: {input}'
                )
        else:
            if pos_arg_index < 0:
                raise RuntimeError(
                    'Postiional arg not expected following named arguments.'
                    f'Line: {input}')
            if pos_arg_index >= len(pos_arg_indices):
                raise RuntimeError(
                    f'Positional argument not expected: "{args[index]}"')
            kwargs[pos_arg_indices[pos_arg_index]] = args[index]
            pos_arg_index += 1
            index += 1

    def intify(arg_name: str) -> None:
        if kwargs[arg_name]:
            if kwargs[arg_name] is None or kwargs[arg_name] == '~':
                kwargs[arg_name] = None
            else:
                kwargs[arg_name] = int(kwargs[arg_name])

    intify('start')
    intify('end')
    intify('indent')

    return kwargs
