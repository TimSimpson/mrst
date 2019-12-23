import typing as t
import typing_extensions as te


IncludeFileArgs = te.TypedDict(
    "IncludeFileArgs",
    {
        "input_file": str,
        "start": t.Optional[int],
        "end": t.Optional[int],
        "indent": t.Optional[int],
        "section": t.Optional[str],
        "start_after": t.Optional[str],
        "end_before": t.Optional[str],
    },
)


def make_include_reg(prefix: str) -> str:
    return f"{prefix} "  # "([^"]*)" ?(.*)$'


def _split_args(args: str) -> t.List[str]:
    index = 0
    result = []
    while index < len(args):
        while len(args) > index and args[index] == " ":
            index += 1

        if len(args) <= index:
            break

        if args[index] == "=":
            result.append("=")
            index += 1
        elif args[index] == '"':
            index += 1
            start_index = index
            while len(args) > index and args[index] != '"':
                if args[index] == "\\":
                    if len(args) > index + 1 and args[index + 1] == '"':
                        index += 2
                else:
                    index += 1
            result.append(args[start_index:index].replace('\\"', '"'))
            index += 1
        else:
            start_index = index
            while len(args) > index and args[index] not in [" ", "="]:
                index += 1
            result.append(args[start_index:index])

    return result


def parse_include_file_args(input: str) -> IncludeFileArgs:
    # rest = matches.groups()
    args = _split_args(input.strip())
    if len(args) < 1:
        raise ValueError("Expected at least one arg.")
    print(f"args={args}")
    input_file = args[0]
    kwargs: t.Dict[str, t.Optional[str]] = {
        "start": None,
        "end": None,
        "indent": None,
        "section": None,
        "start_after": None,
        "end_before": None,
    }
    pos_arg_indices = ["start", "end", "indent"]
    pos_arg_index = 0
    index = 1
    while len(args) > index:
        if len(args) > (index + 1) and args[index + 1] == "=":
            if len(args) > (index + 2):
                name = args[index]
                value = args[index + 2]
                if name not in kwargs:
                    raise RuntimeError(f'Unknown dumpfile arg: "{name}"')
                elif kwargs[name] is not None:
                    raise RuntimeError(f"dumpfile arg {name} set twice")
                kwargs[name] = value
                index += 3
                pos_arg_index = -1
            else:
                raise RuntimeError(
                    'Syntax error: "=" is expected to be followed by an '
                    "argument (this is a name / value pair sitch)."
                    f"Line: {input}"
                )
        else:
            if pos_arg_index < 0:
                raise RuntimeError(
                    "Postiional arg not expected following named arguments."
                    f"Line: {input}"
                )
            if pos_arg_index >= len(pos_arg_indices):
                raise RuntimeError(
                    f'Positional argument not expected: "{args[index]}"'
                )
            kwargs[pos_arg_indices[pos_arg_index]] = args[index]
            pos_arg_index += 1
            index += 1

    def intify(arg_value: t.Optional[str]) -> t.Optional[int]:
        if (not arg_value) or arg_value == "~":
            return None
        else:
            return int(arg_value)

    return {
        "input_file": input_file,
        "start": intify(kwargs["start"]),
        "end": intify(kwargs["end"]),
        "indent": intify(kwargs["indent"]),
        "section": kwargs["section"],
        "start_after": kwargs["start_after"],
        "end_before": kwargs["end_before"],
    }
