# helixlang/core/parser.py

from helixlang.core.tokenizer import Token, TokenType
from helixlang.core.ast_nodes import *
from helixlang.core.errors import HelixSyntaxError

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[self.position] if self.tokens else None

    def peek(self, offset=0):
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def advance(self):
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None

    def expect(self, token_type):
        if self.current_token and self.current_token.type == token_type:
            token = self.current_token
            self.advance()
            return token
        else:
            self.error(f"Expected token {token_type}, found {self.current_token}")

    def error(self, message):
        # Raises syntax error with line/column info
        line = self.current_token.line if self.current_token else "EOF"
        col = self.current_token.column if self.current_token else "EOF"
        raise HelixSyntaxError(f"{message} at line {line}, column {col}")

    def parse(self):
        """Parse full input tokens into AST"""
        statements = []
        while self.current_token is not None:
            stmt = self.parse_statement()
            statements.append(stmt)
        return ProgramNode(statements)

    def parse_statement(self):
        """Dispatch parsing based on current token"""
        if self.current_token.type == TokenType.IF:
            return self.parse_if_statement()
        elif self.current_token.type == TokenType.WHILE:
            return self.parse_while_statement()
        elif self.current_token.type == TokenType.FN:
            return self.parse_function_definition()
        elif self.current_token.type == TokenType.LET:
            return self.parse_variable_declaration()
        # add more statements here
        else:
            # fallback to expression statement
            expr = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return ExpressionStatementNode(expr)

    def parse_expression(self, precedence=0):
        """Parse expressions using precedence climbing algorithm"""
        left = self.parse_primary()

        while True:
            op = self.current_token
            if op is None or not self.is_operator(op.type):
                break

            op_precedence = self.get_precedence(op.type)
            if op_precedence < precedence:
                break

            self.advance()
            right = self.parse_expression(op_precedence + 1)
            left = BinaryOpNode(left, op.type, right)

        return left

    def parse_primary(self):
        """Parse literals, variables, parentheses, function calls"""
        token = self.current_token
        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(token.value)
        elif token.type == TokenType.IDENT:
            self.advance()
            # Could be variable or function call
            if self.current_token and self.current_token.type == TokenType.LPAREN:
                return self.parse_function_call(token.value)
            return VariableNode(token.value)
        elif token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        else:
            self.error(f"Unexpected token {token.type}")

    # Additional methods: parse_if_statement, parse_while_statement, parse_function_call, parse_variable_declaration, etc.

    def is_operator(self, token_type):
        # Return True if token_type is a binary operator
        return token_type in {
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.STAR,
            TokenType.SLASH,
            TokenType.EQEQ,
            # etc...
        }

    def get_precedence(self, token_type):
        precedences = {
            TokenType.EQEQ: 1,
            TokenType.PLUS: 2,
            TokenType.MINUS: 2,
            TokenType.STAR: 3,
            TokenType.SLASH: 3,
            # more operators...
        }
        return precedences.get(token_type, 0)

    # Implement parse_if_statement, parse_while_statement, parse_function_call, parse_variable_declaration similarly

