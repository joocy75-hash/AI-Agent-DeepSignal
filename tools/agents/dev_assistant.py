import argparse
import ast
import importlib.util
import json
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_DIR = REPO_ROOT / "backend" / "src" / "strategies"
REPORT_DIR = REPO_ROOT / "tools" / "agents" / "reports"


@dataclass
class Issue:
    severity: str
    title: str
    evidence: str
    suggestion: str


def _read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _strategy_files() -> List[Path]:
    return sorted(p for p in STRATEGY_DIR.glob("*.py") if p.name != "__init__.py")


def _analyze_strategy_ast(path: Path) -> Tuple[bool, bool, bool, List[str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False, False, False, [f"syntax error in {path.name}"]
    risk_keys = {"stop_loss", "take_profit", "trailing", "liquidation"}
    size_keys = {"size"}
    leverage_keys = {"leverage", "margin", "position_size"}
    risk_found = False
    size_found = False
    leverage_found = False
    evidence: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = []
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.append(key.value)
            if any(k in risk_keys for k in keys):
                risk_found = True
                evidence.append(f"risk keys at line {getattr(node, 'lineno', '?')}")
            if any(k in size_keys for k in keys):
                size_found = True
                evidence.append(f"size key at line {getattr(node, 'lineno', '?')}")
            if any(k in leverage_keys for k in keys):
                leverage_found = True
                evidence.append(f"leverage/margin key at line {getattr(node, 'lineno', '?')}")

    return risk_found, size_found, leverage_found, evidence


def _dynamic_strategy_check(path: Path) -> Optional[str]:
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            return "Unable to load module"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        candles = []
        for i in range(30):
            price = 100 + i * 0.1
            candles.append(
                {
                    "open": price,
                    "high": price + 1,
                    "low": price - 1,
                    "close": price + 0.5,
                    "volume": 100 + i,
                }
            )
        if hasattr(module, "generate_signal"):
            module.generate_signal(105.0, candles, {}, None)
            return None
        for attr in dir(module):
            value = getattr(module, attr)
            if hasattr(value, "generate_signal"):
                value().generate_signal(105.0, candles, None)
                return None
        return "No generate_signal entrypoint found"
    except Exception as exc:
        return f"Dynamic check failed: {exc}"


def scan_strategies() -> List[Issue]:
    issues: List[Issue] = []
    for path in _strategy_files():
        lines = _read_lines(path)
        content = "\n".join(lines)
        risk_found, size_found, leverage_found, ast_evidence = _analyze_strategy_ast(path)
        if not risk_found:
            issues.append(
                Issue(
                    severity="high",
                    title="Missing risk controls in strategy output",
                    evidence=f"{path.relative_to(REPO_ROOT)}: no risk keys in dict literals",
                    suggestion="Add stop_loss/take_profit or trailing/liq fields in signal output.",
                )
            )

        if size_found and not leverage_found:
            issues.append(
                Issue(
                    severity="medium",
                    title="Position sizing without leverage/margin guard",
                    evidence=f"{path.relative_to(REPO_ROOT)}: {', '.join(ast_evidence) if ast_evidence else 'size key found'}",
                    suggestion="Validate size vs leverage/margin and cap by risk settings.",
                )
            )

        if "action" in content and "order" not in content:
            issues.append(
                Issue(
                    severity="low",
                    title="Strategy emits actions without order idempotency hint",
                    evidence=f"{path.relative_to(REPO_ROOT)}: action signals present",
                    suggestion="Ensure downstream executor uses idempotency keys or order-state checks.",
                )
            )

        dynamic_error = _dynamic_strategy_check(path)
        if dynamic_error:
            issues.append(
                Issue(
                    severity="high",
                    title="Strategy dynamic check failed",
                    evidence=f"{path.relative_to(REPO_ROOT)}: {dynamic_error}",
                    suggestion="Fix runtime errors or ensure generate_signal is callable.",
                )
            )

    service_dir = REPO_ROOT / "backend" / "src" / "services"
    service_files = list(service_dir.glob("*.py"))
    service_text = "\n".join(p.read_text(encoding="utf-8") for p in service_files)
    if "idempot" not in service_text and "dedup" not in service_text:
        issues.append(
            Issue(
                severity="medium",
                title="No idempotency or deduplication markers detected in services",
                evidence=f"{service_dir.relative_to(REPO_ROOT)}: missing idempotency keywords",
                suggestion="Add idempotency keys or order-state checks in trade executor.",
            )
        )

    timeout_found = False
    for path in service_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "timeout":
                        timeout_found = True
                        break
    if not any(token in service_text for token in ["rate_limit", "circuit"]) and not timeout_found:
        issues.append(
            Issue(
                severity="medium",
                title="No rate limit/timeout/circuit breaker markers detected",
                evidence=f"{service_dir.relative_to(REPO_ROOT)}: missing timeout/rate_limit/circuit keywords",
                suggestion="Add explicit timeouts and circuit breaker patterns in exchange services.",
            )
        )

    return issues


def scaffold_strategy(name: str, update_init: bool) -> Path:
    snake = re.sub(r"[^a-zA-Z0-9_]+", "_", name).lower()
    filename = f"{snake}_strategy.py"
    target = STRATEGY_DIR / filename
    if target.exists():
        raise FileExistsError(f"{target} already exists")

    class_name = f"{name.replace('_', '').title()}Strategy"
    template = textwrap.dedent(
        f"""\n        \"\"\"\n        {name} Strategy Template\n        \"\"\"\n        from typing import Dict, List, Optional\n\n\n        def generate_signal(\n            current_price: float,\n            candles: List[Dict],\n            params: Optional[Dict] = None,\n            current_position: Optional[Dict] = None,\n        ) -> Dict:\n            params = params or {{}}\n            default_response = {{\n                \"action\": \"hold\",\n                \"confidence\": 0.5,\n                \"reason\": \"Template strategy\",\n                \"stop_loss\": None,\n                \"take_profit\": None,\n                \"size\": params.get(\"size\", 0.001),\n                \"strategy_type\": \"{snake}\",\n            }}\n\n            if not candles:\n                default_response[\"reason\"] = \"No candles provided\"\n                return default_response\n\n            # TODO: Implement entry/exit logic\n            return default_response\n\n\n        class {class_name}:\n            def __init__(self, params: Optional[Dict] = None):\n                self.params = params or {{}}\n\n            def generate_signal(\n                self,\n                current_price: float,\n                candles: List[Dict],\n                current_position: Optional[Dict] = None,\n            ) -> Dict:\n                return generate_signal(current_price, candles, self.params, current_position)\n        """
    ).lstrip()

    target.write_text(template, encoding="utf-8")

    if update_init:
        init_path = STRATEGY_DIR / "__init__.py"
        init_text = init_path.read_text(encoding="utf-8")
        code_entry = f'    "{snake}",\n'
        if code_entry not in init_text:
            init_text = init_text.replace(
                "STRATEGY_CODES = [\n",
                "STRATEGY_CODES = [\n" + code_entry,
            )
            init_path.write_text(init_text, encoding="utf-8")

    return target


def bug_repro_template(log_path: Path, output_dir: Path) -> Path:
    lines = log_path.read_text(encoding="utf-8").splitlines()
    tail = lines[-200:]
    error_line = next(
        (line for line in reversed(tail) if "ERROR" in line or "Exception" in line),
        "",
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"bug_repro_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.py"
    template = textwrap.dedent(
        f"""
        \"\"\"Bug reproduction scaffold\"\"\"

        def reproduce():
            # TODO: Paste failing inputs / environment setup
            # Source hint: {error_line}
            raise NotImplementedError(\"Fill in reproduction steps\")


        if __name__ == \"__main__\":
            reproduce()
        """
    ).lstrip()
    target.write_text(template, encoding="utf-8")
    return target


def write_report(issues: List[Issue], report_dir: Path, title: str) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = report_dir / f"{title}_{timestamp}.json"
    payload = {
        "generated_at": timestamp,
        "issues": [issue.__dict__ for issue in issues],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path = report_dir / f"{title}_{timestamp}.md"
    lines = [f"# {title}", "", f"Generated: {timestamp}", "", "## Issues"]
    for issue in issues:
        lines.append(f"- [{issue.severity}] {issue.title} ({issue.evidence})")
        lines.append(f"  - Suggestion: {issue.suggestion}")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path


def run(args: argparse.Namespace) -> int:
    issues = scan_strategies()
    report_path = write_report(issues, args.report_dir, "dev_assistant_report")

    repro_path = None
    if args.error_log:
        repro_path = bug_repro_template(Path(args.error_log), args.report_dir)

    if args.scaffold_name:
        scaffold_path = scaffold_strategy(args.scaffold_name, args.update_init)
        issues.append(
            Issue(
                severity="info",
                title="Strategy scaffold created",
                evidence=str(scaffold_path.relative_to(REPO_ROOT)),
                suggestion="Fill in signal logic and tests.",
            )
        )
        report_path = write_report(issues, args.report_dir, "dev_assistant_report")

    print(f"Dev assistant report: {report_path}")
    if repro_path:
        print(f"Bug repro scaffold: {repro_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dev assistant for strategy scaffolding and checks"
    )
    parser.add_argument("--report-dir", default=str(REPORT_DIR), help="Report output directory")
    parser.add_argument("--error-log", help="Path to recent error log for repro template")
    parser.add_argument("--scaffold-name", help="Create strategy scaffold with name")
    parser.add_argument("--update-init", action="store_true", help="Update strategies/__init__.py")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.report_dir = Path(args.report_dir)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
