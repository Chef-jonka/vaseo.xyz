"""
AI Bot Traffic Analyzer - Main Engine

Core analysis engine for processing web server logs and generating reports.
"""

from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import urlparse, parse_qs
import re

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
        self.total_all_requests = 0  # All requests including human
        self.human_requests = 0  # Non-bot requests
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
        # New metrics
        self.total_bytes: int = 0  # Bandwidth tracking
        self.bot_bytes: Dict[str, int] = defaultdict(int)
        self.request_methods: Counter = Counter()  # GET, POST, HEAD, etc.
        self.content_types: Counter = Counter()  # HTML, images, CSS, JS
        self.status_code_groups: Dict[str, int] = {'2xx': 0, '3xx': 0, '4xx': 0, '5xx': 0}

        # NEW: Referrer tracking
        self.referrer_sources: Counter = Counter()  # direct/search/external
        self.referrer_domains: Counter = Counter()
        self.bot_referrer_sources: Dict[str, Counter] = defaultdict(Counter)

        # NEW: Site structure
        self.section_hits: Counter = Counter()  # /blog/, /products/
        self.crawl_depth: Counter = Counter()  # 0, 1, 2, 3+
        self.bot_section_preferences: Dict[str, Counter] = defaultdict(Counter)

        # NEW: Compliance tracking
        self.robots_txt_accesses: Dict[str, int] = defaultdict(int)
        self.sitemap_accesses: Dict[str, int] = defaultdict(int)

        # NEW: Query params
        self.url_params: Counter = Counter()
        self.param_urls: Counter = Counter()

        # NEW: Bot versions
        self.bot_versions: Dict[str, Counter] = defaultdict(Counter)

        # NEW: Anomaly detection
        self.daily_request_counts: Dict[str, int] = defaultdict(int)

        # NEW: SEO metrics
        self.indexable_pages: int = 0
        self.non_indexable_pages: int = 0

        # NEW: Geographic (optional)
        self.ip_countries: Counter = Counter()

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

                # Count ALL requests for human vs bot ratio
                self.total_all_requests += 1

                # Check if it's a bot
                bot_type = self.detector.identify(parsed['user_agent'])
                if not bot_type:
                    self.human_requests += 1
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

                # Track status code groups
                status = parsed['status']
                if 200 <= status < 300:
                    self.status_code_groups['2xx'] += 1
                elif 300 <= status < 400:
                    self.status_code_groups['3xx'] += 1
                elif 400 <= status < 500:
                    self.status_code_groups['4xx'] += 1
                elif 500 <= status < 600:
                    self.status_code_groups['5xx'] += 1

                # Track request methods
                self.request_methods[parsed['method']] += 1

                # Track bandwidth (if available in parsed data)
                if 'bytes' in parsed and parsed['bytes']:
                    try:
                        bytes_sent = int(parsed['bytes']) if parsed['bytes'] != '-' else 0
                        self.total_bytes += bytes_sent
                        self.bot_bytes[bot_type] += bytes_sent
                    except (ValueError, TypeError):
                        pass

                # Track content types based on URL extension
                url = parsed['url'].split('?')[0].lower()
                if url.endswith(('.html', '.htm', '/')):
                    self.content_types['HTML'] += 1
                elif url.endswith(('.css',)):
                    self.content_types['CSS'] += 1
                elif url.endswith(('.js',)):
                    self.content_types['JavaScript'] += 1
                elif url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico')):
                    self.content_types['Images'] += 1
                elif url.endswith(('.json',)):
                    self.content_types['JSON/API'] += 1
                elif url.endswith(('.xml', '.rss', '.atom')):
                    self.content_types['XML/Feeds'] += 1
                elif url.endswith(('.pdf', '.doc', '.docx')):
                    self.content_types['Documents'] += 1
                else:
                    self.content_types['Other'] += 1

                # NEW: Referrer analysis
                referrer = parsed.get('referrer', '-')
                ref_category = self._categorize_referrer(referrer)
                self.referrer_sources[ref_category] += 1
                self.bot_referrer_sources[bot_type][ref_category] += 1
                if ref_category == 'external':
                    ref_domain = self._extract_domain(referrer)
                    if ref_domain:
                        self.referrer_domains[ref_domain] += 1

                # NEW: Site structure analysis
                section = self._extract_section(parsed['url'])
                self.section_hits[section] += 1
                self.bot_section_preferences[bot_type][section] += 1
                depth = self._calculate_depth(parsed['url'])
                self.crawl_depth[depth] += 1

                # NEW: Compliance tracking (robots.txt & sitemap)
                url_path = parsed['url'].lower()
                if 'robots.txt' in url_path:
                    self.robots_txt_accesses[bot_type] += 1
                if 'sitemap' in url_path and url_path.endswith('.xml'):
                    self.sitemap_accesses[bot_type] += 1

                # NEW: Query parameter tracking
                if '?' in parsed['url']:
                    params = self._extract_params(parsed['url'])
                    for param in params:
                        self.url_params[param] += 1
                    self.param_urls[parsed['url'].split('?')[0]] += 1

                # NEW: Bot version tracking
                version = self._extract_bot_version(parsed['user_agent'])
                self.bot_versions[bot_type][version] += 1

                # NEW: Daily counts for anomaly detection
                day_str = ts.strftime('%Y-%m-%d')
                self.daily_request_counts[day_str] += 1

                # NEW: SEO indexability
                if 200 <= parsed['status'] < 300:
                    self.indexable_pages += 1
                else:
                    self.non_indexable_pages += 1

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

        # NEW: Generate new insight analyses
        referrer_analysis = self.insights.analyze_referrers(
            dict(self.referrer_sources),
            dict(self.referrer_domains),
            {k: dict(v) for k, v in self.bot_referrer_sources.items()}
        )

        site_structure = self.insights.analyze_site_structure(
            dict(self.section_hits),
            dict(self.crawl_depth),
            {k: dict(v) for k, v in self.bot_section_preferences.items()}
        )

        crawl_efficiency = self.insights.analyze_crawl_efficiency(
            dict(self.content_types),
            self.total_requests
        )

        compliance = self.insights.analyze_compliance(
            dict(self.robots_txt_accesses),
            dict(self.sitemap_accesses),
            list(self.bot_requests.keys())
        )

        query_params = self.insights.analyze_query_params(
            dict(self.url_params),
            dict(self.param_urls),
            self.total_requests
        )

        anomalies = self.insights.detect_anomalies(
            dict(self.daily_request_counts)
        )

        bot_versions = self.insights.analyze_bot_versions(
            {k: dict(v) for k, v in self.bot_versions.items()}
        )

        seo_health = self.insights.calculate_seo_health(
            self.indexable_pages,
            self.non_indexable_pages,
            dict(self.status_codes)
        )

        competitive = self.insights.compare_bot_aggression(
            dict(self.bot_requests),
            {k: dict(v) for k, v in self.bot_section_preferences.items()},
            dict(self.bot_bytes)
        )

        # Calculate human vs bot ratio
        bot_percentage = (self.total_requests / self.total_all_requests * 100) if self.total_all_requests > 0 else 0
        human_percentage = 100 - bot_percentage

        # Status code breakdown with percentages
        status_breakdown = {}
        for group, count in self.status_code_groups.items():
            percentage = (count / self.total_requests * 100) if self.total_requests > 0 else 0
            status_breakdown[group] = {'count': count, 'percentage': round(percentage, 1)}

        # Format bandwidth
        def format_bytes(bytes_val):
            if bytes_val >= 1024 * 1024 * 1024:
                return f"{bytes_val / (1024*1024*1024):.2f} GB"
            elif bytes_val >= 1024 * 1024:
                return f"{bytes_val / (1024*1024):.2f} MB"
            elif bytes_val >= 1024:
                return f"{bytes_val / 1024:.2f} KB"
            return f"{bytes_val} B"

        # Bot bandwidth stats
        bot_bandwidth = []
        for bot_type, bytes_val in sorted(self.bot_bytes.items(), key=lambda x: x[1], reverse=True):
            bot_bandwidth.append({
                'type': bot_type,
                'bytes': bytes_val,
                'formatted': format_bytes(bytes_val)
            })

        # Content types with percentages
        content_breakdown = []
        for ctype, count in self.content_types.most_common():
            percentage = (count / self.total_requests * 100) if self.total_requests > 0 else 0
            content_breakdown.append({'type': ctype, 'count': count, 'percentage': round(percentage, 1)})

        # Request methods with percentages
        method_breakdown = []
        for method, count in self.request_methods.most_common():
            percentage = (count / self.total_requests * 100) if self.total_requests > 0 else 0
            method_breakdown.append({'method': method, 'count': count, 'percentage': round(percentage, 1)})

        return {
            'date_range': {
                'start': self.date_range['min'].strftime('%Y-%m-%d') if self.date_range['min'] else 'N/A',
                'end': self.date_range['max'].strftime('%Y-%m-%d') if self.date_range['max'] else 'N/A',
            },
            'total_requests': self.total_requests,
            'total_all_requests': self.total_all_requests,
            'human_requests': self.human_requests,
            'overall_success_rate': overall_success_rate,
            'bot_statistics': bot_stats,
            'top_urls': top_urls,
            'top_failed_urls': top_failed_urls,
            'failure_types': failure_types,
            'time_analysis': time_analysis,
            'behavior_analysis': behavior_analysis,
            'failure_analysis': failure_analysis,
            'recommendations': recommendations,
            'comparisons': comparisons,
            # New metrics
            'human_vs_bot': {
                'human_requests': self.human_requests,
                'bot_requests': self.total_requests,
                'human_percentage': round(human_percentage, 1),
                'bot_percentage': round(bot_percentage, 1)
            },
            'status_breakdown': status_breakdown,
            'bandwidth': {
                'total_bytes': self.total_bytes,
                'total_formatted': format_bytes(self.total_bytes),
                'by_bot': bot_bandwidth
            },
            'content_types': content_breakdown,
            'request_methods': method_breakdown,
            # NEW: Additional analysis data
            'referrer_analysis': referrer_analysis,
            'site_structure': site_structure,
            'crawl_efficiency': crawl_efficiency,
            'compliance': compliance,
            'query_params': query_params,
            'anomalies': anomalies,
            'bot_versions': bot_versions,
            'seo_health': seo_health,
            'competitive': competitive
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

    def _categorize_referrer(self, referrer: str) -> str:
        """Categorize referrer as direct, search, or external."""
        if not referrer or referrer == '-' or referrer == '':
            return 'direct'

        referrer_lower = referrer.lower()
        search_engines = ['google', 'bing', 'yahoo', 'duckduckgo', 'baidu', 'yandex']
        for engine in search_engines:
            if engine in referrer_lower:
                return 'search'

        return 'external'

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc if parsed.netloc else None
        except Exception:
            return None

    def _extract_section(self, url: str) -> str:
        """Extract the site section from URL."""
        path = url.split('?')[0]
        if path == '/' or path == '':
            return 'homepage'

        parts = [p for p in path.split('/') if p]
        if not parts:
            return 'homepage'

        first_part = parts[0].lower()
        common_sections = ['blog', 'products', 'services', 'about', 'contact',
                          'news', 'articles', 'category', 'categories', 'tag',
                          'tags', 'shop', 'store', 'docs', 'documentation',
                          'api', 'help', 'support', 'faq', 'pricing']

        if first_part in common_sections:
            return f'/{first_part}/'

        # Check for asset directories
        asset_patterns = ['wp-content', 'static', 'assets', 'images', 'img',
                         'css', 'js', 'fonts', 'media']
        if first_part in asset_patterns:
            return '/assets/'

        return f'/{first_part}/'

    def _calculate_depth(self, url: str) -> int:
        """Calculate crawl depth from URL."""
        path = url.split('?')[0]
        parts = [p for p in path.split('/') if p]
        depth = len(parts)
        return min(depth, 5)  # Cap at 5 for grouping

    def _extract_params(self, url: str) -> List[str]:
        """Extract query parameter names from URL."""
        try:
            if '?' not in url:
                return []
            query_string = url.split('?', 1)[1]
            params = parse_qs(query_string)
            return list(params.keys())
        except Exception:
            return []

    def _extract_bot_version(self, user_agent: str) -> str:
        """Extract bot version from user agent string."""
        if not user_agent:
            return 'unknown'

        # Common version patterns
        version_patterns = [
            r'GPTBot/(\d+\.?\d*)',
            r'ClaudeBot/(\d+\.?\d*)',
            r'Googlebot/(\d+\.?\d*)',
            r'bingbot/(\d+\.?\d*)',
            r'PerplexityBot/(\d+\.?\d*)',
            r'anthropic-ai/(\d+\.?\d*)',
            r'/(\d+\.\d+)',  # Generic version pattern
        ]

        for pattern in version_patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                return match.group(1)

        return 'unknown'
