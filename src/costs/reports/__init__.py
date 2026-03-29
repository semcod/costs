"""Reporting package for AI cost tracker."""

# Re-exporting from submodules for backward compatibility 
from .base import get_cost_color
from .markdown import generate_markdown_report
from .html import generate_html_report
from .badge import update_readme_badge
from ..metrics import calculate_human_time

__all__ = [
    'calculate_human_time',
    'get_cost_color',
    'generate_markdown_report',
    'generate_html_report',
    'update_readme_badge'
]
