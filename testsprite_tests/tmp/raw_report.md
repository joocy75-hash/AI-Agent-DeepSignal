
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** auto-dashboard
- **Date:** 2025-12-13
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001
- **Test Name:** user authentication including oauth login and jwt token handling
- **Test Code:** [TC001_user_authentication_including_oauth_login_and_jwt_token_handling.py](./TC001_user_authentication_including_oauth_login_and_jwt_token_handling.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 3, in <module>
ModuleNotFoundError: No module named 'jwt'

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/6924cccd-ec7a-4687-aae2-9f0a4736643a
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002
- **Test Name:** dashboard portfolio and trading statistics display
- **Test Code:** [TC002_dashboard_portfolio_and_trading_statistics_display.py](./TC002_dashboard_portfolio_and_trading_statistics_display.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 149, in <module>
  File "<string>", line 100, in test_dashboard_portfolio_and_trading_statistics_display
  File "<string>", line 43, in get_jwt_token
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:8000/api/auth/login

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/d77ceee1-395c-423d-8c2b-66ae4a307be2
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003
- **Test Name:** bot management create start stop and monitor bots
- **Test Code:** [TC003_bot_management_create_start_stop_and_monitor_bots.py](./TC003_bot_management_create_start_stop_and_monitor_bots.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 87, in <module>
  File "<string>", line 36, in test_bot_management_create_start_stop_monitor
AssertionError: Bot creation failed: {'result': 'success'}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/b65c4437-c15d-4c7d-9cb3-ca22d74546d1
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004
- **Test Name:** grid bot templates application and backtesting
- **Test Code:** [TC004_grid_bot_templates_application_and_backtesting.py](./TC004_grid_bot_templates_application_and_backtesting.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 120, in <module>
  File "<string>", line 28, in test_grid_bot_templates_application_and_backtesting
AssertionError: Login failed: {"success":false,"error":{"code":"HTTP_ERROR","message":"Not Found","details":{},"timestamp":"2025-12-12T19:34:55.892531","request_id":null}}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/68f476c9-5f36-45a6-9513-8f79f3ba9b83
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005
- **Test Name:** admin grid template manager crud and backtesting
- **Test Code:** [TC005_admin_grid_template_manager_crud_and_backtesting.py](./TC005_admin_grid_template_manager_crud_and_backtesting.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 150, in <module>
  File "/var/lang/lib/python3.12/unittest/mock.py", line 1396, in patched
    return func(*newargs, **newkeywargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<string>", line 65, in test_admin_grid_template_manager_crud_and_backtesting
AssertionError

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/d7ded269-b73d-44f1-9617-acef9c5ac8b1
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006
- **Test Name:** backtesting engine with candle data and performance metrics
- **Test Code:** [TC006_backtesting_engine_with_candle_data_and_performance_metrics.py](./TC006_backtesting_engine_with_candle_data_and_performance_metrics.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 139, in <module>
  File "<string>", line 72, in test_backtesting_engine_with_candle_data_and_performance_metrics
AssertionError: Bot creation failed: {"success":false,"error":{"code":"HTTP_ERROR","message":"Not Found","details":{},"timestamp":"2025-12-12T19:35:53.785059","request_id":null}}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/e297c277-3c3c-4b73-b3be-badb9791d521
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007
- **Test Name:** real time trading interface with chart and position management
- **Test Code:** [TC007_real_time_trading_interface_with_chart_and_position_management.py](./TC007_real_time_trading_interface_with_chart_and_position_management.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 121, in <module>
  File "<string>", line 53, in test_real_time_trading_interface_with_chart_and_position_management
  File "/var/task/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://localhost:8000/api/auth/login

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/ce19d4a9-9020-4f9f-9574-8f365916e38e
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008
- **Test Name:** trading history accuracy and analytics
- **Test Code:** [TC008_trading_history_accuracy_and_analytics.py](./TC008_trading_history_accuracy_and_analytics.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 192, in <module>
  File "<string>", line 64, in test_trading_history_accuracy_and_analytics
AssertionError

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/b5d21b12-cc1e-4399-8906-d33a940491a2
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC009
- **Test Name:** strategy management configuration and alert triggering
- **Test Code:** [TC009_strategy_management_configuration_and_alert_triggering.py](./TC009_strategy_management_configuration_and_alert_triggering.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 139, in <module>
  File "<string>", line 69, in test_strategy_management_and_alert_triggering
AssertionError: Strategy creation failed: {"success":false,"error":{"code":"HTTP_ERROR","message":"Not Found","details":{},"timestamp":"2025-12-12T19:35:28.203871","request_id":null}}

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/20225095-f6c2-42f8-b2cc-1b75f49da271
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC010
- **Test Name:** user settings api key management and preferences
- **Test Code:** [TC010_user_settings_api_key_management_and_preferences.py](./TC010_user_settings_api_key_management_and_preferences.py)
- **Test Error:** Traceback (most recent call last):
  File "/var/task/handler.py", line 258, in run_with_retry
    exec(code, exec_env)
  File "<string>", line 92, in <module>
  File "<string>", line 39, in test_user_settings_api_key_management_and_preferences
  File "<string>", line 19, in create_user_and_get_token
AssertionError

- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/7907cc9c-a3f2-4224-b26e-c0b5513fc8cc/1c2044f9-7b1d-4437-8a9f-cfffba526acc
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **0.00** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---