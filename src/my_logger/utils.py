import re
import traceback


def extract_line_number_from_message_traceback(
    message: str, traceback_obj: traceback.extract_tb
) -> int | None:
    stack = traceback.extract_tb(traceback_obj)
    if stack:
        last_frame = stack[-1]  # The last item is the point of origin
        return last_frame.lineno
    pattern = r'File "(.*?)", line (\d+), in (.*)'
    matches = re.findall(pattern, str(message))
    return int(matches[-1][1]) if matches else None
