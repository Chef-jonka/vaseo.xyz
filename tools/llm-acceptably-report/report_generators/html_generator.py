"""
Enhanced UX HTML Report Generator for AI Bot Traffic Analysis
Tabbed interface with 6 tabs and sticky summary bar
"""

from datetime import datetime

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>LLM Acceptably Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; background: #f5f7fa; color: #2d3748; }}

        /* Navigation */
        .nav {{ position: sticky; top: 0; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); z-index: 1000; }}
        .nav-container {{ max-width: 1400px; margin: 0 auto; display: flex; align-items: center; gap: 20px; padding: 12px 20px; }}
        .nav-back {{ color: #667eea; text-decoration: none; font-size: 0.9em; font-weight: 500; padding: 8px 16px; border-radius: 6px; transition: all 0.2s; }}
        .nav-back:hover {{ background: #f7fafc; }}
        .nav-logo {{ font-size: 1.2em; font-weight: 700; color: #667eea; white-space: nowrap; }}
        .nav-actions {{ display: flex; gap: 10px; margin-left: auto; }}
        .btn-print {{ background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 500; transition: all 0.2s; }}
        .btn-print:hover {{ background: #5a67d8; }}

        /* Sticky Summary Bar */
        .sticky-summary {{ position: sticky; top: 56px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 20px; z-index: 999; display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; }}
        .sticky-stat {{ text-align: center; }}
        .sticky-stat-label {{ font-size: 0.75em; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px; }}
        .sticky-stat-value {{ font-size: 1.3em; font-weight: 700; }}
        .sticky-stat-value.good {{ color: #9ae6b4; }}
        .sticky-stat-value.warning {{ color: #fbd38d; }}
        .sticky-stat-value.critical {{ color: #feb2b2; }}

        /* Tab Navigation */
        .tab-navigation {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 0 20px; display: flex; justify-content: center; gap: 5px; flex-wrap: wrap; }}
        .tab-btn {{ background: none; border: none; padding: 15px 25px; font-size: 0.95em; font-weight: 500; color: #718096; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.2s; }}
        .tab-btn:hover {{ color: #667eea; background: #f7fafc; }}
        .tab-btn.active {{ color: #667eea; border-bottom-color: #667eea; }}

        /* Tab Content */
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* Print Styles */
        @media print {{
            .nav, .sticky-summary, .tab-navigation, .footer {{ display: none !important; }}
            .container {{ max-width: 100%; padding: 0; }}
            .tab-content {{ display: block !important; page-break-before: always; }}
            .section {{ break-inside: avoid; box-shadow: none; border: 1px solid #e2e8f0; }}
            body {{ background: white; }}
        }}

        /* Header */
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px 20px; text-align: center; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 700; }}
        .header p {{ font-size: 1.2em; opacity: 0.9; }}

        /* Container */
        .container {{ max-width: 1400px; margin: 0 auto; padding: 30px 20px; }}

        /* Sections */
        .section {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .section-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding-bottom: 12px; border-bottom: 3px solid #667eea; }}
        .section-title {{ font-size: 1.6em; color: #2d3748; display: flex; align-items: center; gap: 12px; }}
        .section-icon {{ font-size: 1.1em; }}
        .section-subtitle {{ color: #718096; font-size: 0.9em; margin-top: 5px; }}

        /* Executive Summary */
        .exec-summary {{ background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); border-left: 5px solid #667eea; }}
        .health-status {{ display: flex; align-items: center; gap: 20px; padding: 20px; background: white; border-radius: 8px; margin-bottom: 20px; }}
        .health-icon {{ font-size: 3em; }}
        .health-info {{ flex: 1; }}
        .health-label {{ font-size: 0.9em; color: #718096; margin-bottom: 5px; }}
        .health-value {{ font-size: 2em; font-weight: 700; }}
        .health-value.good {{ color: #48bb78; }}
        .health-value.warning {{ color: #ed8936; }}
        .health-value.critical {{ color: #f56565; }}

        /* Stats Grid */
        .quick-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .quick-stat {{ background: white; padding: 18px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .quick-stat-label {{ font-size: 0.85em; color: #718096; margin-bottom: 8px; }}
        .quick-stat-value {{ font-size: 1.6em; font-weight: 700; color: #2d3748; }}

        /* Tables */
        .bot-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .bot-table th {{ background: #f7fafc; padding: 12px; text-align: left; font-weight: 600; color: #4a5568; border-bottom: 2px solid #e2e8f0; }}
        .bot-table td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; }}
        .bot-table tr:hover {{ background: #f7fafc; }}
        .bot-name {{ display: flex; align-items: center; gap: 10px; font-weight: 600; }}

        /* Status Indicators */
        .status-indicator {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
        .status-indicator.good {{ background: #48bb78; }}
        .status-indicator.warning {{ background: #ed8936; }}
        .status-indicator.critical {{ background: #f56565; }}

        /* Progress Bars */
        .progress-bar {{ width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin-top: 5px; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s; }}

        /* Charts */
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin: 25px 0; }}
        .chart-container {{ background: #f7fafc; border-radius: 8px; padding: 20px; height: 320px; }}

        /* Insights Grid */
        .insights-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 20px 0; }}
        .insight-card {{ background: #f7fafc; border-radius: 8px; padding: 20px; border-top: 4px solid #667eea; }}
        .insight-title {{ font-weight: 700; font-size: 1em; color: #2d3748; margin-bottom: 15px; }}
        .insight-stat {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e2e8f0; }}
        .insight-stat:last-child {{ border-bottom: none; }}
        .insight-label {{ color: #718096; }}
        .insight-value {{ font-weight: 700; color: #2d3748; }}

        /* URL Lists */
        .url-list {{ background: #f7fafc; border-radius: 8px; padding: 20px; margin-top: 20px; }}
        .url-item {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; background: white; border-radius: 6px; margin-bottom: 8px; font-family: 'Courier New', monospace; font-size: 0.85em; transition: transform 0.2s; }}
        .url-item:hover {{ transform: translateX(5px); }}
        .url-item:last-child {{ margin-bottom: 0; }}
        .url-path {{ color: #4a5568; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; margin-right: 15px; }}
        .url-count {{ color: #667eea; font-weight: 700; white-space: nowrap; background: #edf2f7; padding: 4px 10px; border-radius: 10px; }}

        /* Recommendations */
        .recommendations-grid {{ display: grid; gap: 15px; }}
        .recommendation {{ background: white; border-left: 5px solid #667eea; padding: 18px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform 0.2s, box-shadow 0.2s; }}
        .recommendation:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .recommendation.high {{ border-left-color: #f56565; background: #fff5f5; }}
        .recommendation.medium {{ border-left-color: #ed8936; background: #fffaf0; }}
        .recommendation.low {{ border-left-color: #48bb78; background: #f0fff4; }}
        .rec-header {{ display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px; }}
        .rec-title {{ font-size: 1.1em; font-weight: 700; color: #2d3748; flex: 1; }}
        .rec-badge {{ padding: 4px 10px; border-radius: 15px; font-size: 0.7em; font-weight: 700; text-transform: uppercase; white-space: nowrap; margin-left: 10px; }}
        .rec-badge.high {{ background: #f56565; color: white; }}
        .rec-badge.medium {{ background: #ed8936; color: white; }}
        .rec-badge.low {{ background: #48bb78; color: white; }}
        .rec-description {{ color: #4a5568; margin-bottom: 10px; line-height: 1.5; font-size: 0.95em; }}
        .rec-action {{ background: white; padding: 10px; border-radius: 6px; margin-bottom: 8px; font-size: 0.9em; border-left: 3px solid #667eea; }}
        .rec-impact {{ font-size: 0.85em; color: #667eea; font-weight: 600; }}

        /* Comparison Box */
        .comparison-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; margin: 20px 0; }}
        .comparison-title {{ font-size: 1.3em; font-weight: 700; margin-bottom: 20px; }}
        .comparison-items {{ display: flex; justify-content: space-around; text-align: center; gap: 20px; flex-wrap: wrap; }}
        .comparison-item {{ flex: 1; min-width: 150px; }}
        .comparison-label {{ opacity: 0.9; margin-bottom: 8px; font-size: 1em; }}
        .comparison-value {{ font-size: 2em; font-weight: 700; margin: 8px 0; }}
        .comparison-subtitle {{ opacity: 0.85; font-size: 0.85em; }}

        /* Compliance Checklist */
        .compliance-list {{ list-style: none; }}
        .compliance-item {{ display: flex; align-items: center; gap: 12px; padding: 12px; background: white; border-radius: 6px; margin-bottom: 8px; }}
        .compliance-icon {{ font-size: 1.2em; }}
        .compliance-bot {{ font-weight: 600; flex: 1; }}
        .compliance-badges {{ display: flex; gap: 8px; }}
        .compliance-badge {{ padding: 4px 10px; border-radius: 4px; font-size: 0.75em; font-weight: 600; }}
        .compliance-badge.yes {{ background: #c6f6d5; color: #276749; }}
        .compliance-badge.no {{ background: #fed7d7; color: #c53030; }}

        /* Gauge */
        .gauge-container {{ text-align: center; padding: 20px; }}
        .gauge-value {{ font-size: 3em; font-weight: 700; margin-bottom: 10px; }}
        .gauge-label {{ color: #718096; font-size: 0.9em; }}

        /* Anomaly Timeline */
        .anomaly-item {{ display: flex; align-items: center; gap: 15px; padding: 15px; background: white; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #f56565; }}
        .anomaly-date {{ font-weight: 600; color: #2d3748; min-width: 100px; }}
        .anomaly-details {{ flex: 1; }}
        .anomaly-count {{ font-size: 1.2em; font-weight: 700; color: #f56565; }}
        .anomaly-deviation {{ font-size: 0.85em; color: #718096; }}

        /* Footer */
        .footer {{ background: white; padding: 30px 20px; text-align: center; color: #718096; font-size: 0.9em; border-top: 1px solid #e2e8f0; }}

        /* Responsive */
        @media (max-width: 768px) {{
            .tab-btn {{ padding: 12px 15px; font-size: 0.85em; }}
            .charts-grid, .insights-grid, .quick-stats {{ grid-template-columns: 1fr; }}
            .comparison-items {{ flex-direction: column; }}
            .sticky-summary {{ gap: 20px; }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="/dashboard" class="nav-back">← Dashboard</a>
            <div class="nav-logo">LLM Acceptably Report</div>
            <div class="nav-actions">
                <button class="btn-print" onclick="window.print()">Save as PDF</button>
            </div>
        </div>
    </nav>

    <!-- Sticky Summary Bar -->
    <div class="sticky-summary">
        <div class="sticky-stat">
            <div class="sticky-stat-label">Health</div>
            <div class="sticky-stat-value {health_class}">{health_status}</div>
        </div>
        <div class="sticky-stat">
            <div class="sticky-stat-label">Total Requests</div>
            <div class="sticky-stat-value">{total_requests}</div>
        </div>
        <div class="sticky-stat">
            <div class="sticky-stat-label">Success Rate</div>
            <div class="sticky-stat-value {health_class}">{success_rate}%</div>
        </div>
        <div class="sticky-stat">
            <div class="sticky-stat-label">Issues</div>
            <div class="sticky-stat-value {issues_class}">{issues_count}</div>
        </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-navigation">
        <button class="tab-btn active" data-tab="overview">Overview</button>
        <button class="tab-btn" data-tab="traffic">Traffic Analysis</button>
        <button class="tab-btn" data-tab="crawl">Crawl Intelligence</button>
        <button class="tab-btn" data-tab="bots">Bot Comparison</button>
        <button class="tab-btn" data-tab="technical">Technical & SEO</button>
        <button class="tab-btn" data-tab="actions">Actions</button>
    </div>

    <div class="header">
        <h1>LLM Acceptably Report</h1>
        <p>AI Bot Traffic Intelligence Report</p>
    </div>

    <div class="container">
        <!-- Tab 1: Overview -->
        <div id="overview" class="tab-content active">
            {overview_content}
        </div>

        <!-- Tab 2: Traffic Analysis -->
        <div id="traffic" class="tab-content">
            {traffic_content}
        </div>

        <!-- Tab 3: Crawl Intelligence -->
        <div id="crawl" class="tab-content">
            {crawl_content}
        </div>

        <!-- Tab 4: Bot Comparison -->
        <div id="bots" class="tab-content">
            {bots_content}
        </div>

        <!-- Tab 5: Technical & SEO -->
        <div id="technical" class="tab-content">
            {technical_content}
        </div>

        <!-- Tab 6: Actions -->
        <div id="actions" class="tab-content">
            {actions_content}
        </div>
    </div>

    <div class="footer">
        <p>Generated on {generated_date}</p>
        <p style="margin-top: 10px;">LLM Acceptably Report by <a href="https://vaseo.xyz" target="_blank" style="color: #667eea;">Vaseo</a></p>
    </div>

    <script>
        {chart_scripts}

        // Tab switching
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabBtns.forEach(btn => {{
            btn.addEventListener('click', () => {{
                const tabId = btn.dataset.tab;

                tabBtns.forEach(b => b.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));

                btn.classList.add('active');
                document.getElementById(tabId).classList.add('active');
            }});
        }});
    </script>
</body>
</html>
"""


def get_health_status(success_rate):
    if success_rate >= 80:
        return ('EXCELLENT', 'good', '✅')
    elif success_rate >= 60:
        return ('GOOD', 'warning', '⚠️')
    else:
        return ('NEEDS ATTENTION', 'critical', '❌')


def format_bytes(bytes_val):
    """Format bytes to human readable."""
    if bytes_val >= 1024 * 1024 * 1024:
        return f"{bytes_val / (1024*1024*1024):.2f} GB"
    elif bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024*1024):.2f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    return f"{bytes_val} B"


# ============== TAB 1: OVERVIEW ==============

def generate_overview_tab(report):
    """Generate Overview tab content."""
    success_rate = report['overall_success_rate']
    health_label, health_class, health_icon = get_health_status(success_rate)
    top_bot = report['bot_statistics'][0] if report['bot_statistics'] else {'type': 'N/A'}
    critical_issues = sum(1 for rec in report.get('recommendations', []) if rec['severity'] == 'HIGH')
    human_vs_bot = report.get('human_vs_bot', {})
    seo_health = report.get('seo_health', {})

    html = f"""
    <div class="section exec-summary">
        <div class="section-header">
            <h2 class="section-title"><span class="section-icon">📊</span>Executive Summary</h2>
        </div>
        <div class="health-status">
            <div class="health-icon">{health_icon}</div>
            <div class="health-info">
                <div class="health-label">Overall Health</div>
                <div class="health-value {health_class}">{health_label}</div>
                <div style="color: #718096; font-size: 0.9em; margin-top: 5px;">{success_rate:.1f}% of AI bot requests successful</div>
            </div>
        </div>
        <div class="quick-stats">
            <div class="quick-stat">
                <div class="quick-stat-label">Total AI Requests</div>
                <div class="quick-stat-value">{report['total_requests']:,}</div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-label">Most Active Bot</div>
                <div class="quick-stat-value" style="font-size: 1.2em;">{top_bot['type']}</div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-label">Critical Issues</div>
                <div class="quick-stat-value" style="color: {'#f56565' if critical_issues > 0 else '#48bb78'};">{critical_issues}</div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-label">Analysis Period</div>
                <div class="quick-stat-value" style="font-size: 0.95em;">{report['date_range']['start']}</div>
                <div style="font-size: 0.8em; color: #718096;">to {report['date_range']['end']}</div>
            </div>
        </div>

        <!-- Human vs Bot Ratio -->
        <div class="comparison-box">
            <div class="comparison-title">Human vs AI Bot Traffic</div>
            <div class="comparison-items">
                <div class="comparison-item">
                    <div class="comparison-label">Human Traffic</div>
                    <div class="comparison-value">{human_vs_bot.get('human_percentage', 0)}%</div>
                    <div class="comparison-subtitle">{human_vs_bot.get('human_requests', 0):,} requests</div>
                </div>
                <div class="comparison-item">
                    <div class="comparison-label">Total Requests</div>
                    <div class="comparison-value">{report.get('total_all_requests', 0):,}</div>
                    <div class="comparison-subtitle">All traffic analyzed</div>
                </div>
                <div class="comparison-item">
                    <div class="comparison-label">AI Bot Traffic</div>
                    <div class="comparison-value">{human_vs_bot.get('bot_percentage', 0)}%</div>
                    <div class="comparison-subtitle">{human_vs_bot.get('bot_requests', 0):,} requests</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Key Metrics Grid -->
    <div class="section">
        <div class="section-header">
            <h2 class="section-title"><span class="section-icon">📈</span>Key Metrics</h2>
        </div>
        <div class="charts-grid">
            <div class="chart-container"><canvas id="botDistributionChart"></canvas></div>
            <div class="chart-container"><canvas id="botSuccessChart"></canvas></div>
        </div>
    </div>
    """

    # SEO Health Score (if available)
    if seo_health and seo_health.get('score') is not None:
        seo_status = seo_health.get('status', 'unknown')
        seo_color = '#48bb78' if seo_status == 'excellent' else '#ed8936' if seo_status in ['good', 'warning'] else '#f56565'
        html += f"""
    <div class="section">
        <div class="section-header">
            <h2 class="section-title"><span class="section-icon">🔍</span>SEO Health Score</h2>
        </div>
        <div class="gauge-container">
            <div class="gauge-value" style="color: {seo_color};">{seo_health.get('score', 0)}</div>
            <div class="gauge-label">out of 100 | Status: {seo_status.upper()}</div>
        </div>
        <div class="insights-grid">
            <div class="insight-card">
                <div class="insight-title">Indexable Rate</div>
                <div class="insight-stat"><span class="insight-label">Indexable Pages</span><span class="insight-value">{seo_health.get('indexable_pages', 0):,}</span></div>
                <div class="insight-stat"><span class="insight-label">Rate</span><span class="insight-value">{seo_health.get('indexable_rate', 0)}%</span></div>
            </div>
            <div class="insight-card">
                <div class="insight-title">Error Rates</div>
                <div class="insight-stat"><span class="insight-label">4xx Errors</span><span class="insight-value">{seo_health.get('error_rate_4xx', 0)}%</span></div>
                <div class="insight-stat"><span class="insight-label">5xx Errors</span><span class="insight-value">{seo_health.get('error_rate_5xx', 0)}%</span></div>
            </div>
        </div>
    </div>
        """

    return html


# ============== TAB 2: TRAFFIC ANALYSIS ==============

def generate_traffic_tab(report):
    """Generate Traffic Analysis tab content."""
    html = ""

    # Bot Overview
    html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🤖</span>Bot Overview</h2></div>
        <table class="bot-table">
            <thead><tr><th>Bot Type</th><th>Requests</th><th>Share</th><th>Success Rate</th><th>Performance</th></tr></thead>
            <tbody>
    """
    for bot in report['bot_statistics']:
        status = 'good' if bot['success_rate'] >= 80 else 'warning' if bot['success_rate'] >= 50 else 'critical'
        html += f"""
                <tr>
                    <td><div class="bot-name"><span class="status-indicator {status}"></span>{bot['type']}</div></td>
                    <td><strong>{bot['count']:,}</strong></td>
                    <td>{bot['percentage']:.1f}%</td>
                    <td><strong>{bot['success_rate']:.1f}%</strong></td>
                    <td><div class="progress-bar"><div class="progress-fill" style="width: {bot['success_rate']}%"></div></div></td>
                </tr>
        """
    html += "</tbody></table></div>"

    # Referrer Analysis
    referrer_analysis = report.get('referrer_analysis', {})
    if referrer_analysis:
        html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🔗</span>Referrer Analysis</h2></div>
        <div class="charts-grid">
            <div class="chart-container"><canvas id="referrerSourceChart"></canvas></div>
            <div class="insight-card" style="height: auto;">
                <div class="insight-title">Top Referrer Domains</div>
        """
        for domain in referrer_analysis.get('top_domains', [])[:5]:
            html += f'<div class="insight-stat"><span class="insight-label">{domain["domain"]}</span><span class="insight-value">{domain["count"]:,}</span></div>'
        html += """
            </div>
        </div>
    </div>
        """

    # Traffic Patterns
    time_analysis = report.get('time_analysis', {})
    if time_analysis:
        html += f"""
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">⏰</span>Traffic Patterns</h2></div>
        <div class="insights-grid">
            <div class="insight-card">
                <div class="insight-title">Peak Activity</div>
                <div class="insight-stat"><span class="insight-label">Peak Hour</span><span class="insight-value">{time_analysis.get('peak_hour', 'N/A')}</span></div>
                <div class="insight-stat"><span class="insight-label">Requests</span><span class="insight-value">{time_analysis.get('peak_hour_count', 0):,}</span></div>
            </div>
            <div class="insight-card">
                <div class="insight-title">Quiet Period</div>
                <div class="insight-stat"><span class="insight-label">Quiet Hour</span><span class="insight-value">{time_analysis.get('quiet_hour', 'N/A')}</span></div>
                <div class="insight-stat"><span class="insight-label">Requests</span><span class="insight-value">{time_analysis.get('quiet_hour_count', 0):,}</span></div>
            </div>
            <div class="insight-card">
                <div class="insight-title">Busiest Day</div>
                <div class="insight-stat"><span class="insight-label">Day</span><span class="insight-value">{time_analysis.get('busiest_day', 'N/A')}</span></div>
                <div class="insight-stat"><span class="insight-label">Requests</span><span class="insight-value">{time_analysis.get('busiest_day_count', 0):,}</span></div>
            </div>
        </div>
    </div>
        """

    # Anomaly Detection
    anomalies = report.get('anomalies', {})
    if anomalies and anomalies.get('has_anomalies'):
        html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">⚠️</span>Anomaly Detection</h2></div>
        <p style="color: #718096; margin-bottom: 20px;">Traffic spikes detected that exceed normal patterns (>2 standard deviations)</p>
        """
        for anomaly in anomalies.get('anomalies', [])[:5]:
            severity_color = '#f56565' if anomaly['severity'] == 'high' else '#ed8936'
            html += f"""
        <div class="anomaly-item" style="border-left-color: {severity_color};">
            <div class="anomaly-date">{anomaly['date']}</div>
            <div class="anomaly-details">
                <div class="anomaly-count">{anomaly['count']:,} requests</div>
                <div class="anomaly-deviation">Expected: ~{anomaly['expected']:,} | +{anomaly['deviation_percentage']}% above normal</div>
            </div>
        </div>
            """
        html += "</div>"
    elif anomalies:
        html += f"""
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">✅</span>Anomaly Detection</h2></div>
        <p style="color: #48bb78; font-weight: 600;">No traffic anomalies detected.</p>
        <p style="color: #718096; margin-top: 10px;">Average daily traffic: {anomalies.get('mean_daily', 0):,.0f} requests</p>
    </div>
        """

    return html


# ============== TAB 3: CRAWL INTELLIGENCE ==============

def generate_crawl_tab(report):
    """Generate Crawl Intelligence tab content."""
    html = ""

    # Site Structure Insights
    site_structure = report.get('site_structure', {})
    if site_structure:
        html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🏗️</span>Site Structure Insights</h2></div>
        <div class="charts-grid">
            <div class="chart-container"><canvas id="sectionHitsChart"></canvas></div>
            <div class="chart-container"><canvas id="crawlDepthChart"></canvas></div>
        </div>
        <div class="insights-grid" style="margin-top: 20px;">
        """
        for section in site_structure.get('section_breakdown', [])[:6]:
            html += f"""
            <div class="insight-card">
                <div class="insight-title">{section['section']}</div>
                <div style="font-size: 2em; font-weight: 700; color: #667eea;">{section['percentage']}%</div>
                <div style="color: #718096;">{section['count']:,} hits</div>
            </div>
            """
        html += "</div></div>"

    # Crawl Efficiency & Budget
    crawl_efficiency = report.get('crawl_efficiency', {})
    if crawl_efficiency:
        waste_status = crawl_efficiency.get('waste_status', 'good')
        status_color = '#48bb78' if waste_status == 'good' else '#ed8936' if waste_status == 'warning' else '#f56565'
        html += f"""
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">⚡</span>Crawl Efficiency & Budget</h2></div>
        <div class="gauge-container">
            <div class="gauge-value" style="color: {status_color};">{crawl_efficiency.get('efficiency_score', 0)}</div>
            <div class="gauge-label">Efficiency Score (out of 100)</div>
        </div>
        <div class="insights-grid">
            <div class="insight-card">
                <div class="insight-title">Valuable Content</div>
                <div style="font-size: 2em; font-weight: 700; color: #48bb78;">{crawl_efficiency.get('valuable_percentage', 0)}%</div>
                <div style="color: #718096;">{crawl_efficiency.get('valuable_requests', 0):,} requests</div>
                <div style="color: #718096; font-size: 0.85em; margin-top: 10px;">HTML, JSON/API, XML/Feeds</div>
            </div>
            <div class="insight-card">
                <div class="insight-title">Asset Crawling (Waste)</div>
                <div style="font-size: 2em; font-weight: 700; color: {status_color};">{crawl_efficiency.get('asset_percentage', 0)}%</div>
                <div style="color: #718096;">{crawl_efficiency.get('asset_requests', 0):,} requests</div>
                <div style="color: #718096; font-size: 0.85em; margin-top: 10px;">CSS, JS, Images, Documents</div>
            </div>
        </div>
        """
        recommendations = crawl_efficiency.get('recommendations', [])
        if recommendations:
            html += '<div style="margin-top: 20px;">'
            for rec in recommendations:
                html += f'<div style="background: #f7fafc; padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #667eea;">{rec}</div>'
            html += '</div>'
        html += "</div>"

    # Query Parameter Analysis
    query_params = report.get('query_params', {})
    if query_params:
        html += f"""
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">❓</span>Query Parameter Analysis</h2></div>
        <div class="insights-grid">
            <div class="insight-card">
                <div class="insight-title">Parameter Usage</div>
                <div style="font-size: 2em; font-weight: 700; color: #667eea;">{query_params.get('param_percentage', 0)}%</div>
                <div style="color: #718096;">of requests have query params</div>
                <div style="color: #718096; margin-top: 10px;">{query_params.get('total_param_requests', 0):,} total</div>
            </div>
            <div class="insight-card">
                <div class="insight-title">Top Parameters</div>
        """
        for param in query_params.get('top_params', [])[:5]:
            html += f'<div class="insight-stat"><span class="insight-label">{param["param"]}</span><span class="insight-value">{param["count"]:,}</span></div>'
        html += "</div></div>"

        # Crawl trap warning
        if query_params.get('trap_warning'):
            html += '<div style="background: #fff5f5; border: 1px solid #f56565; border-radius: 8px; padding: 15px; margin-top: 20px;">'
            html += '<strong style="color: #c53030;">⚠️ Potential Crawl Traps Detected</strong>'
            html += '<p style="color: #718096; margin-top: 8px;">Parameters that may cause infinite crawl loops:</p>'
            html += '<ul style="margin-top: 10px; margin-left: 20px; color: #4a5568;">'
            for trap in query_params.get('potential_traps', []):
                html += f'<li><code>{trap["param"]}</code> ({trap["count"]:,} requests)</li>'
            html += '</ul></div>'
        html += "</div>"

    # Robots.txt & Sitemap Compliance
    compliance = report.get('compliance', {})
    if compliance:
        html += f"""
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">📋</span>Robots.txt & Sitemap Compliance</h2></div>
        <div class="gauge-container" style="padding: 15px;">
            <div class="gauge-value" style="color: {'#48bb78' if compliance.get('compliance_rate', 0) >= 50 else '#ed8936'};">{compliance.get('compliance_rate', 0)}%</div>
            <div class="gauge-label">of bots accessed robots.txt or sitemap</div>
        </div>
        <ul class="compliance-list">
        """
        for bot in compliance.get('compliant_bots', []):
            html += f"""
            <li class="compliance-item">
                <span class="compliance-icon">✅</span>
                <span class="compliance-bot">{bot['bot']}</span>
                <div class="compliance-badges">
                    <span class="compliance-badge {'yes' if bot['robots_accessed'] else 'no'}">robots.txt: {'Yes' if bot['robots_accessed'] else 'No'}</span>
                    <span class="compliance-badge {'yes' if bot['sitemap_accessed'] else 'no'}">sitemap: {'Yes' if bot['sitemap_accessed'] else 'No'}</span>
                </div>
            </li>
            """
        for bot in compliance.get('non_compliant_bots', []):
            html += f"""
            <li class="compliance-item" style="background: #fff5f5;">
                <span class="compliance-icon">❌</span>
                <span class="compliance-bot">{bot['bot']}</span>
                <div class="compliance-badges">
                    <span class="compliance-badge no">No compliance files accessed</span>
                </div>
            </li>
            """
        html += "</ul></div>"

    return html


# ============== TAB 4: BOT COMPARISON ==============

def generate_bots_tab(report):
    """Generate Bot Comparison tab content."""
    html = ""

    # Competitive Bot Comparison
    competitive = report.get('competitive', {})
    if competitive and competitive.get('ranking'):
        html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🏆</span>Competitive Bot Comparison</h2></div>
        <table class="bot-table">
            <thead><tr><th>Rank</th><th>Bot</th><th>Requests</th><th>Share</th><th>Sections</th><th>Aggression Score</th></tr></thead>
            <tbody>
        """
        for i, bot in enumerate(competitive.get('ranking', []), 1):
            html += f"""
            <tr>
                <td><strong>#{i}</strong></td>
                <td><strong>{bot['bot']}</strong></td>
                <td>{bot['requests']:,}</td>
                <td>{bot['share']}%</td>
                <td>{bot['sections_crawled']}</td>
                <td><strong style="color: {'#f56565' if bot['aggression_score'] > 50 else '#ed8936' if bot['aggression_score'] > 25 else '#48bb78'};">{bot['aggression_score']}</strong></td>
            </tr>
            """
        html += "</tbody></table></div>"

    # Bot Version Tracking
    bot_versions = report.get('bot_versions', {})
    if bot_versions and bot_versions.get('by_bot'):
        html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🔢</span>Bot Version Tracking</h2></div>
        <div class="insights-grid">
        """
        for bot_name, version_info in bot_versions.get('by_bot', {}).items():
            html += f"""
            <div class="insight-card">
                <div class="insight-title">{bot_name}</div>
                <div style="font-size: 1.5em; font-weight: 700; color: #667eea; margin: 10px 0;">v{version_info.get('primary_version', 'unknown')}</div>
                <div style="color: #718096; font-size: 0.85em; margin-bottom: 10px;">{version_info.get('unique_versions', 1)} version(s) detected</div>
            """
            for v in version_info.get('versions', [])[:3]:
                html += f'<div class="insight-stat"><span class="insight-label">v{v["version"]}</span><span class="insight-value">{v["percentage"]}%</span></div>'
            html += "</div>"
        html += "</div></div>"

    # Bot Behavior
    behavior_analysis = report.get('behavior_analysis', {})
    if behavior_analysis:
        html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">💡</span>Bot Behavior</h2></div>
        <div class="insights-grid">
        """
        for bot_name, behavior in behavior_analysis.items():
            status = 'good' if behavior.get('efficiency_score', 0) >= 80 else 'warning' if behavior.get('efficiency_score', 0) >= 50 else 'critical'
            html += f"""
            <div class="insight-card">
                <div class="insight-title">{bot_name}</div>
                <div class="insight-stat"><span class="insight-label">Avg Pages/Session</span><span class="insight-value">{behavior.get('avg_pages_per_session', 0)}</span></div>
                <div class="insight-stat"><span class="insight-label">Total Sessions</span><span class="insight-value">{behavior.get('total_sessions', 0):,}</span></div>
                <div class="insight-stat"><span class="insight-label">Efficiency</span><span class="insight-value"><span class="status-indicator {status}"></span> {behavior.get('efficiency_score', 0)}%</span></div>
            </div>
            """
        html += "</div></div>"

    # Comparisons
    comparisons = report.get('comparisons', {})
    if comparisons.get('bot_performance'):
        bp = comparisons['bot_performance']
        html += f"""
    <div class="comparison-box">
        <div class="comparison-title">Best vs Worst Performing Bots</div>
        <div class="comparison-items">
            <div class="comparison-item">
                <div class="comparison-label">Best Performer</div>
                <div class="comparison-value">{bp['best']['success_rate']}%</div>
                <div class="comparison-subtitle">{bp['best']['name']}</div>
            </div>
            <div class="comparison-item">
                <div class="comparison-label">Performance Gap</div>
                <div class="comparison-value">{bp['difference']}%</div>
                <div class="comparison-subtitle">Difference</div>
            </div>
            <div class="comparison-item">
                <div class="comparison-label">Needs Improvement</div>
                <div class="comparison-value">{bp['worst']['success_rate']}%</div>
                <div class="comparison-subtitle">{bp['worst']['name']}</div>
            </div>
        </div>
    </div>
        """

    return html


# ============== TAB 5: TECHNICAL & SEO ==============

def generate_technical_tab(report):
    """Generate Technical & SEO tab content."""
    status_breakdown = report.get('status_breakdown', {})
    bandwidth = report.get('bandwidth', {})
    content_types = report.get('content_types', [])
    request_methods = report.get('request_methods', [])

    status_colors = {
        '2xx': '#48bb78',
        '3xx': '#ed8936',
        '4xx': '#f56565',
        '5xx': '#9f7aea'
    }
    label_map = {
        '2xx': '✅ Success (2xx)',
        '3xx': '↩️ Redirects (3xx)',
        '4xx': '❌ Client Errors (4xx)',
        '5xx': '💥 Server Errors (5xx)'
    }

    html = """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">📈</span>Technical Metrics</h2></div>
        <h3 style="margin-bottom: 15px; color: #2d3748;">HTTP Response Status Codes</h3>
        <div class="insights-grid">
    """
    for code_group in ['2xx', '3xx', '4xx', '5xx']:
        data = status_breakdown.get(code_group, {'count': 0, 'percentage': 0})
        color = status_colors.get(code_group, '#718096')
        html += f"""
            <div class="insight-card" style="border-top-color: {color};">
                <div class="insight-title">{label_map.get(code_group, code_group)}</div>
                <div style="font-size: 2em; font-weight: 700; color: {color}; margin: 10px 0;">{data['percentage']}%</div>
                <div style="color: #718096;">{data['count']:,} requests</div>
                <div class="progress-bar" style="margin-top: 12px; height: 10px;">
                    <div class="progress-fill" style="width: {data['percentage']}%; background: {color};"></div>
                </div>
            </div>
        """

    html += """
        </div>
        <div class="charts-grid" style="margin-top: 25px;">
            <div class="chart-container"><canvas id="statusCodeChart"></canvas></div>
            <div class="chart-container"><canvas id="contentTypeChart"></canvas></div>
        </div>
        <div class="insights-grid" style="margin-top: 25px;">
            <div class="insight-card">
                <div class="insight-title">Request Methods</div>
    """
    for method_data in request_methods[:5]:
        html += f'<div class="insight-stat"><span class="insight-label">{method_data["method"]}</span><span class="insight-value">{method_data["percentage"]}% ({method_data["count"]:,})</span></div>'

    html += """
            </div>
            <div class="insight-card">
                <div class="insight-title">Content Types Requested</div>
    """
    for ct_data in content_types[:5]:
        html += f'<div class="insight-stat"><span class="insight-label">{ct_data["type"]}</span><span class="insight-value">{ct_data["percentage"]}% ({ct_data["count"]:,})</span></div>'

    total_bandwidth = bandwidth.get('total_formatted', '0 B')
    html += f"""
            </div>
            <div class="insight-card">
                <div class="insight-title">Bandwidth Consumed</div>
                <div style="font-size: 1.8em; font-weight: 700; color: #667eea; margin: 10px 0;">{total_bandwidth}</div>
                <div style="color: #718096; margin-bottom: 12px;">Total data transferred to AI bots</div>
    """
    for bot_bw in bandwidth.get('by_bot', [])[:3]:
        html += f'<div class="insight-stat"><span class="insight-label">{bot_bw["type"]}</span><span class="insight-value">{bot_bw["formatted"]}</span></div>'

    html += """
            </div>
        </div>
    </div>
    """

    # SEO Health Indicators (detailed)
    seo_health = report.get('seo_health', {})
    if seo_health and seo_health.get('issues'):
        html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🔍</span>SEO Health Indicators</h2></div>
        <div style="background: #fff5f5; border: 1px solid #f56565; border-radius: 8px; padding: 15px;">
            <strong style="color: #c53030;">Issues Detected:</strong>
            <ul style="margin-top: 10px; margin-left: 20px; color: #4a5568;">
        """
        for issue in seo_health.get('issues', []):
            html += f'<li>{issue}</li>'
        html += "</ul></div></div>"

    # Top URLs
    html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">📄</span>Top Requested URLs</h2></div>
        <div class="url-list">
    """
    for item in report.get('top_urls', [])[:10]:
        html += f'<div class="url-item"><div class="url-path">{item["url"]}</div><div class="url-count">{item["count"]:,}x</div></div>'
    html += "</div></div>"

    return html


# ============== TAB 6: ACTIONS ==============

def generate_actions_tab(report):
    """Generate Actions tab content."""
    html = ""

    # Issues & Failures
    html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">⚠️</span>Issues & Failures</h2></div>
        <h3 style="margin-bottom: 15px; color: #2d3748;">Top Failed URLs</h3>
        <div class="url-list">
    """
    for item in report.get('top_failed_urls', [])[:10]:
        html += f'<div class="url-item"><div class="url-path">{item["url"]}</div><div class="url-count" style="background: #fff5f5; color: #f56565;">{item["count"]:,}x</div></div>'
    html += "</div></div>"

    # Action Plan
    recommendations = report.get('recommendations', [])
    if recommendations:
        html += """
    <div class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🎯</span>Action Plan</h2></div>
        <div style="background: #edf2f7; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p style="color: #4a5568; line-height: 1.5;"><strong>Priority-ranked recommendations</strong> based on impact and severity. Start with HIGH priority items for maximum improvement.</p>
        </div>
        <div class="recommendations-grid">
        """
        for rec in recommendations[:8]:
            severity_lower = rec['severity'].lower()
            html += f"""
        <div class="recommendation {severity_lower}">
            <div class="rec-header">
                <div class="rec-title">{rec['title']}</div>
                <div class="rec-badge {severity_lower}">{rec['severity']}</div>
            </div>
            <div class="rec-description">{rec['description']}</div>
            <div class="rec-action"><strong>Action:</strong> {rec['action']}</div>
            <div class="rec-impact"><strong>Impact:</strong> {rec['impact']}</div>
        </div>
            """
        html += "</div></div>"

    return html


# ============== CHART SCRIPTS ==============

def generate_chart_scripts(report):
    """Generate all Chart.js scripts."""
    bot_names = [bot['type'] for bot in report['bot_statistics']]
    bot_counts = [bot['count'] for bot in report['bot_statistics']]
    success_rates = [bot['success_rate'] for bot in report['bot_statistics']]
    bar_colors = ['#48bb78' if rate >= 80 else '#ed8936' if rate >= 50 else '#f56565' for rate in success_rates]

    status_breakdown = report.get('status_breakdown', {})
    status_labels = ['2xx Success', '3xx Redirect', '4xx Client Error', '5xx Server Error']
    status_counts = [
        status_breakdown.get('2xx', {}).get('count', 0),
        status_breakdown.get('3xx', {}).get('count', 0),
        status_breakdown.get('4xx', {}).get('count', 0),
        status_breakdown.get('5xx', {}).get('count', 0)
    ]
    status_colors = ['#48bb78', '#ed8936', '#f56565', '#9f7aea']

    content_types = report.get('content_types', [])
    content_labels = [ct['type'] for ct in content_types[:6]]
    content_counts = [ct['count'] for ct in content_types[:6]]

    scripts = []

    # Bot Distribution Chart
    scripts.append(f"""
        new Chart(document.getElementById('botDistributionChart'), {{
            type: 'doughnut',
            data: {{
                labels: {bot_names},
                datasets: [{{
                    data: {bot_counts},
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{ display: true, text: 'Bot Traffic Distribution', font: {{ size: 14, weight: 'bold' }} }},
                    legend: {{ position: 'bottom', labels: {{ padding: 12, font: {{ size: 11 }} }} }}
                }},
                cutout: '60%'
            }}
        }});
    """)

    # Bot Success Chart
    scripts.append(f"""
        new Chart(document.getElementById('botSuccessChart'), {{
            type: 'bar',
            data: {{
                labels: {bot_names},
                datasets: [{{
                    label: 'Success Rate (%)',
                    data: {success_rates},
                    backgroundColor: {bar_colors},
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, max: 100, ticks: {{ callback: function(value) {{ return value + '%'; }} }} }}
                }},
                plugins: {{
                    title: {{ display: true, text: 'Bot Success Rates', font: {{ size: 14, weight: 'bold' }} }},
                    legend: {{ display: false }}
                }}
            }}
        }});
    """)

    # Status Code Chart
    scripts.append(f"""
        new Chart(document.getElementById('statusCodeChart'), {{
            type: 'doughnut',
            data: {{
                labels: {status_labels},
                datasets: [{{
                    data: {status_counts},
                    backgroundColor: {status_colors},
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{ display: true, text: 'HTTP Status Code Distribution', font: {{ size: 14, weight: 'bold' }} }},
                    legend: {{ position: 'bottom', labels: {{ padding: 12, font: {{ size: 11 }} }} }}
                }},
                cutout: '55%'
            }}
        }});
    """)

    # Content Type Chart
    scripts.append(f"""
        new Chart(document.getElementById('contentTypeChart'), {{
            type: 'bar',
            data: {{
                labels: {content_labels},
                datasets: [{{
                    label: 'Requests',
                    data: {content_counts},
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#f56565'],
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {{
                    x: {{ beginAtZero: true }}
                }},
                plugins: {{
                    title: {{ display: true, text: 'Content Types Requested by Bots', font: {{ size: 14, weight: 'bold' }} }},
                    legend: {{ display: false }}
                }}
            }}
        }});
    """)

    # Referrer Source Chart (if data exists)
    referrer_analysis = report.get('referrer_analysis', {})
    if referrer_analysis and referrer_analysis.get('source_breakdown'):
        ref_labels = [s['source'] for s in referrer_analysis['source_breakdown']]
        ref_counts = [s['count'] for s in referrer_analysis['source_breakdown']]
        scripts.append(f"""
        new Chart(document.getElementById('referrerSourceChart'), {{
            type: 'pie',
            data: {{
                labels: {ref_labels},
                datasets: [{{
                    data: {ref_counts},
                    backgroundColor: ['#667eea', '#4facfe', '#f093fb'],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{ display: true, text: 'Referrer Sources', font: {{ size: 14, weight: 'bold' }} }},
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        """)

    # Site Structure Charts (if data exists)
    site_structure = report.get('site_structure', {})
    if site_structure and site_structure.get('section_breakdown'):
        section_labels = [s['section'] for s in site_structure['section_breakdown'][:8]]
        section_counts = [s['count'] for s in site_structure['section_breakdown'][:8]]
        scripts.append(f"""
        new Chart(document.getElementById('sectionHitsChart'), {{
            type: 'bar',
            data: {{
                labels: {section_labels},
                datasets: [{{
                    label: 'Hits',
                    data: {section_counts},
                    backgroundColor: '#667eea',
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    title: {{ display: true, text: 'Section Hits', font: {{ size: 14, weight: 'bold' }} }},
                    legend: {{ display: false }}
                }}
            }}
        }});
        """)

    if site_structure and site_structure.get('depth_distribution'):
        depth_labels = [d['label'] for d in site_structure['depth_distribution']]
        depth_counts = [d['count'] for d in site_structure['depth_distribution']]
        scripts.append(f"""
        new Chart(document.getElementById('crawlDepthChart'), {{
            type: 'bar',
            data: {{
                labels: {depth_labels},
                datasets: [{{
                    label: 'Requests',
                    data: {depth_counts},
                    backgroundColor: '#764ba2',
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{ display: true, text: 'Crawl Depth Distribution', font: {{ size: 14, weight: 'bold' }} }},
                    legend: {{ display: false }}
                }}
            }}
        }});
        """)

    return '\n'.join(scripts)


# ============== MAIN GENERATOR ==============

def generate_html_report(report, output_file='ai_bot_report.html', ignore_homepage_redirects=True):
    """Generate the complete HTML report."""
    success_rate = report.get('overall_success_rate', 0)
    health_label, health_class, _ = get_health_status(success_rate)
    critical_issues = sum(1 for rec in report.get('recommendations', []) if rec['severity'] == 'HIGH')

    # Generate all tab contents
    overview_content = generate_overview_tab(report)
    traffic_content = generate_traffic_tab(report)
    crawl_content = generate_crawl_tab(report)
    bots_content = generate_bots_tab(report)
    technical_content = generate_technical_tab(report)
    actions_content = generate_actions_tab(report)
    chart_scripts = generate_chart_scripts(report)

    html = HTML_TEMPLATE.format(
        health_status=health_label,
        health_class=health_class,
        total_requests=f"{report.get('total_requests', 0):,}",
        success_rate=f"{success_rate:.1f}",
        issues_count=critical_issues,
        issues_class='critical' if critical_issues > 0 else 'good',
        overview_content=overview_content,
        traffic_content=traffic_content,
        crawl_content=crawl_content,
        bots_content=bots_content,
        technical_content=technical_content,
        actions_content=actions_content,
        chart_scripts=chart_scripts,
        generated_date=datetime.now().strftime('%B %d, %Y at %H:%M')
    )

    from pathlib import Path
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✓ Enhanced tabbed HTML report generated: {output_file}")
    return str(output_path)


if __name__ == '__main__':
    print("This module generates tabbed UX HTML reports")
