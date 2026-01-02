import linecache
import os
import sqlite3
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from . import utils

sqlite3.register_adapter(datetime, lambda val: val.isoformat())


class MyDB:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path
        if self.db_path is None:
            self.db_path = (
                Path(os.environ.get("APPDATA") or Path.home() / ".local/share")
                / "my_logger/logs.db"
            )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    project_version TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line INTEGER NOT NULL,
                    function TEXT NOT NULL,
                    line_code TEXT NOT NULL,
                    exception_type TEXT NOT NULL,
                    exception_value TEXT NOT NULL,
                    level_name TEXT,
                    level_no INTEGER,
                    level_icon TEXT,
                    process_id INTEGER,
                    process_name TEXT,
                    thread_id INTEGER,
                    thread_name TEXT,
                    message TEXT NOT NULL,
                    module TEXT NOT NULL,
                    name TEXT NOT NULL,
                    time INT NOT NULL,
                    elapsed FLOAT,
                    bug_fix_info TEXT DEFAULT NULL,
                    bug_fix_commit TEXT DEFAULT NULL,
                    bug_fix_date INT DEFAULT NULL
                );
            """)

    @contextmanager
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _emergency_log(
        self, error_msg: str, e: Exception, old_sql: str, old_db_dict: dict
    ) -> int:
        line = utils.extract_line_number_from_message_traceback(error_msg, None)
        db_dict = {
            "project_name": "my_logger",
            "project_version": "unknown",
            "file_path": __file__,
            "line": line,
            "function": "insert_into_db",
            "line_code": "",
            "exception_type": type(e).__name__,
            "exception_value": str(e),
            "message": f"Failed to insert log: {error_msg}",
            "module": __name__,
            "name": "my_logger",
            "time": datetime.now().timestamp(),
        }
        columns = ", ".join(db_dict.keys())
        placeholders = ", ".join(["?"] * len(db_dict))
        sql = f"INSERT INTO logs ({columns}) VALUES ({placeholders})"
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, list(db_dict.values()))
                generated_id = cursor.lastrowid
                id = generated_id
            print(f"Database error: {error_msg}")
            print(f"sql attempted: {old_sql}")
            print(f"data attempted: {old_db_dict}")
            print("a log will be created to my_logger project")
            return id
        except Exception as e_critical:
            print(f"Critical failure: unable to log to database. {e_critical}")
            return None

    def insert_into_db(self, db_dict: dict) -> int:
        if not isinstance(db_dict, dict) or len(db_dict) == 0:
            print("insert_into_db called with invalid db_dict: ", db_dict)
            return None
        columns = ", ".join(db_dict.keys())
        placeholders = ", ".join(["?"] * len(db_dict))
        sql = f"INSERT INTO logs ({columns}) VALUES ({placeholders})"
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, list(db_dict.values()))
                generated_id = cursor.lastrowid
                return generated_id
        except Exception as e:
            return self._emergency_log(traceback.format_exc(), e, sql, db_dict)

    def sqlite_sink(self, message):
        db_dict = {}
        record = message.record
        info = {
            k: v
            for k, v in record.items()
            if k
            in [
                "elapsed",
                "exception",
                "file",
                "function",
                "level",
                "message",
                "module",
                "name",
                "process",
                "thread",
                "time",
            ]
        }
        exception = record.get("exception")
        if exception:
            db_dict["line"] = utils.extract_line_number_from_message_traceback(
                message, exception.traceback
            )
        for k, v in info.items():
            if k == "exception":
                db_dict["exception_type"] = str(v.type.__name__)
                db_dict["exception_value"] = str(v.value)
            elif k == "file":
                db_dict["file_path"] = str(v.path)
            elif k == "level":
                db_dict[f"{k}_name"] = v.name
                db_dict[f"{k}_no"] = v.no
                db_dict[f"{k}_icon"] = v.icon
            elif k in ["process", "thread"]:
                db_dict[f"{k}_id"] = v.id
                db_dict[f"{k}_name"] = v.name
            elif k == "elapsed":
                db_dict[k] = v.total_seconds()
            elif k == "time":
                db_dict[k] = v.timestamp()
            else:
                db_dict[k] = v
        extra = record.get("extra", {})
        db_dict.update(extra)
        line_no = db_dict.get("line", record.get("line"))
        db_dict["line_code"] = linecache.getline(db_dict["file_path"], line_no).strip()
        db_dict["message"] = message
        print_msg: str = record.get("extra", {}).get("print_msg")
        db_dict.pop("print_msg", None)
        id = self.insert_into_db(db_dict)
        print(
            print_msg.format(
                log_id=str(id), command_line='"my_logger -h" for more info'
            )
        )
