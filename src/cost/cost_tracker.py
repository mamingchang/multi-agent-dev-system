"""
成本追踪器 - 标准化接口

提供与cost_analyzer.py相同的功能
"""

from src.cost.cost_analyzer import CostAnalyzer as CostTracker
from src.cost.cost_analyzer import CostAnalyzer as CostOptimizer

__all__ = ['CostTracker', 'CostOptimizer']
