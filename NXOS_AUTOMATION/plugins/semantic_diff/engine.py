# semantic_diff/engine.py

from datetime import datetime

from .normalize import normalize_config
from .parser import parse_config
from .domain_compare import compare_configs, SemanticDiff
from .report import render_human_report


def generate_semantic_diff_report(
    baseline_text: str,
    running_text: str,
    hostname: str,
    env: str,
    baseline_path: str,
    running_path: str,
) -> str:
    """
    High-level orchestration:
      - normalise raw text
      - parse into models
      - compute semantic diff
      - render final human-readable report
    """
    # 1) Normalise raw configs
    baseline_norm = normalize_config(baseline_text)
    running_norm = normalize_config(running_text)

    # DEBUG HOOK
    # print(f"[DEBUG] baseline_norm lines: {len(baseline_norm)}")
    # print(f"[DEBUG] running_norm lines: {len(running_norm)}")

    # Fast path: if normalized configs are identical, skip parse+compare.
    if baseline_norm == running_norm:
        now = datetime.now()
        return render_human_report(
            hostname=hostname,
            env=env,
            baseline_path=baseline_path,
            running_path=running_path,
            generated_at=now,
            diff=SemanticDiff(),
            baseline_model=None,
            running_model=None,
        )

    # 2) Parse into structured models
    baseline_model = parse_config(baseline_norm)
    running_model = parse_config(running_norm)

    # DEBUG HOOK
    # print("[DEBUG] Parsed baseline:", len(baseline_model.vlans), "vlans")
    # print("[DEBUG] Parsed running:", len(running_model.vlans), "vlans")
    # print("[DEBUG] Parsed baseline interfaces:", len(baseline_model.interfaces))
    # print("[DEBUG] Parsed running interfaces:", len(running_model.interfaces))

    # 3) Semantic diff
    semantic_diff = compare_configs(baseline_model, running_model)

    # 4) Render the new NX-OS formatted 3-section report
    now = datetime.now()
    return render_human_report(
        hostname=hostname,
        env=env,
        baseline_path=baseline_path,
        running_path=running_path,
        generated_at=now,
        diff=semantic_diff,
        baseline_model=baseline_model,
        running_model=running_model,
    )
