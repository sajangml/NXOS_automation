import sys
from pathlib import Path
from datetime import datetime
from nornir.core.task import Task, Result

# Keep imports portable for cloned showcase repositories.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
print(f"[DEBUG] Using PROJECT_ROOT: {PROJECT_ROOT}")

# Import semantic diff engine
from NXOS_AUTOMATION.plugins.semantic_diff.engine import generate_semantic_diff_report


# -------------------------------------------------------------------
# NORNIR TASK: compare configs
# -------------------------------------------------------------------
def compare_config(task: Task) -> Result:
    hostname = task.host.name.strip()
    env = task.host.get("env", "spineleaf")

    print(f"\n===== [START] Semantic Compare for {hostname} ({env}) =====\n")

    baseline_path = Path("output_builds") / env.upper() / f"{hostname}.cfg"
    running_path = Path("results") / "configs" / f"{hostname}.cfg"

    print(f"[DEBUG] Baseline path : {baseline_path}")
    print(f"[DEBUG] Running path  : {running_path}")

    if not baseline_path.exists():
        print(f"[ERROR] Baseline file NOT FOUND: {baseline_path}")
        return Result(host=task.host, failed=True, result="Baseline file missing")

    if not running_path.exists():
        configs_dir = Path("results") / "configs"
        fallback_match = next(
            (
                path for path in configs_dir.glob("*.cfg")
                if path.stem.strip() == hostname
            ),
            None,
        )
        if fallback_match is not None:
            print(f"[WARN] Running config resolved via fallback match: {fallback_match}")
            running_path = fallback_match
        else:
            print(f"[ERROR] Running config NOT FOUND: {running_path}")
            return Result(host=task.host, failed=True, result="Running config missing")

    print("[DEBUG] Reading baseline config...")
    baseline_text = baseline_path.read_text(encoding="utf-8")

    print("[DEBUG] Reading running config...")
    running_text = running_path.read_text(encoding="utf-8")

    # Generate semantic diff
    print("[DEBUG] Generating semantic diff...\n")
    report = generate_semantic_diff_report(
        baseline_text=baseline_text,
        running_text=running_text,
        hostname=hostname,
        env=env.upper(),
        baseline_path=str(baseline_path),
        running_path=str(running_path),
    )

    print("[DEBUG] Semantic diff generated successfully.")
    print("-----------------------------------------------")
    print(" SEMANTIC DIFF (PREVIEW — FIRST 20 LINES)")
    print("-----------------------------------------------")
    for line in report.splitlines()[:20]:
        print(line)

    if "No semantic differences" in report:
        print("[INFO] No semantic differences found.")

    # Save report
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("results") / "diffs" / env
    report_dir.mkdir(parents=True, exist_ok=True)

    report_file = report_dir / f"{hostname}_semantic_diff_{ts}.txt"
    print(f"\n[DEBUG] Saving diff report to: {report_file}")

    report_file.write_text(report, encoding="utf-8")

    print(f"\n===== [DONE] Semantic Compare for {hostname} =====\n")

    return Result(host=task.host, result=str(report_file))


# -------------------------------------------------------------------
# ALLOW EXECUTION VIA:
#   python -m NXOS_AUTOMATION.plugins.tasks.compare_config --env spineleaf
# -------------------------------------------------------------------
if __name__ == "__main__":
    from nornir import InitNornir
    from nornir_utils.plugins.functions import print_result
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="spineleaf")
    args = parser.parse_args()

    print(f"[MAIN] Starting Nornir semantic compare for env={args.env}")

    # Load absolute config.yaml
    CONFIG_FILE = PROJECT_ROOT / "NXOS_AUTOMATION" / "inventory" / "config.yaml"
    print(f"[DEBUG] Using config: {CONFIG_FILE}")

    nr = InitNornir(config_file=str(CONFIG_FILE))

    # Filter hosts by environment (must be in inventory)
    nr = nr.filter(env=args.env)

    result = nr.run(task=compare_config)
    print_result(result)
