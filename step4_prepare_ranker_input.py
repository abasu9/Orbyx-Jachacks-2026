#!/usr/bin/env python3
"""
Step 4: Prepare Employee Ranker Input

Transforms GitHub-derived employee features into the CSV format
required by employee_ranker.py.
"""

import csv
import json
import os
import sys


def load_features():
    """
    Load employee features from Step 3 output.
    
    Returns:
        dict: Employee features
    """
    print("Loading employee features...")
    
    if not os.path.exists("step3_employee_features.json"):
        print("ERROR: step3_employee_features.json not found")
        sys.exit(1)
    
    try:
        with open("step3_employee_features.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  Loaded data for {len(data)} employees")
        return data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse step3_employee_features.json: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load step3_employee_features.json: {e}")
        sys.exit(1)


def compute_ap(employee_features):
    """
    Compute AP score from GitHub activity metrics.
    
    AP is computed as a weighted combination of normalized activity components,
    then scaled to range [0, 2].
    
    Args:
        employee_features: Dictionary containing employee metrics
    
    Returns:
        float: AP score in range [0, 2]
    """
    commit_metrics = employee_features.get("commit_metrics", {})
    pr_metrics = employee_features.get("pr_metrics", {})
    review_metrics = employee_features.get("review_metrics", {})
    
    # Extract raw values with defaults
    total_commits = commit_metrics.get("total_commits", 0)
    active_days = commit_metrics.get("active_days", 0)
    prs_opened = pr_metrics.get("prs_opened", 0)
    prs_merged = pr_metrics.get("prs_merged", 0)
    reviews_given = review_metrics.get("reviews_given", 0)
    
    # Normalize components to [0, 1]
    commit_component = min(total_commits / 50.0, 1.0)
    pr_component = min(prs_opened / 20.0, 1.0)
    merge_component = min(prs_merged / 15.0, 1.0)
    review_component = min(reviews_given / 20.0, 1.0)
    consistency_component = min(active_days / 60.0, 1.0)
    
    # Compute weighted raw AP score
    raw_ap_score = (
        0.30 * commit_component +
        0.20 * pr_component +
        0.20 * merge_component +
        0.15 * review_component +
        0.15 * consistency_component
    )
    
    # Scale to [0, 2] and round
    ap = round(raw_ap_score * 2, 2)
    
    # Clamp to [0, 2]
    ap = max(0.0, min(2.0, ap))
    
    return ap


def compute_pip_count(employee_features):
    """
    Compute pip_count based on low activity signals.
    
    Args:
        employee_features: Dictionary containing employee metrics
    
    Returns:
        int: pip_count (0, 1, or 2)
    """
    commit_metrics = employee_features.get("commit_metrics", {})
    pr_metrics = employee_features.get("pr_metrics", {})
    review_metrics = employee_features.get("review_metrics", {})
    derived_metrics = employee_features.get("derived_metrics", {})
    
    # Extract raw values with defaults
    total_commits = commit_metrics.get("total_commits", 0)
    prs_opened = pr_metrics.get("prs_opened", 0)
    reviews_given = review_metrics.get("reviews_given", 0)
    activity_score_proxy = derived_metrics.get("activity_score_proxy", 0)
    
    # Apply pip_count rules
    if total_commits < 5 and prs_opened == 0 and reviews_given == 0:
        return 2
    elif total_commits < 10 or activity_score_proxy < 15:
        return 1
    else:
        return 0


def build_ranker_input_rows(features_data):
    """
    Build rows for employee ranker input CSV.
    
    Args:
        features_data: Dictionary of employee features
    
    Returns:
        list: List of dictionaries with employee_id, employee_name, AP, pip_count
    """
    print("\nBuilding ranker input rows...")
    
    rows = []
    
    # Sort employees alphabetically by name
    sorted_employees = sorted(features_data.keys())
    
    # Assign sequential employee IDs
    for idx, employee_name in enumerate(sorted_employees, start=1):
        employee_features = features_data[employee_name]
        
        # Compute AP and pip_count
        ap = compute_ap(employee_features)
        pip_count = compute_pip_count(employee_features)
        
        rows.append({
            "employee_id": idx,
            "employee_name": employee_name,
            "AP": ap,
            "pip_count": pip_count
        })
        
        print(f"  {employee_name}: AP={ap}, pip_count={pip_count}")
    
    return rows


def save_output_csv(rows):
    """
    Save ranker input rows to CSV file.
    
    Args:
        rows: List of dictionaries with employee data
    """
    print("\nSaving output...")
    
    with open("employee_ranker_input.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["employee_id", "employee_name", "AP", "pip_count"])
        writer.writeheader()
        writer.writerows(rows)
    
    print("  Saved employee_ranker_input.csv")


def main():
    """Main execution function."""
    print("="*60)
    print("Prepare Employee Ranker Input - Step 4")
    print("="*60 + "\n")
    
    # Step 1: Load features
    features_data = load_features()
    
    if not features_data:
        print("ERROR: No employee data available")
        sys.exit(1)
    
    # Step 2: Build ranker input rows
    rows = build_ranker_input_rows(features_data)
    
    # Step 3: Save output CSV
    save_output_csv(rows)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total employees processed: {len(rows)}")
    print(f"Output file: employee_ranker_input.csv")
    print("\nThis file can now be used with employee_ranker.py:")
    print("  python3 employee_ranker.py employee_ranker_input.csv ranked_output.csv")
    print("="*60)


if __name__ == "__main__":
    main()
