from pathlib import Path
from .storage import JsonStore
from .repositories import Repos
from .services import AccountingService
from .cli import run_cli


def main() -> None:
    base = Path(__file__).resolve().parent.parent / "data"
    store = JsonStore(base)
    repos = Repos(store)
    svc = AccountingService(repos)
    run_cli(svc)


if __name__ == "__main__":
    main()