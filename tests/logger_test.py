import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from src.my_logger import MyLogger


def test_pytest_running(tmp_path: Path):
    log_folder = tmp_path
    assert (log_folder / "logs").exists() is False
    my_logger = MyLogger(log_folder)
    try:
        raise ValueError("Test exception")
    except Exception:
        my_logger.log_exception()

    assert not (log_folder / "logs").exists()


def test_log_exception_creates_log_file(tmp_path: Path, capsys):
    log_folder = tmp_path
    assert (log_folder / "logs").exists() is False
    my_logger = MyLogger(log_folder)
    with patch("os.environ", return_value={}):
        try:
            raise ValueError("Test exception")
        except Exception:
            my_logger.log_exception()

    assert (log_folder / "logs").exists() is True
    log_files = list((log_folder / "logs").glob("*.log"))
    assert len(log_files) == 1
    assert "ValueError: Test exception" in log_files[0].read_text()
    captured = capsys.readouterr()
    assert captured.out.endswith(". Don't worry, we are looking into it!\n")
    assert captured.out.startswith("Exception")


def test_log_exception_custom_msg(tmp_path: Path, capsys):
    log_folder = tmp_path
    assert (log_folder / "logs").exists() is False
    my_logger = MyLogger(log_folder)
    custom_msg = "Custom error occurred"
    with patch("os.environ", return_value={}):
        try:
            raise RuntimeError("Another test exception")
        except Exception:
            my_logger.log_exception(msg=custom_msg)

    assert (log_folder / "logs").exists() is True
    log_files = list((log_folder / "logs").glob("*.log"))
    assert len(log_files) == 1
    assert "RuntimeError: Another test exception" in log_files[0].read_text()
    captured = capsys.readouterr()
    assert captured.out == "Custom error occurred\n"


def test_log_exception_decorator_sync(tmp_path: Path, capsys):
    log_folder = tmp_path
    assert (log_folder / "logs").exists() is False
    my_logger = MyLogger(log_folder)

    @my_logger.log_exception_decorator()
    def func_that_raises():
        raise IndexError("Decorator test exception")

    with patch("os.environ", return_value={}):
        func_that_raises()

    assert (log_folder / "logs").exists() is True
    log_files = list((log_folder / "logs").glob("*.log"))
    assert len(log_files) == 1
    assert "IndexError: Decorator test exception" in log_files[0].read_text()
    captured = capsys.readouterr()
    assert captured.out.startswith("Exception") and captured.out.endswith(
        ". Don't worry, we are looking into it!\n"
    )


def test_log_exception_decorator_sync_re_raise(tmp_path: Path, capsys):
    log_folder = tmp_path
    assert (log_folder / "logs").exists() is False
    my_logger = MyLogger(log_folder)

    @my_logger.log_exception_decorator(re_raise=True)
    def func_that_raises():
        raise IndexError("Decorator test exception")

    with (
        pytest.raises(Exception, match="Decorator test exception"),
        patch("os.environ", return_value={}),
    ):
        func_that_raises()

    assert (log_folder / "logs").exists() is True
    log_files = list((log_folder / "logs").glob("*.log"))
    assert len(log_files) == 1
    assert "IndexError: Decorator test exception" in log_files[0].read_text()
    captured = capsys.readouterr()
    assert captured.out.startswith("Exception") and captured.out.endswith(
        ". Don't worry, we are looking into it!\n"
    )


def test_log_exception_decorator_async(tmp_path: Path, capsys):
    log_folder = tmp_path
    assert (log_folder / "logs").exists() is False
    my_logger = MyLogger(log_folder)

    @my_logger.log_exception_decorator(re_raise=True)
    async def async_func_that_raises():
        raise KeyError("Async decorator test exception")

    with pytest.raises(Exception, match="'Async decorator test exception'"):
        with patch("os.environ", return_value={}):
            asyncio.run(async_func_that_raises())

    assert (log_folder / "logs").exists() is True
    log_files = list((log_folder / "logs").glob("*.log"))
    assert len(log_files) == 1
    assert "KeyError: 'Async decorator test exception'" in log_files[0].read_text()
    captured = capsys.readouterr()
    assert captured.out.startswith("Exception") and captured.out.endswith(
        ". Don't worry, we are looking into it!\n"
    )


def test_log_exception_decorator_with_try_except(tmp_path: Path, capsys):
    log_folder = tmp_path
    assert not (log_folder / "logs").exists()
    my_logger = MyLogger(log_folder)

    @my_logger.log_exception_decorator()
    def func_that_raises():
        try:
            return 1 / 0
        except Exception:
            return 1_000_000

    with patch("os.environ", return_value={}):
        result = func_that_raises()

    assert result == 1_000_000
    assert (log_folder / "logs").exists() is False
