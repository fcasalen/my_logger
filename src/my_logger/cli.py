import argparse
import sqlite3
from pathlib import Path

from .logger import DB_DEFAULT_PATH


def get_stats(db_path: Path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT project_name, COUNT(*) FROM logs GROUP BY project_name"
        )
        print(f"{'Project Name':<30} | {'Logs Count':<10}")
        print("-" * 45)
        for row in cursor:
            print(f"{row[0]:<30} | {row[1]:<10}")


def export_logs(
    db_path: Path,
    folder_path: Path = None,
    project_name: str = None,
    ids: list[str] = None,
):
    sql_stmt = "SELECT id, exception_text FROM logs WHERE"
    if project_name is not None:
        sql_stmt += " project_name = ?"
        params = (project_name,)
    if ids is not None:
        if project_name is not None:
            sql_stmt += " AND"
        sql_stmt += " id IN ({})".format(",".join("?" * len(ids)))
        params = params + tuple(ids) if project_name is not None else tuple(ids)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql_stmt, params)
        logs = cursor.fetchall()

        if not logs:
            print("No logs found for the given criteria.")
            return

        for log in logs:
            with open(folder_path / f"{log.id}.log", "w", encoding="utf-8") as f:
                msg = ""
                for k, v in log.items():
                    msg += f"{k}: {v}\n"
                msg += "\n"
                f.write(msg)
        print(f"Exported {len(logs)} logs to {str(folder_path)}")


def update_commit(
    db_path: Path, id: str, commit_hash: str = None, bug_fix_info: str = None
):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE logs SET bug_fix_commit = ? , bug_fix_info = ?, bug_fix_date = "
            "CURRENT_TIMESTAMP WHERE id = ?",
            (commit_hash, bug_fix_info, id),
        )
        print(f"Log ID {id} updated!")


def main():
    parser = argparse.ArgumentParser(description="MyLogger CLI - Manage Error Logs")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to the SQLite database file. If None, uses default path. It will "
        "persist across commands and over time.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # db_path setup

    # Command: status
    subparsers.add_parser("status", help="Show log counts per project")

    # Command: export
    export_parser = subparsers.add_parser(
        "export", help="Export logs for a project or a single log ID"
    )
    export_parser.add_argument(
        "--folder-path",
        default=None,
        help="Folder to export logs to. Defaults to current directory.",
    )
    export_parser.add_argument("--project_name", default=None, help="Project name")
    export_parser.add_argument(
        "--ids", nargs="*", default=None, help="Specific Log Entry IDs to export"
    )

    # Command: resolve
    resolve_parser = subparsers.add_parser("resolve", help="Link a commit to a log ID")
    resolve_parser.add_argument("--id", required=True, type=int, help="Log Entry ID")
    resolve_parser.add_argument("--commit", default=None, help="Commit hash/message")
    resolve_parser.add_argument(
        "--info",
        default=None,
        help="Information about how the bug was solved. Main use if the commit is not "
        "available and to future evaltuations about bug fixes.",
    )

    args = parser.parse_args()

    if args.db_path:
        with open(Path(__file__).parent / "db_path.txt", "w", encoding="utf-8") as f:
            f.write(args.db_path)
    if not (Path(__file__).parent / "db_path.txt").exists():
        with open(Path(__file__).parent / "db_path.txt", "w", encoding="utf-8") as f:
            f.write(str(DB_DEFAULT_PATH))
    with open(Path(__file__).parent / "db_path.txt", "r", encoding="utf-8") as f:
        db_path = Path(f.read().strip())

    if db_path.exists() is False:
        raise FileNotFoundError(
            f"Database file not found at {str(db_path)}. Please provide a valid path "
            "using --db-path."
        )

    if args.command == "status":
        get_stats(db_path)
    elif args.command == "export":
        folder_path = Path(args.folder_path) if args.folder_path else Path.cwd()
        folder_path.mkdir(parents=True, exist_ok=True)
        if args.project_name is None and args.ids is None:
            print("Please provide either --project_name or --ids to export logs.")
            return
        export_logs(
            db_path=db_path,
            folder_path=folder_path,
            project_name=args.project_name,
            ids=args.ids,
        )
    elif args.command == "resolve":
        if args.commit is None and args.info is None:
            print("Please provide at least --commit or --info to update the log entry.")
            return
        update_commit(
            db_path=db_path,
            id=str(args.id),
            commit_hash=args.commit,
            bug_fix_info=args.info,
        )


if __name__ == "__main__":
    main()
