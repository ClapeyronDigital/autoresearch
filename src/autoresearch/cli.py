import argparse
import sys

from .init_cmd import run as init_run
from .check_cmd import run as check_run
from .analyze_cmd import run as analyze_run


def main():
    parser = argparse.ArgumentParser(
        prog="autoresearch",
        description="Framework for automated AI-driven research",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Scaffold a new autoresearch project")
    init_p.add_argument(
        "path", nargs="?", default=".", help="Target directory (default: current)"
    )

    check_p = sub.add_parser("check", help="Validate a project structure and contracts")
    check_p.add_argument(
        "path", nargs="?", default=".", help="Project directory (default: current)"
    )

    analyze_p = sub.add_parser("analyze", help="Generate progress chart for a session")
    analyze_p.add_argument(
        "path", nargs="?", default=".", help="Project directory (default: current)"
    )
    analyze_p.add_argument(
        "--session", required=True, help="Session name (e.g. may16)"
    )

    args = parser.parse_args()

    if args.command == "init":
        sys.exit(init_run(args.path))
    elif args.command == "check":
        sys.exit(check_run(args.path))
    elif args.command == "analyze":
        sys.exit(analyze_run(args.path, args.session))
