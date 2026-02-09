"""
WCPS Query Validator
"""
from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from src.wcps_parser.wcpsLexer import wcpsLexer
from src.wcps_parser.wcpsParser import wcpsParser


def validate_wcps_query(wcps_query: str) -> str:
    """
    Validates a WCPS query string using the ANTLR4 parser.

    Returns:
        "VALID" if the query is syntactically correct
        "INVALID SYNTAX: <error message>" if there's a syntax error
    """
    try:
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
        # success
        return "VALID"
    except Exception as e:
        # fail
        return f"INVALID SYNTAX: {str(e)}"


class ValidationErrorListener(ErrorListener):
    """
    Custom error listener to collect parsing errors.
    """

    def __init__(self):
        super().__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        """Called when a syntax error is recognized."""
        error_msg = f"Line {line}:{column} {msg}"
        self.errors.append(error_msg)
        raise Exception(" | ".join(self.errors))
