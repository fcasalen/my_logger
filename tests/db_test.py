import os
from pathlib import Path
from unittest.mock import patch

from src.my_logger.db import MyDB


class TestDBInit:
    def test_db_init_with_path(self, tmp_path: Path):
        db_path = tmp_path / "test_logs.db"
        db = MyDB(db_path)

        assert db.db_path == db_path
        assert db.db_path.exists()

    def test_db_init_without_path(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))

        db = MyDB()

        assert (
            db.db_path
            == Path(os.environ.get("APPDATA") or Path.home() / ".local/share")
            / "my_logger/logs.db"
        )
        assert db.db_path.exists()


class TestInsertIntoDB:
    def test_success(self, tmp_path: Path):
        db_path = tmp_path / "test.db"
        db = MyDB(db_path)

        test_data = {
            "project_name": "test_project",
            "file_path": "/test/path.py",
            "line": 42,
            "message": "test message",
        }

        result = db.insert_into_db(test_data)

        assert isinstance(result, int)
        assert result > 0

    def test_returns_incremented_id(self, tmp_path: Path):
        db_path = tmp_path / "test.db"
        db = MyDB(db_path)

        test_data = {"message": "test1"}
        id1 = db.insert_into_db(test_data)

        test_data = {"message": "test2"}
        id2 = db.insert_into_db(test_data)

        assert id2 == id1 + 1

    def test_invalid_dict_to_db(self, tmp_path: Path, capsys):
        db_path = tmp_path / "test.db"
        db = MyDB(db_path)

        assert db.insert_into_db({"any": 1}) == 1
        captured = capsys.readouterr()
        assert (
            "sqlite3.OperationalError: table logs has no column named any\n\n"
            "sql attempted: INSERT INTO logs (any) VALUES (?)\n"
            "data attempted: {'any': 1}\n"
            "a log will be created to my_logger project\n" in captured.out
        )

    def test_invalid_dict_to_db_recursive(self, tmp_path: Path, capsys):
        db_path = tmp_path / "test.db"
        db = MyDB(db_path)

        with patch.object(db, "get_conn", side_effect=Exception("another error")):
            assert (
                db._emergency_log(
                    {"any": 1},
                    e=Exception("another error"),
                    old_sql="old_sql",
                    old_db_dict={},
                )
                is None
            )
        captured = capsys.readouterr()
        assert (
            "Critical failure: unable to log to database. another error\n"
            == captured.out
        )

    def test_empty_dict(self, tmp_path: Path, capsys):
        db_path = tmp_path / "test.db"
        db = MyDB(db_path)

        result = db.insert_into_db({})

        assert result is None
        captured = capsys.readouterr()
        assert "insert_into_db called with invalid db_dict:  {}" in captured.out

    def test_insert_to_db_invalid_data_type(self, tmp_path: Path, capsys):
        db_path = tmp_path / "test.db"
        db = MyDB(db_path)

        result = db.insert_into_db("invalid data type")

        assert result is None
        captured = capsys.readouterr()
        assert (
            "insert_into_db called with invalid db_dict:  invalid data type"
            in captured.out
        )
