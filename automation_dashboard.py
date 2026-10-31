"""Dashboard for the web/API test-automation projects (YouTube, Google)."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import report_kit as rk


def build(root: Path, *, title: str, eyebrow: str, summary: str, repo: str, layers: dict[str, str], notes: list[str]) -> None:
    results = json.loads((root / "reports" / "results.json").read_text(encoding="utf-8"))
    tests = results["tests"]
    counts = Counter(t["status"] for t in tests)
    blocked = [t for t in tests if t["status"] == "skipped" and t["reason"].startswith("blocked")]
    not_configured = [t for t in tests if t["status"] == "skipped" and not t["reason"].startswith("blocked")]
    executed = [t for t in tests if t["status"] not in ("skipped",)]
    failed = [t for t in tests if t["status"] in ("failed", "error")]
    pass_rate = 100 * counts["passed"] / max(1, len(executed))

    if failed:
        verdict = (f"{len(failed)} failing check{'s' if len(failed) > 1 else ''}: investigate before relying on these services", "bad")
    elif blocked:
        verdict = (f"All executed checks pass · {len(blocked)} blocked by bot protection", "warn")
    else:
        verdict = ("All executed checks pass", "ok")

    by_layer = defaultdict(Counter)
    durations = defaultdict(list)
    for t in tests:
        by_layer[t["category"]][t["status"]] += 1
        if t["status"] == "passed":
            durations[t["category"]].append(t["duration"])

    body = rk.kpis([
        ("Checks", len(tests), f"{len(layers)} layers, {results['duration']:.0f}s run"),
        ("Pass rate", f"{pass_rate:.0f}%", f"{counts['passed']} of {len(executed)} executed", "ok" if not failed else "bad"),
        ("Failing", len(failed), "unexpected failures", "bad" if failed else "ok"),
        ("Blocked", len(blocked), "consent wall / bot check in CI", "warn" if blocked else "ok"),
        ("Not configured", len(not_configured), "need an API key secret", "warn" if not_configured else "ok"),
    ])
    body += rk.grid(
        rk.section("Results", rk.donut([
            ("Passed", counts["passed"], "var(--green)"),
            ("Failed", len(failed), "var(--red)"),
            ("Blocked", len(blocked), "var(--orange)"),
            ("Not configured", len(not_configured), "var(--line)"),
        ], center=f"{pass_rate:.0f}%", caption="pass rate")),
        rk.section("Average check time by layer", rk.bars(
            [(layer, round(sum(d) / len(d), 2)) for layer, d in durations.items() if d], unit=" s"),
            "Mean duration of passing checks; UI checks include browser start-up and page load."),
    )
    layer_rows = [
        [layer, desc, c["passed"], c["failed"] + c["error"], sum(1 for t in blocked if t["category"] == layer), sum(1 for t in not_configured if t["category"] == layer)]
        for layer, desc in layers.items() if (c := by_layer[layer]) or True
    ]
    body += rk.section("Coverage by layer", rk.table(["Layer", "What is checked", "Passed", "Failed", "Blocked", "Not configured"], layer_rows))
    if failed:
        body += rk.section("Failures", rk.table(["Check", "Layer", "Reason"], [[t["title"], t["category"], t["reason"]] for t in failed]))
    rows = [[t["title"], t["category"], t["severity"].title(), f"{t['duration']:.2f}s", rk.pill("blocked" if t in blocked else t["status"]), t["reason"] if t["status"] != "passed" else ""] for t in tests]
    body += rk.section("All checks", rk.table(["Check", "Layer", "Severity", "Time", "Result", "Note"], rows, {4}))
    body += rk.section("How to read this", "<ul>" + "".join(f"<li>{rk.esc(n)}</li>" for n in notes) + "</ul>")

    out = root / "site"
    rk.write(str(out / "index.html"), rk.page(title=title, eyebrow=eyebrow, summary=summary, body=body, repo=repo, verdict=verdict))
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"dashboard: {out / 'index.html'} ({counts['passed']} passed, {len(failed)} failed, {len(blocked)} blocked)")
