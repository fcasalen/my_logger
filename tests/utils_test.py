import sys

from src.my_logger import utils


def test_extract_line_number_from_message_traceback_with_stack():
    """Test extracting line number when traceback stack exists."""
    try:
        1 / 0
    except ZeroDivisionError:
        tb = sys.exc_info()[2]
        result = utils.extract_line_number_from_message_traceback("", tb)
        assert isinstance(result, int)
        assert result > 0
