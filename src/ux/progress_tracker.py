"""
进度追踪器 - 标准化接口

提供与progress_estimator.py相同的功能
"""

from src.ux.progress_estimator import ProgressEstimator as ProgressTracker
from src.ux.template_manager import TemplateManager as NotificationManager

__all__ = ['ProgressTracker', 'NotificationManager']
