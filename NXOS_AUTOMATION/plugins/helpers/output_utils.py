from rich.console import Console
from rich.table import Table
import csv
from pathlib import Path

console = Console()

def display_console_summary(results, title="Sanity Results"):
    """Pretty console output using Rich."""
    table = Table(title=title)

    table.add_column("Host", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")

    for host, multi_result in results.items():
        result = multi_result[0].result if multi_result else "No result"
        status = "FAIL" if multi_result.failed else "OK"
        row = f"{status} | {result}"
        table.add_row(host, row)

    console.print(table)


def save_results_to_csv(results, filepath):
    """Save results to CSV."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Host", "Status", "Message"])

        for host, multi_result in results.items():
            status = "FAIL" if multi_result.failed else "OK"
            message = multi_result[0].result if multi_result else "No result"
            writer.writerow([host, status, message])

    return filepath
