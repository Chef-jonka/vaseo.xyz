"""
Bot Detection Module

Identifies AI bots by user-agent string patterns.
"""

import re
from dataclasses import dataclass
from typing import Optional, Dict, List
from .config import get_config


@dataclass
class BotInfo:
    """Information about a detected bot."""
    name: str
    category: str
    matched_pattern: str
    user_agent: str


class BotDetector:
    """Detects AI bots from user-agent strings."""

    def __init__(self, config=None):
        """Initialize with configuration."""
        self.config = config or get_config()
        self.bot_patterns = self.config.get_bot_patterns()
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance."""
        for bot_type, patterns in self.bot_patterns.items():
            self._compiled_patterns[bot_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def identify(self, user_agent: str) -> Optional[str]:
        """
        Identify the bot type from a user-agent string.

        Args:
            user_agent: The user-agent string to check

        Returns:
            Bot type name if matched, None otherwise
        """
        if not user_agent:
            return None

        for bot_type, compiled in self._compiled_patterns.items():
            for pattern in compiled:
                if pattern.search(user_agent):
                    return bot_type

        return None

    def identify_with_info(self, user_agent: str) -> Optional[BotInfo]:
        """
        Identify bot and return detailed information.

        Args:
            user_agent: The user-agent string to check

        Returns:
            BotInfo object if matched, None otherwise
        """
        if not user_agent:
            return None

        for bot_type, patterns in self.bot_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_agent, re.IGNORECASE):
                    return BotInfo(
                        name=bot_type,
                        category=self._get_category(bot_type),
                        matched_pattern=pattern,
                        user_agent=user_agent
                    )

        return None

    def _get_category(self, bot_type: str) -> str:
        """Get the category for a bot type."""
        categories = {
            'ChatGPT/OpenAI': 'AI Assistant',
            'Perplexity': 'AI Search',
            'Bard/Gemini': 'AI Assistant',
            'Claude/Anthropic': 'AI Assistant',
            'Other AI Bots': 'Other AI'
        }
        return categories.get(bot_type, 'Unknown')

    def is_bot(self, user_agent: str) -> bool:
        """
        Check if a user-agent is an AI bot.

        Args:
            user_agent: The user-agent string to check

        Returns:
            True if the user-agent matches a known bot pattern
        """
        return self.identify(user_agent) is not None

    def get_all_patterns(self) -> Dict[str, List[str]]:
        """Get all configured bot patterns."""
        return self.bot_patterns.copy()

    def add_pattern(self, bot_type: str, pattern: str):
        """
        Add a new detection pattern.

        Args:
            bot_type: The bot type to add pattern for
            pattern: The regex pattern to match
        """
        if bot_type not in self.bot_patterns:
            self.bot_patterns[bot_type] = []

        self.bot_patterns[bot_type].append(pattern)
        self._compiled_patterns[bot_type] = [
            re.compile(p, re.IGNORECASE) for p in self.bot_patterns[bot_type]
        ]
