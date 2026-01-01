from tools.agents import dev_assistant


def test_scan_strategies_returns_issues():
    issues = dev_assistant.scan_strategies()
    assert isinstance(issues, list)
    assert all(hasattr(issue, "severity") for issue in issues)
