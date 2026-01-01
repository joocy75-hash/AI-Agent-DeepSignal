# dev_assistant_report

Generated: 20251231_225046

## Issues
- [low] Strategy emits actions without order idempotency hint (backend/src/strategies/adaptive_market_regime_fighter.py: action signals present)
  - Suggestion: Ensure downstream executor uses idempotency keys or order-state checks.
- [high] Missing risk controls in strategy output (backend/src/strategies/ai_autonomous_adaptive_strategy.py: no risk keys in dict literals)
  - Suggestion: Add stop_loss/take_profit or trailing/liq fields in signal output.
- [high] Strategy dynamic check failed (backend/src/strategies/ai_autonomous_adaptive_strategy.py: No generate_signal entrypoint found)
  - Suggestion: Fix runtime errors or ensure generate_signal is callable.
- [high] Missing risk controls in strategy output (backend/src/strategies/ai_integrated_smart_strategy.py: no risk keys in dict literals)
  - Suggestion: Add stop_loss/take_profit or trailing/liq fields in signal output.
- [low] Strategy emits actions without order idempotency hint (backend/src/strategies/ai_integrated_smart_strategy.py: action signals present)
  - Suggestion: Ensure downstream executor uses idempotency keys or order-state checks.
- [high] Strategy dynamic check failed (backend/src/strategies/ai_integrated_smart_strategy.py: Dynamic check failed: No module named 'ccxt')
  - Suggestion: Fix runtime errors or ensure generate_signal is callable.
- [high] Missing risk controls in strategy output (backend/src/strategies/autonomous_30pct_strategy.py: no risk keys in dict literals)
  - Suggestion: Add stop_loss/take_profit or trailing/liq fields in signal output.
- [high] Strategy dynamic check failed (backend/src/strategies/autonomous_30pct_strategy.py: Dynamic check failed: No module named 'src')
  - Suggestion: Fix runtime errors or ensure generate_signal is callable.
- [low] Strategy emits actions without order idempotency hint (backend/src/strategies/dynamic_strategy_executor.py: action signals present)
  - Suggestion: Ensure downstream executor uses idempotency keys or order-state checks.
- [high] Strategy dynamic check failed (backend/src/strategies/dynamic_strategy_executor.py: Dynamic check failed: DynamicStrategyExecutor.__init__() missing 2 required positional arguments: 'strategy_code' and 'params')
  - Suggestion: Fix runtime errors or ensure generate_signal is callable.
- [high] Missing risk controls in strategy output (backend/src/strategies/eth_ai_autonomous_40pct_strategy.py: no risk keys in dict literals)
  - Suggestion: Add stop_loss/take_profit or trailing/liq fields in signal output.
- [high] Strategy dynamic check failed (backend/src/strategies/eth_ai_autonomous_40pct_strategy.py: Dynamic check failed: No module named 'src')
  - Suggestion: Fix runtime errors or ensure generate_signal is callable.
- [medium] Position sizing without leverage/margin guard (backend/src/strategies/proven_conservative_strategy.py: risk keys at line 102, size key at line 102, risk keys at line 224, size key at line 224, risk keys at line 201, size key at line 201, risk keys at line 212, size key at line 212, risk keys at line 161, size key at line 161, risk keys at line 183, size key at line 183)
  - Suggestion: Validate size vs leverage/margin and cap by risk settings.
- [low] Strategy emits actions without order idempotency hint (backend/src/strategies/proven_conservative_strategy.py: action signals present)
  - Suggestion: Ensure downstream executor uses idempotency keys or order-state checks.
- [high] Missing risk controls in strategy output (backend/src/strategies/sol_volatility_regime_15m_strategy.py: no risk keys in dict literals)
  - Suggestion: Add stop_loss/take_profit or trailing/liq fields in signal output.
- [high] Strategy dynamic check failed (backend/src/strategies/sol_volatility_regime_15m_strategy.py: Dynamic check failed: No module named 'src')
  - Suggestion: Fix runtime errors or ensure generate_signal is callable.