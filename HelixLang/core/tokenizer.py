from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    IF = auto()
    WHILE = auto()
    FN = auto()
    TRUE = auto()
    FALSE = auto()
    RETURN = auto()
    LET = auto()
    # Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    # Operators
    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    EQ = auto()          # =
    EQEQ = auto()        # ==
    NEQ = auto()         # !=
    LT = auto()          # <
    GT = auto()          # >
    LTE = auto()         # <=
    GTE = auto()         # >=
    BANG = auto()        # !
    # Punctuation
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    COMMA = auto()       # ,
    SEMICOLON = auto()   # ;
    EOF = auto()


KEYWORDS = {
    "if": TokenType.IF,
    "while": TokenType.WHILE,
    "fn": TokenType.FN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "return": TokenType.RETURN,
    "let": TokenType.LET,
}


class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, line={self.line}, col={self.column})"


class TokenizerError(Exception):
    pass


class Tokenizer:
    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.current_char = self.source[self.position] if self.source else None

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 0
        self.position += 1
        self.column += 1
        if self.position < len(self.source):
            self.current_char = self.source[self.position]
        else:
            self.current_char = None

    def peek(self, offset=1):
        peek_pos = self.position + offset
        if peek_pos < len(self.source):
            return self.source[peek_pos]
        return None

    def tokenize(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
            elif self.current_char == '/' and self.peek() == '/':
                self.skip_line_comment()
            elif self.current_char == '/' and self.peek() == '*':
                self.skip_block_comment()
            elif self.current_char.isalpha() or self.current_char == '_':
                tokens.append(self.tokenize_identifier_or_keyword())
            elif self.current_char.isdigit():
                tokens.append(self.tokenize_number())
            elif self.current_char == '"' or self.current_char == "'":
                tokens.append(self.tokenize_string())
            elif self.current_char in ('+', '-', '*', '/', '=', '!', '<', '>'):
                tokens.append(self.tokenize_operator())
            elif self.current_char in ('(', ')', '{', '}', ',', ';'):
                tokens.append(self.tokenize_punctuation())
            else:
                self.error(f"Unexpected character '{self.current_char}'")
        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_line_comment(self):
        # consume '//'
        self.advance()
        self.advance()
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def skip_block_comment(self):
        # consume '/*'
        self.advance()
        self.advance()
        while True:
            if self.current_char is None:
                self.error("Unterminated block comment")
            if self.current_char == '*' and self.peek() == '/':
                self.advance()
                self.advance()
                break
            else:
                self.advance()

    def tokenize_identifier_or_keyword(self):
        line, column = self.line, self.column
        ident = []
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            ident.append(self.current_char)
            self.advance()
        ident_str = ''.join(ident)
        token_type = KEYWORDS.get(ident_str, TokenType.IDENTIFIER)
        return Token(token_type, ident_str, line, column)

    def tokenize_number(self):
        line, column = self.line, self.column
        num_str = []
        has_dot = False

        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if has_dot:
                    self.error("Malformed number literal with multiple decimal points")
                has_dot = True
            num_str.append(self.current_char)
            self.advance()

        num_value = ''.join(num_str)
        # Convert to int or float accordingly
        if has_dot:
            try:
                val = float(num_value)
            except ValueError:
                self.error("Invalid float literal")
        else:
            try:
                val = int(num_value)
            except ValueError:
                self.error("Invalid integer literal")

        return Token(TokenType.NUMBER, val, line, column)

    def tokenize_string(self):
        line, column = self.line, self.column
        quote_char = self.current_char
        self.advance()  # consume opening quote
        string_chars = []
        while self.current_char is not None and self.current_char != quote_char:
            if self.current_char == '\\':
                self.advance()
                if self.current_char is None:
                    self.error("Unterminated string literal")
                escape_char = self.handle_escape()
                string_chars.append(escape_char)
            else:
                string_chars.append(self.current_char)
                self.advance()
        if self.current_char != quote_char:
            self.error("Unterminated string literal")
        self.advance()  # consume closing quote
        return Token(TokenType.STRING, ''.join(string_chars), line, column)

    def handle_escape(self):
        escapes = {
            'n': '\n',
            't': '\t',
            '"': '"',
            "'": "'",
            '\\': '\\',
            'r': '\r',
        }
        c = self.current_char
        self.advance()
        return escapes.get(c, c)  # default to the char itself if unknown escape

    def tokenize_operator(self):
        line, column = self.line, self.column
        c = self.current_char
        nxt = self.peek()

        # Two-char operators
        if c == '=' and nxt == '=':
            self.advance()
            self.advance()
            return Token(TokenType.EQEQ, '==', line, column)
        if c == '!' and nxt == '=':
            self.advance()
            self.advance()
            return Token(TokenType.NEQ, '!=', line, column)
        if c == '<' and nxt == '=':
            self.advance()
            self.advance()
            return Token(TokenType.LTE, '<=', line, column)
        if c == '>' and nxt == '=':
            self.advance()
            self.advance()
            return Token(TokenType.GTE, '>=', line, column)

        # Single-char operators
        single_char_tokens = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '=': TokenType.EQ,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '!': TokenType.BANG,
        }

        if c in single_char_tokens:
            self.advance()
            return Token(single_char_tokens[c], c, line, column)

        self.error(f"Unknown operator {c}")

    def tokenize_punctuation(self):
        line, column = self.line, self.column
        c = self.current_char
        punct_tokens = {
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            ',': TokenType.COMMA,
            ';': TokenType.SEMICOLON,
        }
        token_type = punct_tokens[c]
        self.advance()
        return Token(token_type, c, line, column)

    def error(self, message):
        raise TokenizerError(f"[Line {self.line}, Column {self.column}] {message}")


# Example usage
if __name__ == "__main__":
    code = '''
    fn add(x, y) {
        return x + y;
    }
    // This is a comment
    let val = 42;
    let pi = 3.14;
    let msg = "Hello, World\\n";
    if val >= 10 {
        val = val - 1;
    }
    '''
    tokenizer = Tokenizer(code)
    tokens = tokenizer.tokenize()
    for token in tokens:
        print(token)
