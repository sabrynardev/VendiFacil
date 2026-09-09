import argparse
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Restaura um backup do Vendi com confirmação explícita.")
    parser.add_argument("backup")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", "sqlite:///./marketpulse.db"))
    parser.add_argument("--confirm", required=True, choices=["RESTORE"])
    args = parser.parse_args()
    backup = Path(args.backup).resolve(strict=True)

    if args.database_url.startswith("sqlite:///"):
        with sqlite3.connect(backup) as connection:
            result = connection.execute("PRAGMA quick_check").fetchone()
        if not result or result[0] != "ok":
            raise SystemExit("O arquivo informado não é um backup SQLite íntegro.")
        target = Path(args.database_url.removeprefix("sqlite:///")).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, target)
    else:
        parsed = urlparse(args.database_url.replace("postgresql+psycopg", "postgresql", 1))
        subprocess.run(["pg_restore", "--clean", "--if-exists", "--no-owner", "--dbname", parsed.geturl(), str(backup)], check=True)
    print("Restauração concluída. Reinicie o backend e valide /health antes de operar.")


if __name__ == "__main__":
    main()
