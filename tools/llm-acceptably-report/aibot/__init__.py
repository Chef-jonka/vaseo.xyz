"""
AI Bot Traffic Analyzer - Core Package

A professional tool for analyzing web server logs to detect and report on AI bot traffic.
"""

__version__ = "2.0.0"
__author__ = "AI Bot Analyzer Team"

from .config import Config, BotPattern, get_config
from .parsers import LogParser, LogEntry
from .detectors import BotDetector, BotInfo
from .insights import InsightsEngine
from .analyzer import AIBotAnalyzer

__all__ = [
    'Config',
    'BotPattern',
    'get_config',
    'LogParser',
    'LogEntry',
    'BotDetector',
    'BotInfo',
    'InsightsEngine',
    'AIBotAnalyzer',
]
