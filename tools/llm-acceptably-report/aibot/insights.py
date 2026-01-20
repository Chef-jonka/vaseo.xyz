"""Analysis & Insights Generation"""
from collections import defaultdict, Counter
from typing import Dict, List, Any
import statistics

class InsightsEngine:
    def __init__(self, config=None):
        self.config = config
    
    def analyze_time_patterns(self, hourly_traffic, daily_traffic, hourly_by_bot):
        if not hourly_traffic:
            return {}
        
        peak_hour = max(hourly_traffic.items(), key=lambda x: x[1])
        quiet_hour = min(hourly_traffic.items(), key=lambda x: x[1])
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_sorted = sorted(daily_traffic.items(), 
                            key=lambda x: day_order.index(x[0]) if x[0] in day_order else 7)
        busiest_day = max(daily_traffic.items(), key=lambda x: x[1]) if daily_traffic else ('N/A', 0)
        
        bot_peak_times = {}
        for bot_type, hourly_data in hourly_by_bot.items():
            if hourly_data:
                peak = max(hourly_data.items(), key=lambda x: x[1])
                bot_peak_times[bot_type] = f"{peak[0]:02d}:00 ({peak[1]} requests)"
        
        hourly_dist = [{'hour': f"{hour:02d}:00", 'count': hourly_traffic.get(hour, 0)} for hour in range(24)]
        daily_dist = [{'day': day, 'count': count} for day, count in daily_sorted]
        
        return {
            'peak_hour': f"{peak_hour[0]:02d}:00 - {peak_hour[0]+1:02d}:00",
            'peak_hour_count': peak_hour[1],
            'quiet_hour': f"{quiet_hour[0]:02d}:00 - {quiet_hour[0]+1:02d}:00",
            'quiet_hour_count': quiet_hour[1],
            'busiest_day': busiest_day[0],
            'busiest_day_count': busiest_day[1],
            'bot_peak_times': bot_peak_times,
            'hourly_distribution': hourly_dist,
            'daily_distribution': daily_dist
        }
    
    def analyze_bot_behavior(self, bot_sessions, bot_requests, bot_successes, bot_url_preferences):
        behavior = {}
        for bot_type in bot_requests.keys():
            sessions = bot_sessions.get(bot_type, [])
            session_lengths = [len(session) for session in sessions]
            avg_session_length = sum(session_lengths) / len(session_lengths) if session_lengths else 0
            top_urls = bot_url_preferences[bot_type].most_common(5)
            success_rate = (bot_successes[bot_type] / bot_requests[bot_type] * 100) if bot_requests[bot_type] > 0 else 0
            
            behavior[bot_type] = {
                'avg_pages_per_session': round(avg_session_length, 1),
                'total_sessions': len(sessions),
                'preferred_urls': [{'url': url, 'count': count} for url, count in top_urls],
                'efficiency_score': round(success_rate, 1)
            }
        return behavior
    
    def analyze_failures(self, failure_details, url_failure_types, total_requests):
        if not failure_details:
            return {}
        
        root_causes = []
        post_failures = [f for f in failure_details if f.get('method') == 'POST']
        if post_failures:
            post_failure_rate = len(post_failures) / len(failure_details) * 100
            if post_failure_rate > 30:
                root_causes.append({
                    'issue': 'POST Request Failures',
                    'severity': 'HIGH',
                    'description': f'{len(post_failures)} failures on POST requests ({post_failure_rate:.1f}% of all failures)',
                    'suggestion': 'Review form handling and API endpoints'
                })
        
        url_failure_clusters = []
        for url, failure_types in url_failure_types.items():
            total_failures = sum(failure_types.values())
            if total_failures > 20:
                dominant_type = max(failure_types.items(), key=lambda x: x[1])
                url_failure_clusters.append({
                    'url': url,
                    'total_failures': total_failures,
                    'primary_error': dominant_type[0],
                    'error_count': dominant_type[1]
                })
        url_failure_clusters.sort(key=lambda x: x['total_failures'], reverse=True)
        
        total_failures = len(failure_details)
        failure_impact = []
        for failure_type, count in Counter([f['failure_type'] for f in failure_details]).most_common():
            percentage = (count / total_failures) * 100
            severity = 'HIGH' if percentage > 30 else 'MEDIUM' if percentage > 10 else 'LOW'
            failure_impact.append({
                'type': failure_type,
                'count': count,
                'percentage': round(percentage, 1),
                'severity': severity
            })
        
        return {
            'root_causes': root_causes,
            'url_failure_clusters': url_failure_clusters[:10],
            'failure_impact': failure_impact
        }
    
    def generate_recommendations(self, url_failures, url_failure_types, bot_requests, 
                                bot_successes, url_requests, total_requests):
        recommendations = []
        priority_score = 100
        
        for url, count in url_failures.most_common(5):
            if count > 50:
                failure_types = url_failure_types[url]
                dominant_error = max(failure_types.items(), key=lambda x: x[1])[0]
                severity = 'HIGH' if count > 100 else 'MEDIUM'
                recommendations.append({
                    'priority': priority_score,
                    'severity': severity,
                    'title': f'Fix errors on {url}',
                    'description': f'{count} failures detected ({dominant_error})',
                    'action': self._get_fix_suggestion(dominant_error, url),
                    'impact': f'Could improve success rate by {count/total_requests*100:.1f}%'
                })
                priority_score -= 10
        
        for bot_type in bot_requests.keys():
            success_rate = (bot_successes[bot_type] / bot_requests[bot_type] * 100) if bot_requests[bot_type] > 0 else 0
            if success_rate < 50 and bot_requests[bot_type] > 10:
                recommendations.append({
                    'priority': priority_score,
                    'severity': 'MEDIUM',
                    'title': f'Improve {bot_type} success rate',
                    'description': f'Currently at {success_rate:.1f}% (below 50%)',
                    'action': f'Investigate why {bot_type} is failing',
                    'impact': f'Affects {bot_requests[bot_type]} requests'
                })
                priority_score -= 5
        
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        return recommendations[:10]
    
    def _get_fix_suggestion(self, error_type, url):
        if '500' in error_type:
            return 'Check server logs for backend errors'
        elif '404' in error_type:
            return f'Add redirect from {url} or restore missing content'
        elif 'Redirect' in error_type and url != '/':
            return 'Review redirect rules. Consider if redirect is necessary or add permanent redirect (301).'
        return 'Investigate the specific error'
    
    def generate_comparisons(self, bot_requests, bot_successes, url_requests, url_failures):
        comparisons = {}
        
        bot_performance = [(bot, (bot_successes[bot] / bot_requests[bot] * 100) if bot_requests[bot] > 0 else 0) 
                          for bot in bot_requests.keys()]
        bot_performance.sort(key=lambda x: x[1], reverse=True)
        
        if len(bot_performance) >= 2:
            best_bot = bot_performance[0]
            worst_bot = bot_performance[-1]
            comparisons['bot_performance'] = {
                'best': {'name': best_bot[0], 'success_rate': round(best_bot[1], 1)},
                'worst': {'name': worst_bot[0], 'success_rate': round(worst_bot[1], 1)},
                'difference': round(best_bot[1] - worst_bot[1], 1)
            }
        
        url_performance = []
        for url in url_requests.keys():
            total = url_requests[url]
            failures = url_failures.get(url, 0)
            success_rate = ((total - failures) / total * 100) if total > 0 else 0
            if total > 10:
                url_performance.append((url, success_rate, total))
        
        url_performance.sort(key=lambda x: x[1], reverse=True)
        
        if len(url_performance) >= 2:
            best_url = url_performance[0]
            worst_url = url_performance[-1]
            comparisons['url_performance'] = {
                'best': {'url': best_url[0], 'success_rate': round(best_url[1], 1), 'requests': best_url[2]},
                'worst': {'url': worst_url[0], 'success_rate': round(worst_url[1], 1), 'requests': worst_url[2]},
                'difference': round(best_url[1] - worst_url[1], 1)
            }

        return comparisons

    # NEW METHODS FOR ENHANCED ANALYTICS

    def analyze_referrers(self, referrer_sources: Dict[str, int],
                         referrer_domains: Dict[str, int],
                         bot_referrer_sources: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Analyze referrer sources and patterns."""
        total = sum(referrer_sources.values())
        if total == 0:
            return {}

        # Source breakdown with percentages
        source_breakdown = []
        for source, count in sorted(referrer_sources.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            source_breakdown.append({
                'source': source,
                'count': count,
                'percentage': round(percentage, 1)
            })

        # Top referrer domains
        top_domains = [{'domain': d, 'count': c}
                      for d, c in sorted(referrer_domains.items(), key=lambda x: x[1], reverse=True)[:10]]

        # Per-bot referrer sources
        bot_sources = {}
        for bot, sources in bot_referrer_sources.items():
            bot_total = sum(sources.values())
            if bot_total > 0:
                bot_sources[bot] = {
                    source: round((count / bot_total) * 100, 1)
                    for source, count in sources.items()
                }

        return {
            'source_breakdown': source_breakdown,
            'top_domains': top_domains,
            'bot_sources': bot_sources,
            'direct_percentage': round(referrer_sources.get('direct', 0) / total * 100, 1) if total > 0 else 0
        }

    def analyze_site_structure(self, section_hits: Dict[str, int],
                              crawl_depth: Dict[int, int],
                              bot_section_preferences: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Analyze site structure and crawl patterns."""
        total_hits = sum(section_hits.values())
        if total_hits == 0:
            return {}

        # Section breakdown
        section_breakdown = []
        for section, count in sorted(section_hits.items(), key=lambda x: x[1], reverse=True)[:15]:
            percentage = (count / total_hits) * 100
            section_breakdown.append({
                'section': section,
                'count': count,
                'percentage': round(percentage, 1)
            })

        # Depth distribution
        total_depth = sum(crawl_depth.values())
        depth_distribution = []
        for depth in range(6):  # 0-5
            count = crawl_depth.get(depth, 0)
            percentage = (count / total_depth) * 100 if total_depth > 0 else 0
            label = f"Depth {depth}" if depth < 5 else "Depth 5+"
            depth_distribution.append({
                'depth': depth,
                'label': label,
                'count': count,
                'percentage': round(percentage, 1)
            })

        # Bot section preferences
        bot_preferences = {}
        for bot, sections in bot_section_preferences.items():
            top_sections = sorted(sections.items(), key=lambda x: x[1], reverse=True)[:5]
            bot_preferences[bot] = [{'section': s, 'count': c} for s, c in top_sections]

        return {
            'section_breakdown': section_breakdown,
            'depth_distribution': depth_distribution,
            'bot_preferences': bot_preferences,
            'homepage_hits': section_hits.get('homepage', 0),
            'avg_depth': sum(d * c for d, c in crawl_depth.items()) / total_depth if total_depth > 0 else 0
        }

    def analyze_crawl_efficiency(self, content_types: Dict[str, int],
                                total_requests: int) -> Dict[str, Any]:
        """Analyze crawl efficiency and budget usage."""
        if total_requests == 0:
            return {}

        # Define valuable vs non-valuable content
        valuable_types = ['HTML', 'JSON/API', 'XML/Feeds']
        asset_types = ['CSS', 'JavaScript', 'Images', 'Documents']

        valuable_count = sum(content_types.get(t, 0) for t in valuable_types)
        asset_count = sum(content_types.get(t, 0) for t in asset_types)

        valuable_percentage = (valuable_count / total_requests) * 100
        asset_percentage = (asset_count / total_requests) * 100

        # Calculate efficiency score (higher = better)
        efficiency_score = min(100, max(0, valuable_percentage * 1.2))

        # Waste analysis
        waste_score = asset_percentage
        waste_status = 'good' if waste_score < 20 else 'warning' if waste_score < 40 else 'critical'

        return {
            'valuable_requests': valuable_count,
            'valuable_percentage': round(valuable_percentage, 1),
            'asset_requests': asset_count,
            'asset_percentage': round(asset_percentage, 1),
            'efficiency_score': round(efficiency_score, 1),
            'waste_score': round(waste_score, 1),
            'waste_status': waste_status,
            'recommendations': self._get_efficiency_recommendations(waste_score, content_types)
        }

    def _get_efficiency_recommendations(self, waste_score: float,
                                        content_types: Dict[str, int]) -> List[str]:
        """Generate crawl efficiency recommendations."""
        recommendations = []

        if waste_score > 30:
            recommendations.append("Consider blocking bots from crawling static assets via robots.txt")

        if content_types.get('Images', 0) > content_types.get('HTML', 0):
            recommendations.append("High image crawl ratio detected - ensure images aren't being prioritized over content")

        if content_types.get('CSS', 0) + content_types.get('JavaScript', 0) > 100:
            recommendations.append("Significant CSS/JS crawling - add Disallow rules for /static/ or /assets/")

        if not recommendations:
            recommendations.append("Crawl efficiency is optimal")

        return recommendations

    def analyze_compliance(self, robots_accesses: Dict[str, int],
                          sitemap_accesses: Dict[str, int],
                          all_bots: List[str]) -> Dict[str, Any]:
        """Analyze bot compliance with robots.txt and sitemap."""
        compliant_bots = []
        non_compliant_bots = []

        for bot in all_bots:
            accessed_robots = robots_accesses.get(bot, 0) > 0
            accessed_sitemap = sitemap_accesses.get(bot, 0) > 0

            bot_info = {
                'bot': bot,
                'robots_accessed': accessed_robots,
                'sitemap_accessed': accessed_sitemap,
                'robots_count': robots_accesses.get(bot, 0),
                'sitemap_count': sitemap_accesses.get(bot, 0)
            }

            if accessed_robots or accessed_sitemap:
                compliant_bots.append(bot_info)
            else:
                non_compliant_bots.append(bot_info)

        compliance_rate = len(compliant_bots) / len(all_bots) * 100 if all_bots else 0

        return {
            'compliant_bots': compliant_bots,
            'non_compliant_bots': non_compliant_bots,
            'compliance_rate': round(compliance_rate, 1),
            'total_robots_accesses': sum(robots_accesses.values()),
            'total_sitemap_accesses': sum(sitemap_accesses.values())
        }

    def analyze_query_params(self, url_params: Dict[str, int],
                            param_urls: Dict[str, int],
                            total_requests: int) -> Dict[str, Any]:
        """Analyze query parameters in crawled URLs."""
        total_param_requests = sum(param_urls.values())
        param_percentage = (total_param_requests / total_requests) * 100 if total_requests > 0 else 0

        # Top parameters
        top_params = [{'param': p, 'count': c}
                     for p, c in sorted(url_params.items(), key=lambda x: x[1], reverse=True)[:10]]

        # URLs with params
        urls_with_params = [{'url': u, 'param_requests': c}
                          for u, c in sorted(param_urls.items(), key=lambda x: x[1], reverse=True)[:10]]

        # Detect potential crawl traps (URLs with session/tracking params)
        trap_indicators = ['session', 'sid', 'phpsessid', 'jsessionid', 'token', 'utm_', 'ref', 'sort', 'order', 'page']
        potential_traps = []
        for param, count in url_params.items():
            if any(trap in param.lower() for trap in trap_indicators) and count > 10:
                potential_traps.append({'param': param, 'count': count})

        return {
            'param_percentage': round(param_percentage, 1),
            'total_param_requests': total_param_requests,
            'top_params': top_params,
            'urls_with_params': urls_with_params,
            'potential_traps': potential_traps,
            'trap_warning': len(potential_traps) > 0
        }

    def detect_anomalies(self, daily_counts: Dict[str, int]) -> Dict[str, Any]:
        """Detect traffic anomalies and spikes."""
        if not daily_counts or len(daily_counts) < 3:
            return {'has_anomalies': False, 'anomalies': [], 'daily_data': []}

        values = list(daily_counts.values())
        dates = sorted(daily_counts.keys())

        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0
        except statistics.StatisticsError:
            return {'has_anomalies': False, 'anomalies': [], 'daily_data': []}

        # Detect spikes (> 2 standard deviations)
        anomalies = []
        threshold = mean + (2 * stdev) if stdev > 0 else mean * 1.5

        for date, count in daily_counts.items():
            if count > threshold:
                deviation = ((count - mean) / mean) * 100 if mean > 0 else 0
                anomalies.append({
                    'date': date,
                    'count': count,
                    'expected': round(mean),
                    'deviation_percentage': round(deviation, 1),
                    'severity': 'high' if count > mean + (3 * stdev) else 'medium'
                })

        # Daily data for charting
        daily_data = [{'date': d, 'count': daily_counts[d]} for d in dates]

        return {
            'has_anomalies': len(anomalies) > 0,
            'anomalies': sorted(anomalies, key=lambda x: x['deviation_percentage'], reverse=True),
            'daily_data': daily_data,
            'mean_daily': round(mean, 1),
            'std_dev': round(stdev, 1),
            'threshold': round(threshold, 1)
        }

    def analyze_bot_versions(self, bot_versions: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Analyze bot version distribution."""
        version_data = {}

        for bot, versions in bot_versions.items():
            total = sum(versions.values())
            if total > 0:
                version_list = []
                for version, count in sorted(versions.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total) * 100
                    version_list.append({
                        'version': version,
                        'count': count,
                        'percentage': round(percentage, 1)
                    })
                version_data[bot] = {
                    'versions': version_list,
                    'unique_versions': len(versions),
                    'primary_version': version_list[0]['version'] if version_list else 'unknown'
                }

        return {
            'by_bot': version_data,
            'total_bots_tracked': len(version_data)
        }

    def calculate_seo_health(self, indexable: int, non_indexable: int,
                            status_codes: Dict[int, int]) -> Dict[str, Any]:
        """Calculate SEO health indicators."""
        total = indexable + non_indexable
        if total == 0:
            return {'score': 0, 'status': 'unknown'}

        indexable_rate = (indexable / total) * 100

        # Calculate health score based on multiple factors
        score = indexable_rate

        # Penalize for 4xx errors
        error_4xx = sum(c for s, c in status_codes.items() if 400 <= s < 500)
        error_rate_4xx = (error_4xx / total) * 100 if total > 0 else 0
        score -= min(30, error_rate_4xx)  # Max penalty of 30

        # Penalize for 5xx errors (more severe)
        error_5xx = sum(c for s, c in status_codes.items() if 500 <= s < 600)
        error_rate_5xx = (error_5xx / total) * 100 if total > 0 else 0
        score -= min(40, error_rate_5xx * 2)  # Max penalty of 40

        score = max(0, min(100, score))

        # Determine status
        if score >= 80:
            status = 'excellent'
        elif score >= 60:
            status = 'good'
        elif score >= 40:
            status = 'warning'
        else:
            status = 'critical'

        # Issues breakdown
        issues = []
        if error_rate_4xx > 10:
            issues.append(f"High 4xx error rate: {round(error_rate_4xx, 1)}%")
        if error_rate_5xx > 5:
            issues.append(f"Server errors detected: {round(error_rate_5xx, 1)}%")
        if indexable_rate < 70:
            issues.append(f"Low indexable rate: {round(indexable_rate, 1)}%")

        return {
            'score': round(score, 1),
            'status': status,
            'indexable_rate': round(indexable_rate, 1),
            'indexable_pages': indexable,
            'non_indexable_pages': non_indexable,
            'error_rate_4xx': round(error_rate_4xx, 1),
            'error_rate_5xx': round(error_rate_5xx, 1),
            'issues': issues
        }

    def compare_bot_aggression(self, bot_requests: Dict[str, int],
                              bot_section_preferences: Dict[str, Dict[str, int]],
                              bot_bytes: Dict[str, int]) -> Dict[str, Any]:
        """Compare bot aggression and attention distribution."""
        total_requests = sum(bot_requests.values())
        if total_requests == 0:
            return {}

        # Calculate aggression metrics per bot
        bot_metrics = []
        for bot, requests in bot_requests.items():
            sections_crawled = len(bot_section_preferences.get(bot, {}))
            bandwidth = bot_bytes.get(bot, 0)

            # Aggression score based on volume and breadth
            share = (requests / total_requests) * 100
            aggression = share * (1 + (sections_crawled / 10))

            bot_metrics.append({
                'bot': bot,
                'requests': requests,
                'share': round(share, 1),
                'sections_crawled': sections_crawled,
                'bandwidth': bandwidth,
                'aggression_score': round(aggression, 1)
            })

        # Sort by aggression
        bot_metrics.sort(key=lambda x: x['aggression_score'], reverse=True)

        # Attention distribution (how spread out is the crawling)
        attention_scores = {}
        for bot, sections in bot_section_preferences.items():
            if sections:
                total_hits = sum(sections.values())
                # Calculate entropy-like score
                concentration = sum((c / total_hits) ** 2 for c in sections.values())
                attention_scores[bot] = round((1 - concentration) * 100, 1)  # Higher = more spread out

        return {
            'ranking': bot_metrics,
            'attention_distribution': attention_scores,
            'most_aggressive': bot_metrics[0] if bot_metrics else None,
            'least_aggressive': bot_metrics[-1] if bot_metrics else None
        }
