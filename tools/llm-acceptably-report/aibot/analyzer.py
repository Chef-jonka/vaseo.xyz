"""
AI Bot Traffic Analyzer - Main Engine

Core analysis engine for processing web server logs and generating reports.
"""

from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from .config import get_config, Config
from .parsers import LogParser
from .detectors import BotDetector
from .insights import InsightsEngine


class AIBotAnalyzer:
    """
    Main analyzer class for processing web server logs.

    Identifies AI bot traffic and generates comprehensive reports.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize analyzer with configuration."""
        self.config = config or get_config()
        self.parser = LogParser()
        self.detector = BotDetector(self.config)
        self.insights = InsightsEngine(self.config)
        self.reset()

    def reset(self):
        """Reset all counters and data structures."""
        self.total_requests = 0
        self.bot_requests: Dict[str, int] = defaultdict(int)
        self.bot_successes: Dict[str, int] = defaultdict(int)
        self.url_requests: Counter = Counter()
        self.url_failures: Counter = Counter()
        self.status_codes: Counter = Counter()
        self.bot_status_codes: Dict[str, Counter] = defaultdict(Counter)
        self.date_range: Dict[str, Any] = {'min': None, 'max': None}
        self.hourly_traffic: Dict[int, int] = defaultdict(int)
        self.daily_traffic: Dict[str, int] = defaultdict(int)
        self.hourly_by_bot: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.bot_sessions: Dict[str, List] = defaultdict(list)
        self.bot_url_preferences: Dict[str, Counter] = defaultdict(Counter)
        self.failure_details: List[Dict] = []
        self.url_failure_types: Dict[str, Counter] = defaultdict(Counter)
        self.bot_failure_types: Dict[str, Counter] = defaultdict(Counter)

    def analyze_file(
        self,
        log_file: str,
        ignore_homepage_redirects: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a log file for AI bot traffic.

        Args:
            log_file: Path to the log file
            ignore_homepage_redirects: Treat homepage redirects as success
            progress_callback: Optional callback for progress updates

        Returns:
            Analysis report as dictionary
        """
        log_path = Path(log_file)
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")

        print(f"Analyzing log file: {log_file}")

        # Track sessions by IP
        ip_sessions: Dict[str, List] = defaultdict(list)

        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                parsed = self.parser.parse(line.strip())
                if not parsed:
                    continue

                # Check if it's a bot
                bot_type = self.detector.identify(parsed['user_agent'])
                if not bot_type:
                    continue

                # Update date range
                ts = parsed['timestamp']
                if self.date_range['min'] is None or ts < self.date_range['min']:
                    self.date_range['min'] = ts
                if self.date_range['max'] is None or ts > self.date_range['max']:
                    self.date_range['max'] = ts

                # Time patterns
                hour_key = ts.hour
                day_key = ts.strftime('%A')

                self.hourly_traffic[hour_key] += 1
                self.daily_traffic[day_key] += 1
                self.hourly_by_bot[bot_type][hour_key] += 1

                # Session tracking
                ip_sessions[parsed['ip']].append({
                    'timestamp': ts,
                    'url': parsed['url'],
                    'bot_type': bot_type,
                    'status': parsed['status']
                })
                self.bot_url_preferences[bot_type][parsed['url']] += 1

                # Count requests
                self.total_requests += 1
                self.bot_requests[bot_type] += 1
                self.url_requests[parsed['url']] += 1
                self.status_codes[parsed['status']] += 1
                self.bot_status_codes[bot_type][parsed['status']] += 1

                # Determine success
                is_success = self._is_success(parsed['status'])

                # Optionally treat homepage redirects as success
                if ignore_homepage_redirects and parsed['url'] == '/' and 300 <= parsed['status'] < 400:
                    is_success = True

                if is_success:
                    self.bot_successes[bot_type] += 1
                else:
                    self.url_failures[parsed['url']] += 1
                    failure_type = self._categorize_failure(parsed['status'])
                    self.failure_details.append({
                        'timestamp': ts,
                        'url': parsed['url'],
                        'status': parsed['status'],
                        'bot_type': bot_type,
                        'failure_type': failure_type,
                        'method': parsed['method']
                    })
                    self.url_failure_types[parsed['url']][failure_type] += 1
                    self.bot_failure_types[bot_type][failure_type] += 1

                # Progress callback
                if progress_callback and line_num % 1000 == 0:
                    progress_callback(line_num, self.total_requests)

        # Build sessions from IP tracking
        for ip, requests in ip_sessions.items():
            if len(requests) > 1:
                requests.sort(key=lambda x: x['timestamp'])
                bot_type = requests[0]['bot_type']
                self.bot_sessions[bot_type].append(requests)

        print(f"Analysis complete: {self.total_requests} AI bot requests found")

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate the analysis report from collected data."""
        if self.total_requests == 0:
            return {"error": "No AI bot requests found"}

        # Calculate overall success rate
        total_successes = sum(self.bot_successes.values())
        overall_success_rate = (total_successes / self.total_requests) * 100

        # Bot statistics
        bot_stats = []
        for bot_type in sorted(self.bot_requests.keys(), key=lambda x: self.bot_requests[x], reverse=True):
            count = self.bot_requests[bot_type]
            successes = self.bot_successes[bot_type]
            percentage = (count / self.total_requests) * 100
            success_rate = (successes / count * 100) if count > 0 else 0

            bot_stats.append({
                'type': bot_type,
                'count': count,
                'percentage': percentage,
                'success_rate': success_rate
            })

        # Top URLs
        top_urls = [{'url': url, 'count': count} for url, count in self.url_requests.most_common(10)]
        top_failed_urls = [{'url': url, 'count': count} for url, count in self.url_failures.most_common(10)]

        # Failure types
        failure_counts: Counter = Counter()
        for status, count in self.status_codes.items():
            if not self._is_success(status):
                failure_type = self._categorize_failure(status)
                failure_counts[failure_type] += count

        failure_types = [{'type': ft, 'count': count} for ft, count in failure_counts.most_common()]

        # Generate insights
        time_analysis = self.insights.analyze_time_patterns(
            dict(self.hourly_traffic),
            dict(self.daily_traffic),
            {k: dict(v) for k, v in self.hourly_by_bot.items()}
        )

        behavior_analysis = self.insights.analyze_bot_behavior(
            dict(self.bot_sessions),
            dict(self.bot_requests),
            dict(self.bot_successes),
            {k: Counter(v) for k, v in self.bot_url_preferences.items()}
        )

        failure_analysis = self.insights.analyze_failures(
            self.failure_details,
            {k: Counter(v) for k, v in self.url_failure_types.items()},
            self.total_requests
        )

        recommendations = self.insights.generate_recommendations(
            self.url_failures,
            {k: Counter(v) for k, v in self.url_failure_types.items()},
            dict(self.bot_requests),
            dict(self.bot_successes),
            self.url_requests,
            self.total_requests
        )

        comparisons = self.insights.generate_comparisons(
            dict(self.bot_requests),
            dict(self.bot_successes),
            self.url_requests,
            self.url_failures
        )

        return {
            'date_range': {
                'start': self.date_range['min'].strftime('%Y-%m-%d') if self.date_range['min'] else 'N/A',
                'end': self.date_range['max'].strftime('%Y-%m-%d') if self.date_range['max'] else 'N/A',
            },
            'total_requests': self.total_requests,
            'overall_success_rate': overall_success_rate,
            'bot_statistics': bot_stats,
            'top_urls': top_urls,
            'top_failed_urls': top_failed_urls,
            'failure_types': failure_types,
            'time_analysis': time_analysis,
            'behavior_analysis': behavior_analysis,
            'failure_analysis': failure_analysis,
            'recommendations': recommendations,
            'comparisons': comparisons
        }

    def _is_success(self, status_code: int) -> bool:
        """Check if status code indicates success (2xx)."""
        return 200 <= status_code < 300

    def _categorize_failure(self, status_code: int) -> str:
        """Categorize a failure status code."""
        if 300 <= status_code < 400:
            return "Redirect"
        elif status_code == 404:
            return "404 Not Found"
        elif status_code == 500:
            return "500 Server Error"
        elif status_code == 503:
            return "503 Service Unavailable"
        elif 400 <= status_code < 500:
            return f"{status_code} Client Error"
        elif 500 <= status_code < 600:
            return f"{status_code} Server Error"
        return f"Unknown ({status_code})"
