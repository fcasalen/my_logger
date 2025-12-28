import os
from loguru import logger
from pathlib import Path
from pathlib import Path
from uuid import uuid4


def pytest_running() -> bool:
    if "PYTEST_CURRENT_TEST" in os.environ:
        return True
    return False

class MyLogger:
    def __init__(self, folder_log_path: Path):
        """Logger class to handle exception logging. Logs one exception per 
        file in the specified folder / logs subfolder. Doesn't log when pytest 
        is running.

        Args:
            folder_log_path (Path): Path to the folder where logs will be stored
        """           
        self.folder_log_path = folder_log_path

    def log_exception(self, msg:str = None) -> None:
        """Logs ONE exception per file in the logs subfolder of the specified 
        folder. Doesn't log when pytest is running.

        Args:
            msg (str): A custom message to be printed before the exception log.
        """
        if pytest_running():
            return 
        logs_path = Path(self.folder_log_path) / "logs"
        logs_path.mkdir(exist_ok=True)
        error_code = uuid4()
        logger.remove()
        sink = logger.add(logs_path / f"{error_code}.log", level="ERROR")
        logger.exception("--- Exception Logged ---")
        if msg is None:
            print(f"Exception {error_code}. Don't worry, we are looking into it!")
        else:
            print(msg)
        logger.remove(sink)
