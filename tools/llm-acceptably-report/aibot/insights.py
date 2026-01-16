"""Analysis & Insights Generation"""
from collections import defaultdict, Counter

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
