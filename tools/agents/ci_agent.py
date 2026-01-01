import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = REPO_ROOT / "tools" / "agents" / "reports"


@dataclass
class FailureSummary:
    test_name: str
    reason: str


def run_command(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _run_optional(cmd: List[str], cwd: Path) -> tuple[str, int, str]:
    if shutil.which(cmd[0]) is None and cmd[0] != sys.executable:
        return "skipped", 0, f"{cmd[0]} not installed"
    result = run_command(cmd, cwd)
    status = "ok" if result.returncode == 0 else "failed"
    return status, result.returncode, result.stdout + result.stderr


def lint_check(report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = report_dir / f"lint_log_{timestamp}.txt"

    outputs = []
    compile_status, _, compile_output = _run_optional(
        [sys.executable, "-m", "compileall", "backend/src", "tools"], REPO_ROOT
    )
    outputs.append(("compileall", compile_status, compile_output))

    ruff_status, _, ruff_output = _run_optional(
        [sys.executable, "-m", "ruff", "check", "tools/agents", "tools/tests"],
        REPO_ROOT,
    )
    outputs.append(("ruff", ruff_status, ruff_output))

    black_status, _, black_output = _run_optional(
        [sys.executable, "-m", "black", "--check", "tools/agents", "tools/tests"],
        REPO_ROOT,
    )
    outputs.append(("black", black_status, black_output))

    log_contents = []
    for name, status, out in outputs:
        log_contents.append(f"## {name} [{status}]")
        log_contents.append(out.strip())
    log_path.write_text("\n\n".join(log_contents), encoding="utf-8")

    status = "ok" if all(item[1] in {"ok", "skipped"} for item in outputs) else "failed"
    summary = {
        "status": status,
        "command": "compileall + ruff + black",
        "log": str(log_path),
        "details": {name: state for name, state, _ in outputs},
    }
    report_path = report_dir / f"lint_report_{timestamp}.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return report_path


def run_tests(report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = report_dir / f"pytest_log_{timestamp}.txt"
    result = run_command([sys.executable, "-m", "pytest", "tools/tests"], REPO_ROOT)
    log_path.write_text(result.stdout + result.stderr, encoding="utf-8")

    summary = {
        "status": "ok" if result.returncode == 0 else "failed",
        "command": "python -m pytest tools/tests",
        "log": str(log_path),
    }
    report_path = report_dir / f"test_report_{timestamp}.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return report_path


def analyze_failures(log_text: str) -> List[FailureSummary]:
    failures = []
    for line in log_text.splitlines():
        if line.startswith("FAILED"):
            parts = line.split(" - ")
            test_name = parts[0].replace("FAILED ", "").strip()
            reason = parts[1].strip() if len(parts) > 1 else "Unknown"
            failures.append(FailureSummary(test_name=test_name, reason=reason))
    return failures


def suggest_causes(log_text: str) -> List[str]:
    patterns = [
        (r"ModuleNotFoundError|ImportError", "Missing dependency or incorrect import path"),
        (r"AssertionError", "Assertion mismatch: expected vs actual output"),
        (r"ConnectionRefusedError|TimeoutError", "External service unavailable or network timeout"),
    ]
    suggestions = []
    for pattern, suggestion in patterns:
        if re.search(pattern, log_text):
            suggestions.append(suggestion)
    while len(suggestions) < 3:
        suggestions.append("Review stack trace and isolate failing fixture or mock setup")
    return suggestions[:3]


def write_failure_report(log_path: Path, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    log_text = log_path.read_text(encoding="utf-8")
    failures = analyze_failures(log_text)
    suggestions = suggest_causes(log_text)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"failure_report_{timestamp}.md"
    lines = [
        "# CI Failure Analysis",
        "",
        "## Failed Tests",
    ]
    if failures:
        for failure in failures:
            lines.append(f"- {failure.test_name}: {failure.reason}")
    else:
        lines.append("- No FAILED lines detected")

    lines.extend(
        [
            "",
            "## Likely Causes",
        ]
    )
    for suggestion in suggestions:
        lines.append(f"- {suggestion}")

    lines.extend(
        [
            "",
            "## Immediate Fix Guidance",
            "- Re-run the failing test in isolation to capture full traceback.",
            "- Check recent diffs around the failing module and fixtures.",
            "- Verify environment variables or mocks used by the test.",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def run(args: argparse.Namespace) -> int:
    lint_report = lint_check(args.report_dir)
    test_report = run_tests(args.report_dir)
    failure_report = None

    test_log = Path(json.loads(Path(test_report).read_text(encoding="utf-8"))["log"])
    log_path = REPO_ROOT / test_log
    if log_path.exists():
        failure_report = write_failure_report(log_path, args.report_dir)

    summary_path = args.report_dir / f"ci_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    summary_lines = [
        "# CI Summary",
        f"- Lint report: {lint_report}",
        f"- Test report: {test_report}",
    ]
    if failure_report:
        summary_lines.append(f"- Failure report: {failure_report}")
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Lint report: {lint_report}")
    print(f"Test report: {test_report}")
    print(f"Summary report: {summary_path}")
    if failure_report:
        print(f"Failure report: {failure_report}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CI agent: lint, tests, failure analysis")
    parser.add_argument("--report-dir", default=str(REPORT_DIR), help="Report output directory")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.report_dir = Path(args.report_dir)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
