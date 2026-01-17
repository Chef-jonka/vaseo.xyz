"""
Enhanced UX HTML Report Generator for AI Bot Traffic Analysis
User-first design with clear narrative flow
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
        .nav {{ position: sticky; top: 0; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); z-index: 1000; padding: 0 20px; }}
        .nav-container {{ max-width: 1400px; margin: 0 auto; display: flex; align-items: center; gap: 30px; padding: 15px 0; }}
        .nav-back {{ color: #667eea; text-decoration: none; font-size: 0.9em; font-weight: 500; padding: 8px 16px; border-radius: 6px; transition: all 0.2s; }}
        .nav-back:hover {{ background: #f7fafc; }}
        .nav-actions {{ display: flex; gap: 10px; }}
        .btn-print {{ background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em; font-weight: 500; transition: all 0.2s; }}
        .btn-print:hover {{ background: #5a67d8; }}
        @media print {{
            .nav, .footer {{ display: none !important; }}
            .container {{ max-width: 100%; padding: 0; }}
            .section {{ break-inside: avoid; box-shadow: none; border: 1px solid #e2e8f0; }}
            body {{ background: white; }}
        }}
        .nav-logo {{ font-size: 1.3em; font-weight: 700; color: #667eea; }}
        .nav-links {{ display: flex; gap: 5px; flex: 1; }}
        .nav-link {{ padding: 8px 16px; border-radius: 6px; cursor: pointer; transition: all 0.2s; font-size: 0.9em; color: #4a5568; text-decoration: none; }}
        .nav-link:hover {{ background: #f7fafc; color: #667eea; }}
        .nav-link.active {{ background: #667eea; color: white; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 20px; text-align: center; }}
        .header h1 {{ font-size: 3em; margin-bottom: 10px; font-weight: 700; }}
        .header p {{ font-size: 1.3em; opacity: 0.9; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 40px 20px; }}
        .section {{ background: white; border-radius: 12px; padding: 40px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .section-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 15px; border-bottom: 3px solid #667eea; }}
        .section-title {{ font-size: 2em; color: #2d3748; display: flex; align-items: center; gap: 15px; }}
        .section-icon {{ font-size: 1.2em; }}
        .exec-summary {{ background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%); border-left: 5px solid #667eea; }}
        .health-status {{ display: flex; align-items: center; gap: 20px; padding: 20px; background: white; border-radius: 8px; margin-bottom: 20px; }}
        .health-icon {{ font-size: 3em; }}
        .health-info {{ flex: 1; }}
        .health-label {{ font-size: 0.9em; color: #718096; margin-bottom: 5px; }}
        .health-value {{ font-size: 2em; font-weight: 700; }}
        .health-value.good {{ color: #48bb78; }}
        .health-value.warning {{ color: #ed8936; }}
        .health-value.critical {{ color: #f56565; }}
        .quick-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .quick-stat {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .quick-stat-label {{ font-size: 0.85em; color: #718096; margin-bottom: 8px; }}
        .quick-stat-value {{ font-size: 1.8em; font-weight: 700; color: #2d3748; }}
        .bot-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .bot-table th {{ background: #f7fafc; padding: 15px; text-align: left; font-weight: 600; color: #4a5568; border-bottom: 2px solid #e2e8f0; }}
        .bot-table td {{ padding: 15px; border-bottom: 1px solid #e2e8f0; }}
        .bot-table tr:hover {{ background: #f7fafc; }}
        .bot-name {{ display: flex; align-items: center; gap: 10px; font-weight: 600; }}
        .status-indicator {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
        .status-indicator.good {{ background: #48bb78; }}
        .status-indicator.warning {{ background: #ed8936; }}
        .status-indicator.critical {{ background: #f56565; }}
        .progress-bar {{ width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin-top: 5px; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin: 30px 0; }}
        .chart-container {{ background: #f7fafc; border-radius: 8px; padding: 20px; height: 350px; }}
        .insights-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .insight-card {{ background: #f7fafc; border-radius: 8px; padding: 20px; border-top: 4px solid #667eea; }}
        .insight-title {{ font-weight: 700; font-size: 1.1em; color: #2d3748; margin-bottom: 15px; }}
        .insight-stat {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #e2e8f0; }}
        .insight-stat:last-child {{ border-bottom: none; }}
        .insight-label {{ color: #718096; }}
        .insight-value {{ font-weight: 700; color: #2d3748; }}
        .url-list {{ background: #f7fafc; border-radius: 8px; padding: 20px; margin-top: 20px; }}
        .url-item {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; background: white; border-radius: 6px; margin-bottom: 8px; font-family: 'Courier New', monospace; font-size: 0.9em; transition: transform 0.2s; }}
        .url-item:hover {{ transform: translateX(5px); }}
        .url-item:last-child {{ margin-bottom: 0; }}
        .url-path {{ color: #4a5568; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; margin-right: 20px; }}
        .url-count {{ color: #667eea; font-weight: 700; white-space: nowrap; background: #edf2f7; padding: 4px 12px; border-radius: 12px; }}
        .recommendations-grid {{ display: grid; gap: 15px; }}
        .recommendation {{ background: white; border-left: 5px solid #667eea; padding: 20px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform 0.2s, box-shadow 0.2s; }}
        .recommendation:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .recommendation.high {{ border-left-color: #f56565; background: #fff5f5; }}
        .recommendation.medium {{ border-left-color: #ed8936; background: #fffaf0; }}
        .recommendation.low {{ border-left-color: #48bb78; background: #f0fff4; }}
        .rec-header {{ display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px; }}
        .rec-title {{ font-size: 1.2em; font-weight: 700; color: #2d3748; flex: 1; }}
        .rec-badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; white-space: nowrap; margin-left: 10px; }}
        .rec-badge.high {{ background: #f56565; color: white; }}
        .rec-badge.medium {{ background: #ed8936; color: white; }}
        .rec-badge.low {{ background: #48bb78; color: white; }}
        .rec-description {{ color: #4a5568; margin-bottom: 12px; line-height: 1.6; }}
        .rec-action {{ background: white; padding: 12px; border-radius: 6px; margin-bottom: 10px; font-size: 0.95em; border-left: 3px solid #667eea; }}
        .rec-impact {{ font-size: 0.9em; color: #667eea; font-weight: 600; }}
        .comparison-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin: 20px 0; }}
        .comparison-title {{ font-size: 1.5em; font-weight: 700; margin-bottom: 20px; }}
        .comparison-items {{ display: flex; justify-content: space-around; text-align: center; gap: 20px; }}
        .comparison-item {{ flex: 1; }}
        .comparison-label {{ opacity: 0.9; margin-bottom: 10px; font-size: 1.1em; }}
        .comparison-value {{ font-size: 2.5em; font-weight: 700; margin: 10px 0; }}
        .comparison-subtitle {{ opacity: 0.85; font-size: 0.9em; }}
        .footer {{ background: white; padding: 40px 20px; text-align: center; color: #718096; font-size: 0.9em; border-top: 1px solid #e2e8f0; }}
        @media (max-width: 768px) {{ .nav-links {{ display: none; }} .charts-grid, .insights-grid, .quick-stats {{ grid-template-columns: 1fr; }} .comparison-items {{ flex-direction: column; }} }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="/dashboard" class="nav-back">← Back to Dashboard</a>
            <div class="nav-logo">🤖 LLM Acceptably Report</div>
            <div class="nav-links">
                <a href="#summary" class="nav-link">Summary</a>
                <a href="#bots" class="nav-link">Bots</a>
                <a href="#patterns" class="nav-link">Patterns</a>
                <a href="#behavior" class="nav-link">Behavior</a>
                <a href="#issues" class="nav-link">Issues</a>
                <a href="#actions" class="nav-link">Actions</a>
            </div>
            <div class="nav-actions">
                <button class="btn-print" onclick="window.print()">📄 Save as PDF</button>
            </div>
        </div>
    </nav>
    <div class="header">
        <h1>🤖 LLM Acceptably Report</h1>
        <p>AI Bot Traffic Intelligence Report</p>
    </div>
    <div class="container">
        {content_sections}
    </div>
    <div class="footer">
        <p>Generated on {generated_date}</p>
        <p style="margin-top: 10px;">LLM Acceptably Report by <a href="https://vaseo.xyz" target="_blank" style="color: #667eea;">Vaseo</a></p>
    </div>
    <script>
        {chart_scripts}
        const sections = document.querySelectorAll('.section');
        const navLinks = document.querySelectorAll('.nav-link');
        window.addEventListener('scroll', () => {{
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                if (pageYOffset >= sectionTop - 100) {{
                    current = section.getAttribute('id');
                }}
            }});
            navLinks.forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {{
                    link.classList.add('active');
                }}
            }});
        }});
        navLinks.forEach(link => {{
            link.addEventListener('click', (e) => {{
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
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

def generate_executive_summary(report):
    success_rate = report['overall_success_rate']
    health_label, health_class, health_icon = get_health_status(success_rate)
    top_bot = report['bot_statistics'][0] if report['bot_statistics'] else {'type': 'N/A'}
    critical_issues = sum(1 for rec in report.get('recommendations', []) if rec['severity'] == 'HIGH')
    top_action = report['recommendations'][0] if report.get('recommendations') else None
    
    html = f"""
    <div id="summary" class="section exec-summary">
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
                <div class="quick-stat-value" style="font-size: 1.3em;">{top_bot['type']}</div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-label">Critical Issues</div>
                <div class="quick-stat-value" style="color: {'#f56565' if critical_issues > 0 else '#48bb78'};">{critical_issues}</div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-label">Analysis Period</div>
                <div class="quick-stat-value" style="font-size: 1em;">{report['date_range']['start']}</div>
                <div style="font-size: 0.85em; color: #718096;">to {report['date_range']['end']}</div>
            </div>
        </div>
    """
    
    if top_action:
        html += f"""
        <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #f56565;">
            <div style="font-weight: 700; color: #2d3748; margin-bottom: 10px; font-size: 1.1em;">🎯 Top Priority Action</div>
            <div style="color: #4a5568; margin-bottom: 8px;">{top_action['title']}</div>
            <div style="color: #718096; font-size: 0.9em;">{top_action['description']} • Impact: {top_action['impact']}</div>
        </div>
        """
    
    html += "</div>"
    return html

def generate_bot_overview(report):
    html = """
    <div id="bots" class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🤖</span>Bot Overview</h2></div>
        <div class="charts-grid">
            <div class="chart-container"><canvas id="botDistributionChart"></canvas></div>
            <div class="chart-container"><canvas id="botSuccessChart"></canvas></div>
        </div>
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
    return html

def generate_patterns_section(report):
    time_analysis = report.get('time_analysis', {})
    comparisons = report.get('comparisons', {})
    if not time_analysis:
        return ""
    
    html = f"""
    <div id="patterns" class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">⏰</span>Traffic Patterns</h2></div>
        <div class="insights-grid">
            <div class="insight-card">
                <div class="insight-title">⏰ Peak Activity</div>
                <div class="insight-stat"><span class="insight-label">Peak Hour:</span><span class="insight-value">{time_analysis.get('peak_hour', 'N/A')}</span></div>
                <div class="insight-stat"><span class="insight-label">Requests:</span><span class="insight-value">{time_analysis.get('peak_hour_count', 0):,}</span></div>
            </div>
            <div class="insight-card">
                <div class="insight-title">😴 Quiet Period</div>
                <div class="insight-stat"><span class="insight-label">Quiet Hour:</span><span class="insight-value">{time_analysis.get('quiet_hour', 'N/A')}</span></div>
                <div class="insight-stat"><span class="insight-label">Requests:</span><span class="insight-value">{time_analysis.get('quiet_hour_count', 0):,}</span></div>
            </div>
            <div class="insight-card">
                <div class="insight-title">📅 Busiest Day</div>
                <div class="insight-stat"><span class="insight-label">Day:</span><span class="insight-value">{time_analysis.get('busiest_day', 'N/A')}</span></div>
                <div class="insight-stat"><span class="insight-label">Requests:</span><span class="insight-value">{time_analysis.get('busiest_day_count', 0):,}</span></div>
            </div>
        </div>
    """
    
    if comparisons.get('bot_performance'):
        bp = comparisons['bot_performance']
        html += f"""
        <div class="comparison-box">
            <div class="comparison-title">🤖 Best vs Worst Performing Bots</div>
            <div class="comparison-items">
                <div class="comparison-item">
                    <div class="comparison-label">🏆 Best Performer</div>
                    <div class="comparison-value">{bp['best']['success_rate']}%</div>
                    <div class="comparison-subtitle">{bp['best']['name']}</div>
                </div>
                <div class="comparison-item">
                    <div class="comparison-label">📉 Performance Gap</div>
                    <div class="comparison-value">{bp['difference']}%</div>
                    <div class="comparison-subtitle">Difference</div>
                </div>
                <div class="comparison-item">
                    <div class="comparison-label">⚠️ Needs Improvement</div>
                    <div class="comparison-value">{bp['worst']['success_rate']}%</div>
                    <div class="comparison-subtitle">{bp['worst']['name']}</div>
                </div>
            </div>
        </div>
        """
    
    html += "</div>"
    return html

def generate_behavior_section(report):
    html = """
    <div id="behavior" class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">💡</span>Bot Behavior & Content</h2></div>
        <h3 style="margin-bottom: 20px; color: #2d3748;">Top Requested URLs</h3>
        <div class="url-list">
    """
    
    for item in report['top_urls'][:10]:
        html += f'<div class="url-item"><div class="url-path">{item["url"]}</div><div class="url-count">{item["count"]:,}x</div></div>'
    
    html += "</div></div>"
    return html

def generate_issues_section(report):
    html = """
    <div id="issues" class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">⚠️</span>Issues & Failures</h2></div>
        <h3 style="margin-bottom: 20px; color: #2d3748;">Top Failed URLs</h3>
        <div class="url-list">
    """
    
    for item in report['top_failed_urls'][:10]:
        html += f'<div class="url-item"><div class="url-path">{item["url"]}</div><div class="url-count" style="background: #fff5f5; color: #f56565;">{item["count"]:,}x</div></div>'
    
    html += "</div></div>"
    return html

def generate_actions_section(report):
    recommendations = report.get('recommendations', [])
    if not recommendations:
        return ""
    
    html = """
    <div id="actions" class="section">
        <div class="section-header"><h2 class="section-title"><span class="section-icon">🎯</span>Action Plan</h2></div>
        <div style="background: #edf2f7; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
            <p style="color: #4a5568; line-height: 1.6;"><strong>Priority-ranked recommendations</strong> based on impact and severity. Start with HIGH priority items for maximum improvement.</p>
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
            <div class="rec-action">💡 <strong>Action:</strong> {rec['action']}</div>
            <div class="rec-impact">📈 <strong>Impact:</strong> {rec['impact']}</div>
        </div>
        """
    
    html += "</div></div>"
    return html

def generate_chart_scripts(report):
    bot_names = [bot['type'] for bot in report['bot_statistics']]
    bot_counts = [bot['count'] for bot in report['bot_statistics']]
    success_rates = [bot['success_rate'] for bot in report['bot_statistics']]
    bar_colors = ['#48bb78' if rate >= 80 else '#ed8936' if rate >= 50 else '#f56565' for rate in success_rates]
    
    scripts = []
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
                    title: {{ display: true, text: 'Bot Traffic Distribution', font: {{ size: 16, weight: 'bold' }} }},
                    legend: {{ position: 'bottom', labels: {{ padding: 15, font: {{ size: 12 }} }} }}
                }},
                cutout: '60%'
            }}
        }});
    """)
    
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
                    title: {{ display: true, text: 'Bot Success Rates', font: {{ size: 16, weight: 'bold' }} }},
                    legend: {{ display: false }}
                }}
            }}
        }});
    """)
    
    return '\n'.join(scripts)

def generate_html_report(report, output_file='ai_bot_report.html', ignore_homepage_redirects=True):
    sections = []
    sections.append(generate_executive_summary(report))
    sections.append(generate_bot_overview(report))
    sections.append(generate_patterns_section(report))
    sections.append(generate_behavior_section(report))
    sections.append(generate_issues_section(report))
    sections.append(generate_actions_section(report))
    
    content_sections = '\n'.join(sections)
    chart_scripts = generate_chart_scripts(report)
    
    html = HTML_TEMPLATE.format(
        content_sections=content_sections,
        chart_scripts=chart_scripts,
        generated_date=datetime.now().strftime('%B %d, %Y at %H:%M')
    )
    
    from pathlib import Path
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✓ Enhanced UX HTML report generated: {output_file}")
    return str(output_path)

if __name__ == '__main__':
    print("This module generates UX-optimized HTML reports")
