"""
Configuration management for AI Bot Traffic Analyzer.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from pathlib import Path


@dataclass
class BotPattern:
    """Configuration for a bot detection pattern."""
    name: str
    display_name: str
    patterns: List[str]
    category: str = "AI Bot"
    color: str = "#667eea"


# Default bot detection patterns
DEFAULT_BOT_PATTERNS: List[BotPattern] = [
    BotPattern(
        name="chatgpt",
        display_name="ChatGPT/OpenAI",
        patterns=["GPTBot", "ChatGPT-User", "ChatGPT", "OpenAI"],
        category="AI Assistant",
        color="#10a37f"
    ),
    BotPattern(
        name="perplexity",
        display_name="Perplexity",
        patterns=["PerplexityBot", "Perplexity"],
        category="AI Search",
        color="#20b2aa"
    ),
    BotPattern(
        name="gemini",
        display_name="Bard/Gemini",
        patterns=["Google-Extended", "GoogleOther", "Bard", "Gemini"],
        category="AI Assistant",
        color="#4285f4"
    ),
    BotPattern(
        name="claude",
        display_name="Claude/Anthropic",
        patterns=["ClaudeBot", "Claude-Web", "anthropic-ai", "Anthropic"],
        category="AI Assistant",
        color="#cc785c"
    ),
    BotPattern(
        name="other_ai",
        display_name="Other AI Bots",
        patterns=["Applebot-Extended", "YouBot", "AI2Bot", "CCBot", "cohere-ai"],
        category="Other AI",
        color="#8b5cf6"
    ),
]


# Known bot IP ranges (for optional IP-based detection)
KNOWN_BOT_IP_RANGES: Dict[str, List[str]] = {
    "Googlebot": [
        "66.249.64.0/19",
        "64.233.160.0/19",
        "72.14.192.0/18",
        "209.85.128.0/17",
    ],
    "Bingbot": [
        "157.55.39.0/24",
        "207.46.13.0/24",
        "40.77.167.0/24",
    ],
    "OpenAI": [
        "20.171.207.0/24",  # Example - verify current ranges
    ],
}


@dataclass
class FeatureToggles:
    """Feature toggles for optional functionality."""
    enable_referrer_analysis: bool = True
    enable_site_structure: bool = True
    enable_crawl_efficiency: bool = True
    enable_compliance_tracking: bool = True
    enable_query_params: bool = True
    enable_anomaly_detection: bool = True
    enable_bot_versions: bool = True
    enable_seo_health: bool = True
    enable_competitive_analysis: bool = True
    enable_geographic_analysis: bool = False  # Requires geoip2


@dataclass
class Config:
    """Main configuration class for the analyzer."""

    # Bot detection patterns (as dict for easy lookup)
    bot_patterns: Dict[str, List[str]] = field(default_factory=dict)

    # Feature toggles
    features: FeatureToggles = field(default_factory=FeatureToggles)

    # Success status codes
    success_codes: List[int] = field(default_factory=lambda: list(range(200, 300)))

    # Redirect codes (can optionally be treated as success)
    redirect_codes: List[int] = field(default_factory=lambda: [301, 302, 303, 307, 308])

    # Client error codes
    client_error_codes: List[int] = field(default_factory=lambda: list(range(400, 500)))

    # Server error codes
    server_error_codes: List[int] = field(default_factory=lambda: list(range(500, 600)))

    # Analysis options
    ignore_homepage_redirects: bool = False
    homepage_paths: List[str] = field(default_factory=lambda: ["/", "/index.html", "/index.php"])

    # Health thresholds
    health_good_threshold: float = 80.0
    health_warning_threshold: float = 60.0

    # Report settings
    top_urls_count: int = 10
    top_failed_urls_count: int = 10

    # Output paths
    output_dir: Path = field(default_factory=lambda: Path.home() / "ai-bot-analyzer" / "output")
    reports_dir: Path = field(default_factory=lambda: Path.home() / "ai-bot-analyzer" / "output" / "reports")
    logs_dir: Path = field(default_factory=lambda: Path.home() / "ai-bot-analyzer" / "output" / "logs")

    def __post_init__(self):
        """Initialize bot patterns and ensure output directories exist."""
        if not self.bot_patterns:
            self.bot_patterns = self._load_bot_patterns()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _load_bot_patterns(self) -> Dict[str, List[str]]:
        """Load default bot patterns."""
        return {bp.display_name: bp.patterns for bp in DEFAULT_BOT_PATTERNS}

    def get_bot_patterns(self) -> Dict[str, List[str]]:
        """Get bot patterns dictionary."""
        return self.bot_patterns

    def is_success(self, status_code: int, url: str = "") -> bool:
        """Check if a status code represents success."""
        if status_code in self.success_codes:
            return True

        if self.ignore_homepage_redirects:
            if status_code in self.redirect_codes and url in self.homepage_paths:
                return True

        return False

    def get_status_category(self, status_code: int) -> str:
        """Get the category for a status code."""
        if status_code in self.success_codes:
            return "success"
        elif status_code in self.redirect_codes:
            return "redirect"
        elif status_code in self.client_error_codes:
            return "client_error"
        elif status_code in self.server_error_codes:
            return "server_error"
        else:
            return "unknown"

    def get_health_status(self, success_rate: float) -> str:
        """Get health status based on success rate."""
        if success_rate >= self.health_good_threshold:
            return "good"
        elif success_rate >= self.health_warning_threshold:
            return "warning"
        else:
            return "critical"

    def get_health_color(self, success_rate: float) -> str:
        """Get color for health status."""
        status = self.get_health_status(success_rate)
        colors = {
            "good": "#22c55e",
            "warning": "#eab308",
            "critical": "#ef4444"
        }
        return colors.get(status, "#6b7280")

    def get(self, key, default=None):
        """Get a config value by key."""
        return getattr(self, key, default)


# Singleton instance
_config = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
