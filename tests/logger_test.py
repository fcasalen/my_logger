import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from src.my_logger import MyLogger, OptPrint

mock_my_logger = MyLogger(Path(".") / "logs")
assert mock_my_logger._pytest_running() is False, (
    "Expected _pytest_running to return "
    "False when it's called outside pytest. This is to avoid the idea of setting a var"
    " at init, because it will return False if the logger is instantiated outside "
    "pytest but used inside pytest."
)


class TestLogException:
    def test_pytest_running(self, tmp_path: Path):
        log_folder = tmp_path
        assert (log_folder / "logs").exists() is False
        my_logger = MyLogger(log_folder / "logs")
        try:
            raise ValueError("Test exception")
        except Exception:
            my_logger.log_exception()

        assert (log_folder / "logs").exists() is False

    def test_creates_log_file_file_name(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(log_folder / "logs")
            try:
                raise ValueError("Test exception")
            except Exception:
                my_logger.log_exception()

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert "ValueError: Test exception" in log_files[0].read_text()
        captured = capsys.readouterr()
        assert (
            captured.out
            == f"Exception {log_files[0].stem}. Don't worry, we are looking into it!\n"
        )

    def test_creates_log_file_full_path(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(log_folder / "logs", opt_print=OptPrint.FULL_PATH)
            try:
                raise ValueError("Test exception for full path")
            except Exception:
                my_logger.log_exception()

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert "ValueError: Test exception for full path" in log_files[0].read_text()
        captured = capsys.readouterr()
        expected_path = str(log_files[0].resolve())
        assert (
            captured.out
            == f"Exception {expected_path}. Don't worry, we are looking into it!\n"
        )

    def test_creates_log_file_rel_path(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(log_folder / "logs", opt_print=OptPrint.REL_PATH)
            try:
                raise ValueError("Test exception for rel path")
            except Exception:
                my_logger.log_exception()

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert "ValueError: Test exception for rel path" in log_files[0].read_text()
        captured = capsys.readouterr()
        expected_path = str(log_files[0].relative_to(log_folder))
        assert (
            captured.out
            == f"Exception {expected_path}. Don't worry, we are looking into it!\n"
        )

    def test_creates_log_file_std_msg_no_placeholder(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        custom_std_msg = "An error has occurred. Please contact support."
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(log_folder / "logs", std_msg=custom_std_msg)
            try:
                raise ValueError("Test exception with custom std msg")
            except Exception:
                my_logger.log_exception()

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert (
            "ValueError: Test exception with custom std msg" in log_files[0].read_text()
        )
        captured = capsys.readouterr()
        assert captured.out == f"{custom_std_msg}\n"

    def test_creates_log_file_std_msg_with_placeholder(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        custom_std_msg = "Error logged at {opt_print_adj}. Please check the log file."
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(
                log_folder / "logs",
                opt_print=OptPrint.FILE_NAME,
                std_msg=custom_std_msg,
            )
            try:
                raise ValueError("Test exception with custom std msg and placeholder")
            except Exception:
                my_logger.log_exception()

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert (
            "ValueError: Test exception with custom std msg and placeholder"
            in log_files[0].read_text()
        )
        captured = capsys.readouterr()
        assert (
            captured.out
            == f"Error logged at {log_files[0].stem}. Please check the log file.\n"
        )

    def test_custom_msg(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        custom_msg = "Custom error occurred"
        with patch("os.environ", return_value={}):
            try:
                my_logger = MyLogger(log_folder / "logs")
                raise RuntimeError("Another test exception")
            except Exception:
                my_logger.log_exception(one_time_message=custom_msg)

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert "RuntimeError: Another test exception" in log_files[0].read_text()
        captured = capsys.readouterr()
        assert captured.out == "Custom error occurred\n"

    def test_header_exc(self, tmp_path: Path):
        log_folder = tmp_path
        header = "=== Exception Log Start ==="
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(log_folder / "logs")
            try:
                raise KeyError("Test exception with header")
            except Exception:
                my_logger.log_exception(header_exc=header)

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        log_content = log_files[0].read_text()
        assert header in log_content
        assert "KeyError: 'Test exception with header'" in log_content


class TestDecorator:
    def test_sync(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator()
            def func_that_raises():
                raise IndexError("Decorator test exception")

            func_that_raises()

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert "IndexError: Decorator test exception" in log_files[0].read_text()
        captured = capsys.readouterr()
        assert captured.out.startswith("Exception") and captured.out.endswith(
            ". Don't worry, we are looking into it!\n"
        )

    def test_sync_re_raise(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with (
            pytest.raises(Exception, match="Decorator test exception"),
            patch("os.environ", return_value={}),
        ):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator(re_raise=True)
            def func_that_raises():
                raise IndexError("Decorator test exception")

            func_that_raises()

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert "IndexError: Decorator test exception" in log_files[0].read_text()
        captured = capsys.readouterr()
        assert captured.out.startswith("Exception") and captured.out.endswith(
            ". Don't worry, we are looking into it!\n"
        )

    def test_async(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with (
            pytest.raises(Exception, match="'Async decorator test exception'"),
            patch("os.environ", return_value={}),
        ):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator(re_raise=True)
            async def async_func_that_raises():
                raise KeyError("Async decorator test exception")

            asyncio.run(async_func_that_raises())

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        assert "KeyError: 'Async decorator test exception'" in log_files[0].read_text()
        captured = capsys.readouterr()
        assert captured.out.startswith("Exception") and captured.out.endswith(
            ". Don't worry, we are looking into it!\n"
        )

    def test_with_try_except(self, tmp_path: Path):
        log_folder = tmp_path
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator()
            def func_that_raises():
                try:
                    return 1 / 0
                except Exception:
                    return 1_000_000

            result = func_that_raises()

        assert result == 1_000_000

    def test_passing_one_time_message_and_header(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        custom_msg = "One-time custom error message"
        header = "--- Start of Exception Log ---"
        with patch("os.environ", return_value={}):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator(
                one_time_message=custom_msg, header_exc=header
            )
            def func_that_raises():
                raise ValueError("Test exception for one-time message and header")

            func_that_raises()

        log_files = list((log_folder / "logs").glob("*.log"))
        assert len(log_files) == 1
        log_content = log_files[0].read_text()
        assert header in log_content
        assert (
            "ValueError: Test exception for one-time message and header" in log_content
        )
        captured = capsys.readouterr()
        assert captured.out == f"{custom_msg}\n"
