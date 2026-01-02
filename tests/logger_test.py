import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from src.my_logger import MyLogger
from src.my_logger.logger import _pytest_running

assert _pytest_running() is False, (
    "Expected _pytest_running to return "
    "False when it's called outside pytest. This is to avoid the idea of setting a var"
    " at init, because it will return False if the logger is instantiated outside "
    "pytest but used inside pytest."
)


class TestLoggerInit:
    def test_init_with_project_folder(self, tmp_path: Path):
        db_path = tmp_path / "logs.db"
        site_packages_folder = tmp_path / "site_packages"
        project_folder = site_packages_folder / "project"
        project_folder.mkdir(parents=True, exist_ok=True)
        dist_info = site_packages_folder / "project-1.0.0.dist-info"
        dist_info.mkdir(parents=True, exist_ok=True)
        metadata_file = dist_info / "METADATA"
        metadata_file.write_text(
            "Name: TestProject\nVersion: 1.0.0\n", encoding="utf-8"
        )
        assert db_path.exists() is False
        logger = MyLogger(db_path=db_path, project_folder=project_folder)
        assert logger.project_name == "TestProject"
        assert logger.project_version == "1.0.0"
        assert db_path.exists() is True


class TestLogException:
    def test_pytest_running(self, tmp_path: Path):
        db_file = tmp_path / f"{uuid4()}_logs.db"
        assert db_file.exists() is False
        my_logger = MyLogger(
            db_file, project_name="TestProject", project_version="1.0.0", enqueue=False
        )
        try:
            raise ValueError("Test exception")
        except Exception:
            my_logger.log_exception()
        assert db_file.exists() is True

    def test_creates_log(self, tmp_path: Path, capsys):
        db_file = tmp_path / f"{uuid4()}_logs.db"
        with patch.dict("os.environ", {}, clear=True):
            my_logger = MyLogger(
                db_file,
                project_name="TestProject",
                project_version="1.0.0",
                enqueue=False,
            )
            try:
                return 1 / 0
            except Exception:
                my_logger.log_exception()

        with my_logger.my_db.get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM logs")
            logs = cursor.fetchall()
            assert len(logs) == 1
            assert logs[0]["line"] == 62
            assert logs[0]["exception_type"] == "ZeroDivisionError"
            assert logs[0]["exception_value"] == "division by zero"
        captured = capsys.readouterr()
        assert (
            captured.out
            == "An exception occurred (id 1). Don't worry, we are looking into it! For"
            ' dev, type "my_logger -h" for more info to see more details.\n'
        )

    def test_creates_log_std_msg_no_placeholder(self, tmp_path: Path, capsys):
        logs_folder = tmp_path / "logs"
        custom_std_msg = "An error has occurred. Please contact support."
        with patch.dict("os.environ", {}, clear=True):
            my_logger = MyLogger(
                logs_folder / "logs.db", std_msg=custom_std_msg, enqueue=False
            )
            try:
                raise ValueError("Test exception with custom std msg")
            except Exception:
                my_logger.log_exception()

        with my_logger.my_db.get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM logs")
            count = cursor.fetchone()[0]
            assert count == 1
        captured = capsys.readouterr()
        assert captured.out == "An error has occurred. Please contact support.\n"

    def test_creates_log_std_msg_with_placeholder(self, tmp_path: Path, capsys):
        logs_folder = tmp_path / "logs"
        custom_std_msg = "Error logged at {log_id}. Please check the log file."
        with patch.dict("os.environ", {}, clear=True):
            my_logger = MyLogger(
                logs_folder / "logs.db",
                std_msg=custom_std_msg,
                enqueue=False,
            )
            try:
                raise ValueError("Test exception with custom std msg and placeholder")
            except Exception:
                my_logger.log_exception()

        with my_logger.my_db.get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM logs")
            count = cursor.fetchone()[0]
            assert count == 1
        captured = capsys.readouterr()
        assert captured.out == "Error logged at 1. Please check the log file.\n"

    def test_custom_msg(self, tmp_path: Path, capsys):
        logs_folder = tmp_path / "logs"
        custom_msg = "Custom error occurred"
        with patch.dict("os.environ", {}, clear=True):
            try:
                my_logger = MyLogger(logs_folder / "logs.db", enqueue=False)
                raise RuntimeError("Another test exception")
            except Exception:
                my_logger.log_exception(one_time_message=custom_msg)
        with my_logger.my_db.get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM logs")
            count = cursor.fetchone()[0]
            assert count == 1
        captured = capsys.readouterr()
        assert captured.out == "Custom error occurred\n"

    def test_header_exc(self, tmp_path: Path):
        logs_folder = tmp_path / "logs"
        header = "=== Exception Log Start ==="
        with patch.dict("os.environ", {}, clear=True):
            my_logger = MyLogger(logs_folder / "logs.db", enqueue=False)
            try:
                raise KeyError("Test exception with header")
            except Exception:
                my_logger.log_exception(header_exc=header)

        with my_logger.my_db.get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM logs")
            count = cursor.fetchone()[0]
            assert count == 1
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM logs")
            log = cursor.fetchone()
            assert header in log["message"]
            assert "KeyError: 'Test exception with header'" in log["message"]


class TestDecorator:
    def test_sync(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with patch.dict("os.environ", {}, clear=True):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator()
            def func_that_raises():
                raise IndexError("Decorator test exception")

            func_that_raises()

        with my_logger.my_db.get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM logs")
            logs = cursor.fetchall()
            assert len(logs) == 1
            assert logs[0]["exception_type"] == "IndexError"
            assert logs[0]["exception_value"] == "Decorator test exception"
        captured = capsys.readouterr()
        assert (
            captured.out
            == "An exception occurred (id 1). Don't worry, we are looking into it! For"
            ' dev, type "my_logger -h" for more info to see more details.\n'
        )

    def test_sync_re_raise(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with (
            pytest.raises(Exception, match="Decorator test exception"),
            patch.dict("os.environ", {}, clear=True),
        ):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator(re_raise=True)
            def func_that_raises():
                raise IndexError("Decorator test exception")

            func_that_raises()

        with my_logger.my_db.get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM logs")
            logs = cursor.fetchall()
            assert len(logs) == 1
            assert logs[0]["exception_type"] == "IndexError"
            assert logs[0]["exception_value"] == "Decorator test exception"
        captured = capsys.readouterr()
        assert (
            captured.out
            == "An exception occurred (id 1). Don't worry, we are looking into it! For"
            ' dev, type "my_logger -h" for more info to see more details.\n'
        )

    def test_async(self, tmp_path: Path, capsys):
        log_folder = tmp_path
        with (
            pytest.raises(Exception, match="'Async decorator test exception'"),
            patch.dict("os.environ", {}, clear=True),
        ):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator(re_raise=True)
            async def async_func_that_raises():
                raise KeyError("Async decorator test exception")

            asyncio.run(async_func_that_raises())

        with my_logger.my_db.get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM logs")
            logs = cursor.fetchall()
            assert len(logs) == 1
            assert logs[0]["exception_type"] == "KeyError"
            assert logs[0]["exception_value"] == "'Async decorator test exception'"
        captured = capsys.readouterr()
        assert (
            captured.out
            == "An exception occurred (id 1). Don't worry, we are looking into it! For"
            ' dev, type "my_logger -h" for more info to see more details.\n'
        )

    def test_with_try_except(self, tmp_path: Path):
        log_folder = tmp_path
        with patch.dict("os.environ", {}, clear=True):
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
        with patch.dict("os.environ", {}, clear=True):
            my_logger = MyLogger(log_folder / "logs")

            @my_logger.log_exception_decorator(
                one_time_message=custom_msg, header_exc=header
            )
            def func_that_raises():
                raise ValueError("Test exception for one-time message and header")

            func_that_raises()

        with my_logger.my_db.get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM logs")
            logs = cursor.fetchall()
            assert len(logs) == 1
            assert logs[0]["exception_type"] == "ValueError"
            assert (
                logs[0]["exception_value"]
                == "Test exception for one-time message and header"
            )
            assert header in logs[0]["message"]
        captured = capsys.readouterr()
        assert captured.out == f"{custom_msg}\n"
