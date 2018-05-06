from enum import Enum
import re
import textwrap
import typing as t

from . import common

# In rst, you can pick whatever char you want for section headers.
# but this list is what appeared in the docs, and is what pandoc uses when
# converting from MarkDown, so it looks like it has to be the standard.
HEADERS_STR = '=-~^\'`'
HEADERS = list(HEADERS_STR)

SEE_FILE_RE = re.compile(common.make_include_reg('// ~see-file'))

FileReader = t.Callable[..., t.Tuple[t.List[str], t.Any]]


class Line(object):
    """Represents a line of text."""

    def __init__(self, line: str) -> None:
        self.line = line

    def class_keyword(self) -> bool:
        return 'class' in self.line

    def starts_with_section_comment(self) -> bool:
        return self.line.startswith('//')

    def starts_with_doc_line(self) -> bool:
        return self.line.startswith('// --')

    def starts_with_rst_section_underline(self) -> t.Optional[str]:
        if (len(self.line) > 4 and
                self.line.startswith('// ') and
                self.line[3] == self.line[4] and
                self.line[3] in HEADERS_STR):
            return self.line[3]
        else:
            return None

    def starts_with(self, text: str) -> bool:
        """True if the line starts with the given text."""
        return self.line.startswith(text)

    def strip_comment_slashes(self) -> str:
        """Removes "// " from the text."""
        if self.line.startswith('// '):
            return self.line[3:]
        elif self.line.startswith('//'):
            return self.line[2:]
        else:
            return self.line

    def text(self) -> str:
        """Just returns the text."""
        return self.line.rstrip()

    def end_class_marker(self) -> bool:
        """Special }; at start of line."""
        return self.line.strip().startswith('};')

    def begin_marker(self) -> bool:
        return self.line.startswith('// ~begin-doc')

    def end_marker(self) -> bool:
        """Has "// end-doc" """
        return self.line.startswith('// ~end-doc')

    def doc_line_with_tail(self) -> bool:
        return self.line.rstrip().endswith('-/')

    def is_include_directive(self) -> bool:
        return self.line.startswith('// ~see-file ')


class TokenType(Enum):
    NONE = 0
    BIG_HEADER = 1
    SECTION_START = 2
    SECTION_DIVIDER = 3
    SECTION_TEXT = 4
    CODE = 5
    EOF = 6
    SEE_FILE = 7


class Token(object):

    def __init__(self,
                 type: TokenType=TokenType.NONE,
                 text: t.List[str]=None,
                 line_number: int=0) -> None:
        self.type = type
        self.text = text or []
        self.line_number = line_number


class Mode(Enum):
    OUTER_SPACE = 0
    SECTION_START = 1
    SECTION_DIVIDER = 2
    SECTION_TEXT = 3
    UNKNOWN_CODE = 4
    CLASS_CODE = 5
    NONCLASS_CODE = 6
    SECTION_HEADER = 7


class Tokenizer:

    def __init__(self) -> None:
        self._line_number = 0
        self._m = Mode.OUTER_SPACE
        self._indent_level = 0
        self._text: t.List[str] = []
        self._section_text_max_dedent = 0

    def read(self, l: Line) -> t.Optional[Token]:
        self._line_number += 1
        if l.is_include_directive():
            return Token(
                    TokenType.SEE_FILE,
                    [l.text()],
                    self._line_number)
        method_name = '_case_{}'.format(self._m.name.lower())
        method = getattr(self, method_name)
        if method is None:
            raise ValueError('Unhandled Mode! {}'.format(method_name))

        return method(l)

    def _case_outer_space(self, l: Line) -> t.Optional[Token]:
        if l.starts_with_doc_line():
            self._m = Mode.SECTION_TEXT
            self._text: t.List[str] = []
            return Token(TokenType.SECTION_START, None, self._line_number)
        elif l.begin_marker():
            self._m = Mode.UNKNOWN_CODE
            self._text: t.List[str] = []
        return None

    # def _case_section_header(self,
    #                          l: Line,
    #                          next_line: Line) -> t.Optional[Token]:
    #         if l.starts_with_doc_line():
    #             tt = TokenType.SECTION_HEADER
    #             t = Token(tt, self._text, self._line_number)
    #             self._m = Mode.SECTION_TEXT
    #             self._section_text_max_dedent = 256
    #             self._text = []
    #             return t
    #         else:
    #             self._text.append(l.strip_comment_slashes().strip())
    #             return None

    def _case_section_text(self, l: Line) -> t.Optional[Token]:
        rst_section = l.starts_with_rst_section_underline()
        if rst_section:
            if l.doc_line_with_tail():
                self._m = Mode.OUTER_SPACE
                self._text = []
            return Token(TokenType.SECTION_DIVIDER, [rst_section],
                         self._line_number)
        elif l.starts_with_section_comment():
            return Token(
                TokenType.SECTION_TEXT,
                [l.strip_comment_slashes()],
                self._line_number)
        else:
            self._m = Mode.UNKNOWN_CODE
            self._text = []
            return self._case_unknown_code(l)

        # elif l.starts_with_doc_line():  # finish section, add Token
        #     dedent_text = []
        #     for text in self._text:
        #         if len(text) >= self._section_text_max_dedent:
        #             dedent_text.append(text[self._section_text_max_dedent:])
        #         else:
        #             dedent_text.append(text)

        #     t = Token(TokenType.SECTION_TEXT, dedent_text, self._line_number)
        #     self._text = []  # reset text buffer
        #     if l.doc_line_with_tail():
        #         self._m = Mode.OUTER_SPACE
        #     else:
        #         self._m = Mode.UNKNOWN_CODE
        #     return t
        # else:
        #     s_text = l.strip_comment_slashes().rstrip()
        #     content = s_text.lstrip()
        #     if len(content) > 0:
        #         spaces = len(s_text) - len(content)
        #         self._section_text_max_dedent = \
        #             min(spaces, self._section_text_max_dedent)

        #     self._text.append(s_text)
        #     return None

    def _case_unknown_code(self, l: Line) -> t.Optional[Token]:
        if l.end_marker():
            self._m = Mode.OUTER_SPACE
            return None
        elif l.class_keyword():
            self._m = Mode.CLASS_CODE
        else:
            self._m = Mode.NONCLASS_CODE
        self._text.append('    {}'.format(l.text()))
        return None

    def _case_class_code(self, l: Line) -> t.Optional[Token]:
        if l.end_class_marker():
            self._text.append('    {}'.format(l.text()))
            self._m = Mode.OUTER_SPACE
            t = Token(TokenType.CODE, self._text, self._line_number)
            self._text = []
            return t
        return self._case_nonclass_code(l)

    def _case_nonclass_code(
            self, l: Line) -> t.Optional[Token]:
        if l.end_marker():
            self._m = Mode.OUTER_SPACE
            t = Token(TokenType.CODE, self._text, self._line_number)
            self._text = []
            return t
        elif l.starts_with_doc_line():
            self._m = Mode.SECTION_TEXT
            t = Token(TokenType.CODE, self._text, self._line_number)
            self._text = []
            return t
        else:
            if len(l.text()) > 0:
                self._text.append('    {}'.format(l.text()))
            else:
                self._text.append('')
            return None


def parse_source(lines: t.List[str], read_file: FileReader) -> t.List[Token]:
    tokens: t.List[Token] = []

    tokenizer = Tokenizer()

    for line in lines:
        result = tokenizer.read(Line(line.rstrip()))
        if result:
            if result.type == TokenType.SEE_FILE:
                kwargs = common.parse_include_file_args(result.text[0][12:])
                other_file_lines, other_file_reader = read_file(
                    **kwargs)
                tokens += parse_source(other_file_lines, other_file_reader)
            else:
                tokens.append(result)

    tokens.append(Token(TokenType.EOF, []))
    return tokens


class SuperTokenType(Enum):
    SECTION_HEADER = 2
    SECTION_TEXT = 3
    CODE = 4


class SuperToken(object):
    """A collapsed token.

    Only has the headers, text, and code blocks.
    """

    def __init__(self,
                 type: SuperTokenType,
                 text: t.List[str],
                 header: t.Optional[int],
                 line_number: int) -> None:
        self.type = type
        self.text = text or []
        self.header = header
        self.line_number = line_number


class TokenCombiner:

    def __init__(self, token_type: SuperTokenType) -> None:
        self._tokens: t.List[Token] = []
        self._token_type = token_type

    def add(self, token: Token) -> None:
        self._tokens.append(token)

    def create_super_token(self) -> t.Optional[SuperToken]:
        if not self._tokens:
            return None
        all_text: t.List[str] = []

        for tok in self._tokens:
            all_text += tok.text

        # if self._token_type == SuperTokenType.SECTION_TEXT:
        #     for i in range(len(all_text)):
        #         assert all_text[i].startswith('// ')
        #         all_text[i] = all_text[i][3]

        # This is probably going to slow things down, so figure out something
        # else soon.
        dedent_text = textwrap.dedent('\n'.join(all_text)).strip().split('\n')

        result = SuperToken(self._token_type,
                            dedent_text,
                            header=None,
                            line_number=self._tokens[0].line_number)
        self._tokens = []
        return result


def create_super_tokens(tokens: t.List[Token]) -> t.List[SuperToken]:
    result: t.List[SuperToken] = []

    section_text = TokenCombiner(SuperTokenType.SECTION_TEXT)
    code = TokenCombiner(SuperTokenType.CODE)

    def finish_combiners() -> None:
        st = section_text.create_super_token() or code.create_super_token()
        if st:
            result.append(st)

    for i in range(len(tokens)):
        current_t = tokens[i]
        next_1 = tokens[i + 1] if i + 1 < len(tokens) else None
        next_2 = tokens[i + 2] if i + 2 < len(tokens) else None

        if current_t.type == TokenType.SECTION_TEXT:
            if (next_1 and next_2 and
                next_1.type == TokenType.SECTION_DIVIDER and
                next_2.type in [TokenType.SECTION_TEXT,
                                TokenType.SECTION_DIVIDER]):
                # We can only ever see one of these. Finish the combiners first
                finish_combiners()
                # then create a header token
                header_char = next_1.text[0][0]
                header_depth = HEADERS_STR.index(header_char)
                result.append(SuperToken(SuperTokenType.SECTION_HEADER,
                                         current_t.text,
                                         header=header_depth,
                                         line_number=current_t.line_number))
            else:
                section_text.add(current_t)
                if next_1 and next_1.type != TokenType.SECTION_TEXT:
                    finish_combiners()
        elif current_t.type == TokenType.CODE:
            code.add(current_t)
            if next_1 != TokenType.CODE:
                finish_combiners()

    return result


def read_source(lines: t.List[str], reader: FileReader) -> t.List[SuperToken]:
    tokens = parse_source(lines, reader)
    return create_super_tokens(tokens)


def translate_cpp_file(lines: t.List[str], section: t.Optional[str],
                       reader: FileReader) -> t.List[str]:
    if not section:
        header_depth = 0
    else:
        header_depth = HEADERS.index(section) + 1

    tokens = read_source(lines, reader)
    output = []
    for token in tokens:
        if token.type == SuperTokenType.SECTION_HEADER:
            if len(token.text) != 1:
                # Looked like a section header, but it wasn't!
                raise ValueError('Section header starting at line {} was '
                                 'malformed.'.format(token.line_number))

            assert token.header is not None
            depth = token.header + header_depth

            header_char = HEADERS[depth % len(HEADERS)]
            output.append(token.text[0].rstrip())
            output.append(header_char * len(token.text[0].rstrip()))
        elif token.type == SuperTokenType.SECTION_TEXT:
            output += token.text
            output.append('')
        elif token.type == SuperTokenType.CODE:
            output.append('.. code-block:: c++\n')

            for cl in token.text:
                cl_lines = cl.split('\n')
                for cl_line in cl_lines:
                    output.append(f'    {cl_line}'.rstrip())
            output.append('')
        else:
            raise AssertionError('Unexpected case: {}'.format(token.type))

    return output
