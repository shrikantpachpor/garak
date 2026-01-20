"""Compare two garak reports to verify structural equivalence.

This script validates that two reports (e.g., original vs modified tool) have:
- Same probe order
- Consistent run_id format
- Matching score calculation logic
- Same detection behavior

Score variance is expected due to LLM non-determinism.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def parse_report(report_path: Path) -> Dict:
    """Parse JSONL report file."""
    records = []
    with open(report_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    return {
        "setup": next((r for r in records if r.get("entry_type") == "start_run setup"), None),
        "init": next((r for r in records if r.get("entry_type") == "init"), None),
        "attempts": [r for r in records if r.get("entry_type") == "attempt"],
        "evals": [r for r in records if r.get("entry_type") == "eval"],
        "digest": next((r for r in records if r.get("entry_type") == "digest"), None),
    }


def parse_hitlog(hitlog_path: Path) -> List[Dict]:
    """Parse hitlog JSONL file."""
    hits = []
    if not hitlog_path.exists():
        return hits
    
    with open(hitlog_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                hits.append(json.loads(line))
    return hits


def validate_run_id_consistency(report: Dict, hits: List[Dict]) -> Tuple[bool, str]:
    """Verify run_id is consistent across report and hitlog."""
    run_id = report["init"]["run"]
    
    # If no hitlog, can't validate consistency
    if not hits:
        return True, f"No hitlog available (run_id: {run_id})"
    
    # Check hitlog run_ids
    hitlog_run_ids = set(hit["run_id"] for hit in hits)
    
    if len(hitlog_run_ids) != 1:
        return False, f"Multiple run_ids in hitlog: {hitlog_run_ids}"
    
    hitlog_run_id = hitlog_run_ids.pop()
    
    # Check format consistency (should be UUID, not full garak-run-... format)
    if hitlog_run_id.startswith("garak-run-"):
        return False, f"Hitlog uses full run_id format: {hitlog_run_id}"
    
    if hitlog_run_id != run_id:
        return False, f"Run ID mismatch: report={run_id}, hitlog={hitlog_run_id}"
    
    return True, f"Run ID consistent: {run_id}"


def validate_probe_order(report: Dict) -> Tuple[bool, str]:
    """Verify probe order matches probe_spec."""
    probe_spec = report["setup"].get("plugins.probe_spec", "")
    expected_order = [p.strip() for p in probe_spec.split(",")]
    
    # Check digest order
    digest = report["digest"]
    if not digest:
        return False, "No digest found in report"
    
    actual_order = []
    eval_section = digest["eval"]
    
    for group in eval_section.values():
        for key in group.keys():
            if key != "_summary" and "." in key:
                actual_order.append(key)
    
    if actual_order != expected_order:
        return False, f"Order mismatch: expected {expected_order}, got {actual_order}"
    
    return True, f"Probe order correct: {expected_order}"


def validate_seq_numbering(report: Dict) -> Tuple[bool, str]:
    """Verify seq numbering resets per probe."""
    attempts = report["attempts"]
    
    # Group by probe - each probe should have its own seq sequence
    probe_attempts = {}
    for attempt in attempts:
        probe = attempt["probe_classname"]
        if probe not in probe_attempts:
            probe_attempts[probe] = []
        probe_attempts[probe].append(attempt["seq"])
    
    # Check each probe starts at 0 and sequences are valid
    for probe, seqs in probe_attempts.items():
        if min(seqs) != 0:
            return False, f"{probe} seq doesn't start at 0: min={min(seqs)}"
        
        if max(seqs) != len(set(seqs)) - 1:
            return False, f"{probe} seq numbering gaps or duplicates: {sorted(set(seqs))}"
        
        # Check that seqs are contiguous 0..N
        expected = set(range(len(set(seqs))))
        if set(seqs) != expected:
            return False, f"{probe} seqs not contiguous: got {sorted(set(seqs))}, expected {sorted(expected)}"
    
    return True, "Seq numbering correct (resets per probe)"


def validate_score_accuracy(report: Dict, hits: List[Dict]) -> Tuple[bool, str]:
    """Verify digest scores match hitlog counts."""
    attempts = report["attempts"]
    digest = report["digest"]
    
    if not digest:
        return False, "No digest found"
    
    # If no hitlog, can't validate
    if not hits:
        return True, "No hitlog available (scores not validated)"
    
    # Calculate expected scores
    probe_totals = {}
    probe_hits = {}
    
    for attempt in attempts:
        probe = attempt["probe_classname"]
        if probe not in probe_totals:
            probe_totals[probe] = 0
        probe_totals[probe] += 1
    
    for hit in hits:
        probe = hit["probe"]
        if probe not in probe_hits:
            probe_hits[probe] = 0
        probe_hits[probe] += 1
    
    # Compare with digest scores
    eval_section = digest["eval"]
    issues = []
    
    for group in eval_section.values():
        for probe_key, probe_data in group.items():
            if probe_key == "_summary" or "." not in probe_key:
                continue
            
            # Find matching probe in attempts
            matching_probe = None
            for p in probe_totals.keys():
                if probe_key in p or p in probe_key:
                    matching_probe = p
                    break
            
            if not matching_probe:
                continue
            
            total = probe_totals[matching_probe]
            hits_count = probe_hits.get(probe_key, 0)
            
            # Score = pass rate = 1 - (hits / total)
            expected_score = 1.0 - (hits_count / total)
            actual_score = probe_data["_summary"]["probe_score"]
            
            if abs(actual_score - expected_score) > 0.01:
                issues.append(f"{probe_key}: expected {expected_score:.2f}, got {actual_score:.2f} (hits={hits_count}/{total})")
    
    if issues:
        return False, f"Score mismatches: {'; '.join(issues)}"
    
    return True, "Scores match hitlog counts"


def compare_reports(report1_path: Path, report2_path: Path) -> Dict:
    """Compare two reports and identify differences."""
    report1 = parse_report(report1_path)
    report2 = parse_report(report2_path)
    
    hitlog1_path = report1_path.parent / report1_path.name.replace('.report.jsonl', '.hitlog.jsonl')
    hitlog2_path = report2_path.parent / report2_path.name.replace('.report.jsonl', '.hitlog.jsonl')
    
    hits1 = parse_hitlog(hitlog1_path)
    hits2 = parse_hitlog(hitlog2_path)
    
    results = {
        "report1": {
            "path": str(report1_path),
            "run_id": report1["init"]["run"],
            "attempts": len(report1["attempts"]),
            "hits": len(hits1),
        },
        "report2": {
            "path": str(report2_path),
            "run_id": report2["init"]["run"],
            "attempts": len(report2["attempts"]),
            "hits": len(hits2),
        },
        "structural_checks": {},
        "differences": {}
    }
    
    # Structural validation for both reports
    for report_key, report_data, hits in [("report1", report1, hits1), ("report2", report2, hits2)]:
        checks = {}
        
        checks["run_id_consistency"] = validate_run_id_consistency(report_data, hits)
        checks["probe_order"] = validate_probe_order(report_data)
        checks["seq_numbering"] = validate_seq_numbering(report_data)
        checks["score_accuracy"] = validate_score_accuracy(report_data, hits)
        
        results["structural_checks"][report_key] = checks
    
    # Compare probe orders
    probe_spec1 = report1["setup"].get("plugins.probe_spec", "")
    probe_spec2 = report2["setup"].get("plugins.probe_spec", "")
    
    if probe_spec1 != probe_spec2:
        results["differences"]["probe_spec"] = {
            "report1": probe_spec1,
            "report2": probe_spec2
        }
    
    # Compare scores (note: variance is expected)
    digest1 = report1["digest"]
    digest2 = report2["digest"]
    
    if digest1 and digest2:
        score_diffs = []
        
        for group_name in digest1["eval"].keys():
            if group_name not in digest2["eval"]:
                continue
            
            group1 = digest1["eval"][group_name]
            group2 = digest2["eval"][group_name]
            
            for probe_key in group1.keys():
                if probe_key == "_summary" or probe_key not in group2:
                    continue
                
                score1 = group1[probe_key]["_summary"]["probe_score"]
                score2 = group2[probe_key]["_summary"]["probe_score"]
                
                if abs(score1 - score2) > 0.01:
                    score_diffs.append({
                        "probe": probe_key,
                        "report1_score": score1,
                        "report2_score": score2,
                        "difference": abs(score1 - score2)
                    })
        
        if score_diffs:
            results["differences"]["scores"] = score_diffs
            results["differences"]["scores_note"] = "Score variance is expected due to LLM non-determinism"
    
    return results


def print_report(results: Dict):
    """Print comparison results in readable format."""
    print("=" * 80)
    print("GARAK REPORT COMPARISON")
    print("=" * 80)
    
    print("\n📊 REPORT SUMMARY")
    print("-" * 80)
    for key in ["report1", "report2"]:
        print(f"\n{key.upper()}:")
        print(f"  Path: {results[key]['path']}")
        print(f"  Run ID: {results[key]['run_id']}")
        print(f"  Attempts: {results[key]['attempts']}")
        print(f"  Hits: {results[key]['hits']}")
    
    print("\n\n✅ STRUCTURAL VALIDATION")
    print("-" * 80)
    
    all_passed = True
    
    for report_key in ["report1", "report2"]:
        print(f"\n{report_key.upper()}:")
        checks = results["structural_checks"][report_key]
        
        for check_name, (passed, message) in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}: {message}")
            if not passed:
                all_passed = False
    
    print("\n\n🔍 DIFFERENCES")
    print("-" * 80)
    
    if "differences" in results and results["differences"]:
        diffs = results["differences"]
        
        if "probe_spec" in diffs:
            print("\n⚠️  Probe Spec Mismatch:")
            print(f"  Report 1: {diffs['probe_spec']['report1']}")
            print(f"  Report 2: {diffs['probe_spec']['report2']}")
        
        if "scores" in diffs:
            print("\n📈 Score Differences (Expected due to LLM variance):")
            for diff in diffs["scores"]:
                print(f"  • {diff['probe']}:")
                print(f"    Report 1: {diff['report1_score']:.2f}")
                print(f"    Report 2: {diff['report2_score']:.2f}")
                print(f"    Difference: {diff['difference']:.2f}")
            print(f"\n  Note: {diffs.get('scores_note', '')}")
    else:
        print("\n✓ No structural differences found")
    
    print("\n" + "=" * 80)
    
    if all_passed:
        print("✅ ALL STRUCTURAL CHECKS PASSED")
    else:
        print("❌ SOME STRUCTURAL CHECKS FAILED")
    
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_reports.py <report1.jsonl> <report2.jsonl>")
        sys.exit(1)
    
    report1_path = Path(sys.argv[1])
    report2_path = Path(sys.argv[2])
    
    if not report1_path.exists():
        print(f"Error: {report1_path} not found")
        sys.exit(1)
    
    if not report2_path.exists():
        print(f"Error: {report2_path} not found")
        sys.exit(1)
    
    results = compare_reports(report1_path, report2_path)
    exit_code = print_report(results)
    
    sys.exit(exit_code)
