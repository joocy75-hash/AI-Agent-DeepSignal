from tools.agents import ci_agent


def test_analyze_failures_parses_failed_lines():
    sample = """FAILED tests/test_sample.py::test_one - AssertionError: boom\n"""
    failures = ci_agent.analyze_failures(sample)
    assert len(failures) == 1
    assert failures[0].test_name == "tests/test_sample.py::test_one"


def test_suggest_causes_returns_three():
    sample = "ModuleNotFoundError: missing" "\nAssertionError: bad" "\nTimeoutError: slow"
    suggestions = ci_agent.suggest_causes(sample)
    assert len(suggestions) == 3
