import inspect
import os
from functools import wraps
from pathlib import Path
from typing import Callable

from loguru import logger

from .db import MyDB


def _pytest_running() -> bool:
    if "PYTEST_CURRENT_TEST" in os.environ:
        return True
    return False


class MyLogger:
    def __init__(
        self,
        db_path: Path = None,
        project_folder: Path = None,
        project_metadata: Path = None,
        project_name: str = "Unnamed_Project",
        project_version: str = "0.0.0",
        std_msg: str = "An exception occurred (id {log_id}). Don't worry, we are "
        "looking into it! For dev, type {command_line} to see more details.",
        enqueue: bool = True,
    ):
        """Logger class to handle exception logging. Logs exceptions in sqlite3
        database. Doesn't log when pytest is running.

        If `std_msg` contains the placeholder `{log_id}`, it will be
        replaced with the log file path according to the `opt_print` option.

        Args:
            db_path (Path): Path to the sqlite3 database file. Defaults to None. If None
                , uses `%APPDATA%/my_logger/logs.db` on Windows and
                `~/.local/share/my_logger/logs.db` on Linux.
                Keep this equal in all your projects to have a centralized log database.
            project_folder (Path, optional): Path to the project folder in
                site-pacakges. Used to automatically extract project metadata.
                Defaults to None.
            project_metadata (Path, optional): Path to the METADATA file of the project.
                Used to automatically extract project metadata if project_folder is None
                or can't get project metadata using project_folder. Defaults to None.
            project_name (str): Name of the project. Used if project metadata can't be
                found. Defaults to "Unnamed_Project".
            project_version (str): Version of the project. Used if project metadata
                can't be found. Defaults to "0.0.0".
            std_msg (str): Standard message to be printed when an exception is logged.
                Defaults to "An Exception occurred (id {log_id}). Don't worry, we are
                looking into it! For dev, type {command_line} to see more details.".
            enqueue (bool): Whether to use enqueue in loguru logger sink. Defaults to
                True.
        """
        self.std_msg = std_msg
        if project_folder is not None:
            site_packages = project_folder.parent
            dist_info = list(site_packages.glob(f"{project_folder.stem}-*.dist-info"))[
                0
            ]
            metadata_file: Path = dist_info / "METADATA"
            if metadata_file.exists():
                project_metadata = metadata_file
        if project_metadata is not None and project_metadata.exists():
            lines = project_metadata.read_text(encoding="utf-8").splitlines()
            for line in lines:
                if line.startswith("Name:"):
                    project_name = line.split(":", 1)[1].strip()
                elif line.startswith("Version:"):
                    project_version = line.split(":", 1)[1].strip()
        self.project_name = project_name
        self.project_version = project_version
        self.my_db = MyDB(db_path)
        self.enqueue = enqueue

    def log_exception(self, one_time_message: str = None, header_exc: str = "") -> None:
        """Logs the current exception using the logger. Does nothing if pytest is
        running.

        if `one_time_message` contains the placeholder `{log_id}`, it will be
        replaced with the log file path according to the `opt_print` option.

        Args:
            one_time_message (str, optional): Message to be printed when an exception is
                logged. If None, uses the standard message defined in the constructor.
            header_exc (str, optional): Header to be added before the exception log.
                Defaults to "".
        """
        if _pytest_running():
            return
        if one_time_message is not None:
            print_msg = one_time_message
        else:
            print_msg = self.std_msg
        logger.remove()
        sink = logger.add(self.my_db.sqlite_sink, enqueue=self.enqueue)
        logger.bind(
            print_msg=print_msg,
            project_name=self.project_name,
            project_version=self.project_version,
        ).exception(header_exc)
        logger.remove(sink)

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
