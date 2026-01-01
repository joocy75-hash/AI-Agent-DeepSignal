"""
전략 모듈

사용 가능한 전략:
1. eth_ai_fusion - ETH AI/ML 융합 전략
"""

from .eth_ai_fusion_strategy import ETHAIFusionStrategy, create_eth_ai_fusion_strategy

__all__ = [
    "ETHAIFusionStrategy",
    "create_eth_ai_fusion_strategy",
]

# 전략 코드 목록
STRATEGY_CODES = [
    "eth_ai_fusion",
]
