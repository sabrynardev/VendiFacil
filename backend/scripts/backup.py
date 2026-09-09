import argparse
import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um backup consistente do banco do Vendi.")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", "sqlite:///./marketpulse.db"))
    parser.add_argument("--output", default="../backups")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    if args.database_url.startswith("sqlite:///"):
        source = Path(args.database_url.removeprefix("sqlite:///")).resolve()
        target = output / f"vendi-{stamp}.db"
        with sqlite3.connect(source) as origin, sqlite3.connect(target) as backup:
            origin.backup(backup)
            result = backup.execute("PRAGMA quick_check").fetchone()
        if not result or result[0] != "ok":
            target.unlink(missing_ok=True)
            raise SystemExit("O backup falhou na verificação de integridade.")
    else:
        target = output / f"vendi-{stamp}.dump"
        parsed = urlparse(args.database_url.replace("postgresql+psycopg", "postgresql", 1))
        subprocess.run(["pg_dump", "--format=custom", "--file", str(target), parsed.geturl()], check=True)
    print(f"Backup criado e verificado: {target}")


if __name__ == "__main__":
    main()
