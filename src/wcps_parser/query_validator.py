from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from .wcpsLexer import wcpsLexer
from .wcpsParser import wcpsParser


def validate_wcps_query(wcps_query: str):
    """
    Validates a WCPS query string.
    Throws a SyntaxError if the query is syntactically incorrect.
    """
    # create input stream from the query string
    input_stream = InputStream(wcps_query)
    # create lexer
    lexer = wcpsLexer(input_stream)
    lexer.removeErrorListeners()
    lexer.addErrorListener(ErrorListener())
    token_stream = CommonTokenStream(lexer)
    token_stream.fill()
    # create parser
    parser = wcpsParser(token_stream)
    # set error handler to collect errors
    parser.removeErrorListeners()
    parser.addErrorListener(ValidationErrorListener())
    # try to parse the query
    parser.wcpsQuery()


class ValidationErrorListener(ErrorListener):
    """
    Custom error listener to collect parsing errors.
    """

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, _recognizer, _offendingSymbol, line, column, msg, _e):
        """Called when a syntax error is recognized."""
        error_msg = f"Line {line}:{column} {msg}"
        self.errors.append(error_msg)
        raise SyntaxError(" | ".join(self.errors))
