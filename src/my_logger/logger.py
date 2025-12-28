import inspect
import os
from enum import StrEnum
from functools import wraps
from pathlib import Path
from typing import Callable
from uuid import uuid4

from loguru import logger


class OptPrint(StrEnum):
    FULL_PATH = "full_path"
    REL_PATH = "rel_path"
    FILE_NAME = "file_name"


def pytest_running() -> bool:
    if "PYTEST_CURRENT_TEST" in os.environ:
        return True
    return False


class MyLogger:
    def __init__(
        self,
        folder_log_path: Path,
        opt_print: OptPrint = OptPrint.FILE_NAME,
        std_msg: str = "Exception {opt_print_adj}. Don't worry, we are looking into "
        "it!",
    ):
        """Logger class to handle exception logging. Logs one exception per
        file in the specified folder logs folder. Doesn't log when pytest
        is running.

        If `std_msg` contains the placeholder `{opt_print_adj}`, it will be
        replaced with the log file path according to the `opt_print` option.

        Args:
            folder_log_path (Path): Path to the folder where logs will be stored
            opt_print (OptPrint): Option to print the log file path in the message.
                Can be FULL_PATH (print the full_path), REL_PATH (print the relative
                path including folder_log_path) or FILE_NAME (just the file name
                without extension). Defaults to FILE_NAME.
            std_msg (str): Standard message to be printed when an exception is logged.
                Defaults to "Exception {opt_print_adj}. Don't worry, we are looking
                into it!".
        """
        assert isinstance(opt_print, OptPrint), (
            "opt_print must be an instance of OptPrint"
        )
        self.folder_log_path = folder_log_path
        self.std_msg = std_msg
        self.opt_print = opt_print
        self.pytest_running = pytest_running()
        self.folder_log_path.mkdir(exist_ok=True)

    def log_exception(self, one_time_message: str = None, header_exc: str = "") -> None:
        """Logs ONE exception per file in the logs subfolder of the specified
        folder. Doesn't log when pytest is running.

        if `one_time_message` contains the placeholder `{opt_print_adj}`, it will be
        replaced with the log file path according to the `opt_print` option.

        Args:
            one_time_message (str, optional): Message to be printed when an exception is
                logged. If None, uses the standard message defined in the constructor.
            header_exc (str, optional): Header to be added before the exception log.
                Defaults to "".
        """
        if self.pytest_running:
            return
        error_code = uuid4()
        full_path = self.folder_log_path / f"{error_code}.log"
        rel_path = full_path.relative_to(self.folder_log_path.parent)
        logger.remove()
        sink = logger.add(full_path, level="ERROR")
        logger.exception(header_exc)
        logger.remove(sink)
        if one_time_message is not None:
            msg = one_time_message
        else:
            msg = self.std_msg
        if "opt_print_adj" not in msg:
            print(msg)
            return
        if self.opt_print == OptPrint.FULL_PATH:
            opt_print_adj = str(full_path)
        elif self.opt_print == OptPrint.REL_PATH:
            opt_print_adj = str(rel_path)
        else:
            opt_print_adj = full_path.stem
        print(msg.format(opt_print_adj=opt_print_adj))

    def log_exception_decorator(
        self, re_raise: bool = False, one_time_message: str = None, header_exc: str = ""
    ) -> Callable:
        """
        Decorator that logs any exception raised by the wrapped function.

        Args:
            re_raise (bool): If True, re-raises the exception after logging it.
            one_time_message (str, optional): Message to be printed when an exception
                is logged. If None, uses the standard message defined in the
                constructor.
            header_exc (str, optional): Header to be added before the exception log.
                Defaults to "".

        Returns:
            Callable: The decorated function with exception logging.
        """

        def make_decorator(func):
            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        self.log_exception(
                            one_time_message=one_time_message, header_exc=header_exc
                        )
                        if re_raise:
                            raise e

                return async_wrapper
            else:

                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        self.log_exception(
                            one_time_message=one_time_message, header_exc=header_exc
                        )
                        if re_raise:
                            raise e

                return sync_wrapper

        return make_decorator
