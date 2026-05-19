"""
======================================================
🔹 report_utils.py — Reporting and Summary Utilities
======================================================
Generates structured reports (CSV/HTML/Console) for:
 - Config diff results
 - Sanity test results
 - Regression suite outcomes

Used by:
 - compare_config.py
 - run_sanity.py
 - run_regression.py
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from plugins.helpers.genie_utils import summarize_diff


console = Console()


# ----------------------------------------------------
# 🔹 Save Results to CSV
# ----------------------------------------------------
def save_results_to_csv(results, filename="results/report_summary.csv", include_timestamp=True):
    """
    Save Nornir task results to CSV format.
    Each row: host, status, message.
    """
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        headers = ["Host", "Status", "Message"]
        if include_timestamp:
            headers.append("Timestamp")
        writer.writerow(headers)

        for host, result in results.items():
            status = "PASS" if not result.failed else "FAIL"
            msg = str(result.result)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [host, status, msg]
            if include_timestamp:
                row.append(timestamp)
            writer.writerow(row)

    console.print(f"📊 CSV report saved: [green]{output_path}[/green]")
    return str(output_path)


# ----------------------------------------------------
# 🔹 Generate HTML Summary Report
# ----------------------------------------------------
def generate_html_report(results, title="NX-OS Automation Report", output_file="results/report.html"):
    """
    Generate a simple HTML summary report for task outcomes.
    """
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    html = [
        "<html><head>",
        f"<title>{title}</title>",
        "<style>",
        "body { font-family: Arial; background-color: #f8f9fa; padding: 20px; }",
        "table { border-collapse: collapse; width: 100%; }",
        "th, td { border: 1px solid #ddd; padding: 8px; }",
        "th { background-color: #4CAF50; color: white; }",
        "tr:nth-child(even){background-color: #f2f2f2;}",
        "</style></head><body>",
        f"<h2>{title}</h2>",
        f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        "<table><tr><th>Host</th><th>Status</th><th>Message</th></tr>"
    ]

    for host, result in results.items():
        status = "PASS" if not result.failed else "FAIL"
        color = "#28a745" if status == "PASS" else "#dc3545"
        html.append(
            f"<tr><td>{host}</td><td style='color:{color}; font-weight:bold'>{status}</td><td>{result.result}</td></tr>"
        )

    html.append("</table></body></html>")

    Path(output_file).write_text("\n".join(html), encoding="utf-8")
    console.print(f"🧾 HTML report generated: [green]{output_file}[/green]")
    return str(output_file)


# ----------------------------------------------------
# 🔹 Display Console Table Summary
# ----------------------------------------------------
def display_console_summary(results, title="Task Summary"):
    """
    Print a pretty console table using rich.
    """
    table = Table(title=title, show_lines=True)
    table.add_column("Host", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Message", style="white")

    pass_count, fail_count = 0, 0
    for host, result in results.items():
        status = "PASS" if not result.failed else "FAIL"
        color = "green" if status == "PASS" else "red"
        if status == "PASS":
            pass_count += 1
        else:
            fail_count += 1
        table.add_row(host, f"[{color}]{status}[/{color}]", str(result.result))

    console.print(table)
    console.print(f"✅ Passed: [green]{pass_count}[/green] | ❌ Failed: [red]{fail_count}[/red]")


# ----------------------------------------------------
# 🔹 Generate Config Diff Summary
# ----------------------------------------------------
def generate_diff_summary(diff_dir="results/diffs", output_csv="results/diff_summary.csv"):
    """
    Scan all diff files, summarize drift counts, and save to CSV.
    """
    diff_path = Path(diff_dir)
    if not diff_path.exists():
        console.print(f"⚠ Diff directory not found: {diff_path}")
        return None

    rows = []
    for file in diff_path.glob("*_diff.txt"):
        diff_text = file.read_text(encoding="utf-8")
        summary = summarize_diff(diff_text)
        rows.append({
            "Device": file.stem.replace("_diff", ""),
            **summary
        })

    if not rows:
        console.print("✅ No drift detected across devices.")
        return None

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    console.print(f"📈 Drift summary saved to: [green]{output_csv}[/green]")
    return str(output_csv)
