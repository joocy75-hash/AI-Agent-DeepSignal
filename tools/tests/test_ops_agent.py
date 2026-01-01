from tools.agents import ops_agent


def test_classify_lines_counts_patterns():
    lines = [
        "ERROR timeout while fetching",
        "WARNING rate limit exceeded 429",
        "ERROR websocket disconnected",
    ]
    counts = ops_agent.classify_lines(lines)
    assert counts["network_timeout"] >= 1
    assert counts["rate_limit"] >= 1
    assert counts["data_delay_ws"] >= 1
