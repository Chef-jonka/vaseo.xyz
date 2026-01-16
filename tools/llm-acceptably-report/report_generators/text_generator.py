"""Text Report Generator"""

class TextReportGenerator:
    def __init__(self):
        pass
    
    def generate(self, report, output_file=None):
        lines = []
        lines.append("=" * 70)
        lines.append("AI BOT TRAFFIC ANALYSIS REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        lines.append(f"Analysis Period: {report['date_range']['start']} to {report['date_range']['end']}")
        lines.append(f"Total AI Bot Requests: {report['total_requests']:,}")
        lines.append(f"Overall Success Rate: {report['overall_success_rate']:.1f}%")
        lines.append("")
        
        lines.append("BOT STATISTICS:")
        lines.append("-" * 70)
        for bot in report['bot_statistics']:
            lines.append(f"  {bot['type']}: {bot['count']:,} ({bot['percentage']:.1f}%) - {bot['success_rate']:.1f}% success")
        lines.append("")
        
        if report.get('recommendations'):
            lines.append("RECOMMENDATIONS:")
            lines.append("-" * 70)
            for i, rec in enumerate(report['recommendations'][:5], 1):
                lines.append(f"  {i}. [{rec['severity']}] {rec['title']}")
                lines.append(f"     {rec['description']}")
                lines.append(f"     Action: {rec['action']}")
                lines.append(f"     Impact: {rec['impact']}")
                lines.append("")
        
        lines.append("TOP REQUESTED URLS:")
        lines.append("-" * 70)
        for item in report['top_urls'][:10]:
            lines.append(f"  {item['count']:,}x - {item['url']}")
        lines.append("")
        
        lines.append("MOST COMMON FAILURES:")
        lines.append("-" * 70)
        for item in report['failure_types']:
            lines.append(f"  {item['type']}: {item['count']:,}")
        lines.append("")
        
        lines.append("TOP FAILED URLS:")
        lines.append("-" * 70)
        for item in report['top_failed_urls'][:10]:
            lines.append(f"  {item['count']:,}x - {item['url']}")
        lines.append("")
        
        lines.append("=" * 70)
        
        text = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(text)
            return output_file
        
        return text
