import argparse
from pathlib import Path

from . import ci_agent, dev_assistant, ops_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified agents CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dev_parser = subparsers.add_parser("dev", help="Run dev assistant")
    dev_parser.add_argument("--report-dir", default=dev_assistant.REPORT_DIR)
    dev_parser.add_argument("--error-log")
    dev_parser.add_argument("--scaffold-name")
    dev_parser.add_argument("--update-init", action="store_true")

    ci_parser = subparsers.add_parser("ci", help="Run CI agent")
    ci_parser.add_argument("--report-dir", default=ci_agent.REPORT_DIR)

    ops_parser = subparsers.add_parser("ops", help="Run ops agent")
    ops_parser.add_argument("--log", required=True)
    ops_parser.add_argument("--since", type=int)
    ops_parser.add_argument("--report-dir", default=ops_agent.REPORT_DIR)
    ops_parser.add_argument("--execute", action="store_true")
    ops_parser.add_argument("--health-url")
    ops_parser.add_argument("--execute-action", choices=sorted(ops_agent.SAFE_ACTIONS.keys()))
    ops_parser.add_argument("--approval-token")

    args = parser.parse_args()

    if args.command == "dev":
        args.report_dir = Path(args.report_dir)
        return dev_assistant.run(args)
    if args.command == "ci":
        args.report_dir = Path(args.report_dir)
        return ci_agent.run(args)
    if args.command == "ops":
        args.report_dir = Path(args.report_dir)
        return ops_agent.run(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
