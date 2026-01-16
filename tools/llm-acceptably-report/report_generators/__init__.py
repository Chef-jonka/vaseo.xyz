"""
Report generators for AI Bot Traffic Analyzer.
"""

from .html_generator import generate_html_report
from .text_generator import TextReportGenerator

__all__ = [
    'generate_html_report',
    'TextReportGenerator',
]
