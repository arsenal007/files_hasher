# files_hashing.py
from __future__ import annotations

import time
import socket
import argparse
import logging


from typing import Callable, Iterable, List, Optional, Tuple

from utils.database import (
    create_database,
    save_hashes_to_db,
    get_file_info_from_db,
    delete_file_from_db,
    set_meta
)
from utils.config import Config
from utils.files import FileBackend, SFTPFileBackend
from utils.hash_file import hash_file  # returns (digest, error)

# Import Paramiko-derived exceptions if available; otherwise – stubs for typing/checks.
try:
    from paramiko.ssh_exception import SSHException, NoValidConnectionsError
except Exception:  # pragma: no cover
    class SSHException(Exception): ...
    class NoValidConnectionsError(Exception): ...


logger = logging.getLogger(__name__)

class FileHashingService:


    def __init__(
        self,
        config: Config,
        *,
        backend_factory: Callable[[Config], FileBackend] = SFTPFileBackend,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.backend_factory = backend_factory
        self.sleep = sleep_fn
        
        # read from config with defaults
        self.sleep_after_pass_s = int(self.config.get("SLEEP_AFTER_PASS", 10 * 60))
        self.retry_sleep_s = int(self.config.get("RETRY_SLEEP", 10 * 60))

        self.db_path = config.get("DB_PATH", "file_hashes.db")
        create_database(self.db_path)

    # ---------- Public methods ----------

    def run_forever(self) -> None:
        """Endless runs: each run includes connection retries + 10 minutes of sleep after success."""
        while True:
            self.run_once()                  # one full run (with connection retries inside)
            self._sleep_after_pass()         # 10 minutes after the run

    def run_once(self) -> None:
        """
        One full run: collect the list of files, calculate hashes, and save them to the database.
        If the connection is lost during the run — sleep for 10 minutes and then RETRY the entire run from the beginning
        """
        while True:  # connection retry loop
            backend: Optional[FileBackend] = None
            try:
                backend = self.backend_factory(self.config)
                self._process_all_files(backend)
                return  # successfully finished the run — exit retries
            except Exception as e:
                if self._is_connection_error(e):
                    self._sleep_retry()
                    continue  # try again with a new connection
                raise  # other errors are raised up (non-network)
            finally:
                if backend is not None:
                    try:
                        backend.close()
                    except Exception:
                        pass

    # ---------- Internal logic ----------

    def _process_all_files(self, backend: FileBackend) -> None:
        remote_roots = self.config.get("PATHS", [])
        if not remote_roots:
            logger.warning("PATHS is empty in %s – no files will be processed", self.config.path)
            return
        all_files = self._collect_files(backend, remote_roots)
        total = len(all_files)

        # Persist the latest discovery snapshot in the DB
        set_meta(self.db_path, "total_files", str(total))

        logger.info("Found %d files to process (saved to DB meta).", total)

        for file_path in all_files:   
            try:
                size, mtime = backend.stat(file_path)
                if size == 0:
                    continue  # skip empty files

                db_info = get_file_info_from_db(self.db_path, file_path)
                if db_info:
                    db_hash, db_size, db_mtime = db_info
                    if db_size == size and db_mtime == mtime:
                        continue  # already relevant hash in DB — skip

                digest, err = hash_file(backend, file_path, "sha256")
                if err is not None:
                    # If this looks like a connection drop — raise an exception and reconnect
                    possible_exc = self._string_to_exception(err)
                    if self._is_connection_error(possible_exc):
                        raise possible_exc
                    # Otherwise — just skip the file
                    continue

                save_hashes_to_db([(file_path, digest, size, mtime)], self.db_path)

            except FileNotFoundError:
                delete_file_from_db([file_path], self.db_path)
            except Exception as e:
                # If the connection drops during the run — we’ll restore it for an external retry
                if self._is_connection_error(e):
                    raise
                # Any other errors with the file — skip the file
                continue

    def _collect_files(self, backend: FileBackend, roots: Iterable[str]) -> List[str]:
        files: List[str] = []
        for root in roots:
            # backend.list_files recursively lists all files under root
            files.extend(list(backend.list_files(root)))
        return files

    # ---------- Utilities/hooks for checks and timings ----------

    def _is_connection_error(self, exc: BaseException) -> bool:
        return isinstance(exc, (OSError, socket.error, SSHException, NoValidConnectionsError))

    def _string_to_exception(self, msg: str) -> Exception:
        # Converting a string error description (from hash_file) into an Exception for uniform checking
        return OSError(msg)

    def _sleep_retry(self) -> None:
        # Sleep between reconnection attempts
        self.sleep(self.retry_sleep_s)

    def _sleep_after_pass(self) -> None:
        # Sleep after a SUCCESSFUL pass
        self.sleep(self.sleep_after_pass_s)
        
        
def main() -> None:
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    parser = argparse.ArgumentParser(
        description="Hash remote files over SFTP via FileBackend with resilient retries."
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single pass and exit (useful for tests/cron).",
    )
    args = parser.parse_args()

    config = Config(args.config)
    service = FileHashingService(config)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.get("LOG_PATH", "file_hashing_service.log")),
            logging.StreamHandler()
        ]
    )

    if args.once:
        service.run_once()
    else:
        service.run_forever()

if __name__ == "__main__":
    main()
