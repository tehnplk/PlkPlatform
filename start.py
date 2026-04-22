import sys

from Main_logic import main


def handle_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
    print(f"[Unhandled Exception] {exc_type.__name__}: {exc_value}", file=sys.stderr)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_uncaught_exception


if __name__ == "__main__":
    main()
