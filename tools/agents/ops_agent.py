import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from urllib import request as urlrequest
from urllib.error import URLError

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = REPO_ROOT / "tools" / "agents" / "reports"


@dataclass
class Classification:
    name: str
    patterns: List[str]
    actions: List[str]


CLASSIFICATIONS = [
    Classification(
        name="network_timeout",
        patterns=[r"timeout", r"ConnectionError", r"ConnectionRefused"],
        actions=[
            "Restart websocket client",
            "Backoff and retry requests",
            "Check upstream exchange status",
        ],
    ),
    Classification(
        name="auth_signature",
        patterns=[r"signature", r"invalid api key", r"auth", r"unauthorized"],
        actions=["Reload API keys", "Verify API key permissions", "Check server clock drift"],
    ),
    Classification(
        name="rate_limit",
        patterns=[r"429", r"rate limit", r"Too many requests"],
        actions=["Increase backoff", "Reduce request frequency", "Enable request batching"],
    ),
    Classification(
        name="order_rejected",
        patterns=[r"insufficient", r"margin", r"order rejected", r"position limit"],
        actions=[
            "Pause new orders",
            "Review leverage/position sizing",
            "Notify operator for approval",
        ],
    ),
    Classification(
        name="data_delay_ws",
        patterns=[r"websocket", r"ws", r"stale", r"lag"],
        actions=[
            "Reconnect websocket",
            "Restart market data collector",
            "Increase heartbeat monitoring",
        ],
    ),
]

SAFE_ACTIONS = {
    "validate_env": ["bash", "scripts/validate-env.sh"],
}


def load_log_lines(path: Path, since_minutes: int | None) -> List[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if since_minutes is None:
        return lines[-1000:]
    # naive: return last N lines for MVP
    return lines[-1000:]


def classify_lines(lines: List[str]) -> Dict[str, int]:
    counts = {c.name: 0 for c in CLASSIFICATIONS}
    for line in lines:
        lower = line.lower()
        for cls in CLASSIFICATIONS:
            if any(re.search(pat, lower, re.IGNORECASE) for pat in cls.patterns):
                counts[cls.name] += 1
    return counts


def top_messages(lines: List[str], level: str) -> List[str]:
    hits = [line for line in lines if level in line]
    return hits[-5:]


def fetch_health(health_url: str | None) -> Dict:
    if not health_url:
        return {}
    try:
        with urlrequest.urlopen(health_url, timeout=5) as response:
            body = response.read().decode("utf-8")
            return {"url": health_url, "status": response.status, "body": body[:1000]}
    except URLError as exc:
        return {"url": health_url, "error": str(exc)}


def _execute_action(action: str, approval_token: str | None) -> Tuple[str, str]:
    required_token = os.getenv("OPS_AGENT_APPROVAL_TOKEN")
    if not required_token or not approval_token or approval_token != required_token:
        return "blocked", "approval token missing or invalid"
    cmd = SAFE_ACTIONS.get(action)
    if not cmd:
        return "blocked", f"unknown action: {action}"
    result = subprocess.run(cmd, capture_output=True, text=True)
    status = "ok" if result.returncode == 0 else "failed"
    output = (result.stdout + result.stderr).strip()
    return status, output[:2000]


def build_report(lines: List[str], execute_mode: bool, health: Dict, action_result: Dict) -> Dict:
    counts = classify_lines(lines)
    suggestions = {cls.name: cls.actions for cls in CLASSIFICATIONS if counts.get(cls.name, 0) > 0}
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "error_top": top_messages(lines, "ERROR"),
            "warning_top": top_messages(lines, "WARNING"),
            "order_fail_top": top_messages(lines, "order"),
        },
        "classifications": counts,
        "suggested_actions": suggestions,
        "execute_mode": execute_mode,
        "action_result": action_result,
        "health_check": health,
        "guardrail": "This agent never places orders directly",
    }


def write_report(report: Dict, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"ops_report_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report_path


def run(args: argparse.Namespace) -> int:
    log_path = Path(args.log)
    lines = load_log_lines(log_path, args.since)

    execute_mode = bool(args.execute and os.getenv("OPS_AGENT_EXECUTE") == "true")
    health = fetch_health(args.health_url)
    action_result = {}
    if execute_mode and args.execute_action:
        status, output = _execute_action(args.execute_action, args.approval_token)
        action_result = {"action": args.execute_action, "status": status, "output": output}
    report = build_report(lines, execute_mode, health, action_result)
    report_path = write_report(report, args.report_dir)

    print(f"Ops report: {report_path}")
    if execute_mode:
        print("Execute mode enabled, only safe actions are allowed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ops agent: log triage and safe action suggestions"
    )
    parser.add_argument("--log", required=True, help="Path to log file")
    parser.add_argument("--since", type=int, help="Minutes lookback (approx)")
    parser.add_argument("--report-dir", default=str(REPORT_DIR), help="Report output directory")
    parser.add_argument("--health-url", help="Optional health endpoint URL")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Enable execute mode (requires OPS_AGENT_EXECUTE=true)",
    )
    parser.add_argument("--execute-action", choices=sorted(SAFE_ACTIONS.keys()))
    parser.add_argument("--approval-token", help="Approval token for execute mode")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.report_dir = Path(args.report_dir)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
