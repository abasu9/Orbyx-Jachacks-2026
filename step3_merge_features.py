#!/usr/bin/env python3
"""
Step 3: Merge Employee Performance Features

Merges commit metrics (Step 1) and PR/review metrics (Step 2) into
a unified employee performance feature table.
"""

import csv
import json
import os
import sys
from copy import deepcopy


def load_step1_data():
    """
    Load commit metrics from Step 1 output.
    
    Returns:
        dict: Employee commit metrics
    """
    print("Loading Step 1 data (commit metrics)...")
    
    if not os.path.exists("output.json"):
        print("WARNING: output.json not found, using empty data")
        return {}
    
    try:
        with open("output.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  Loaded data for {len(data)} employees")
        return data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse output.json: {e}")
        return {}
    except Exception as e:
        print(f"ERROR: Failed to load output.json: {e}")
        return {}


def load_step2_data():
    """
    Load PR and review metrics from Step 2 output.
    
    Returns:
        dict: Employee PR and review metrics
    """
    print("Loading Step 2 data (PR/review metrics)...")
    
    if not os.path.exists("step2_pr_review_metrics.json"):
        print("WARNING: step2_pr_review_metrics.json not found, using empty data")
        return {}
    
    try:
        with open("step2_pr_review_metrics.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  Loaded data for {len(data)} employees")
        return data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse step2_pr_review_metrics.json: {e}")
        return {}
    except Exception as e:
        print(f"ERROR: Failed to load step2_pr_review_metrics.json: {e}")
        return {}


def normalize_missing_fields():
    """
    Get default values for missing fields.
    
    Returns:
        dict: Default values for all metric categories
    """
    return {
        "commit_metrics": {
            "total_commits": 0,
            "repos_contributed_to": 0,
            "active_days": 0,
            "last_commit_date": None,
            "commits_per_repo": {}
        },
        "pr_metrics": {
            "prs_opened": 0,
            "prs_merged": 0,
            "prs_closed_unmerged": 0,
            "draft_prs": 0,
            "repos_with_prs": 0,
            "avg_pr_additions": 0,
            "avg_pr_deletions": 0,
            "avg_pr_changed_files": 0,
            "avg_pr_comments": 0,
            "avg_pr_review_comments": 0,
            "avg_pr_merge_time_hours": 0,
            "last_pr_date": None
        },
        "review_metrics": {
            "reviews_given": 0,
            "approvals_given": 0,
            "change_requests_given": 0,
            "review_comments_left": 0,
            "unique_prs_reviewed": 0,
            "unique_repos_reviewed": 0,
            "last_review_date": None
        }
    }


def merge_employee_metrics(step1_data, step2_data):
    """
    Merge all metrics into one record per employee.
    
    Args:
        step1_data: Commit metrics from Step 1
        step2_data: PR/review metrics from Step 2
    
    Returns:
        dict: Merged metrics per employee
    """
    print("\nMerging employee metrics...")
    
    # Get union of all employees
    all_employees = set(step1_data.keys()) | set(step2_data.keys())
    print(f"  Found {len(all_employees)} unique employees")
    
    merged = {}
    defaults = normalize_missing_fields()
    
    for employee in all_employees:
        merged[employee] = {}
        
        # Merge commit metrics
        if employee in step1_data:
            commit_data = step1_data[employee]
            merged[employee]["commit_metrics"] = {
                "total_commits": commit_data.get("total_commits", 0),
                "repos_contributed_to": commit_data.get("repos_contributed_to", 0),
                "active_days": commit_data.get("active_days", 0),
                "last_commit_date": commit_data.get("last_commit_date"),
                "commits_per_repo": commit_data.get("commits_per_repo", {})
            }
        else:
            merged[employee]["commit_metrics"] = deepcopy(defaults["commit_metrics"])
        
        # Merge PR and review metrics
        if employee in step2_data:
            step2_employee = step2_data[employee]
            
            # PR metrics
            pr_data = step2_employee.get("pr_metrics", {})
            merged[employee]["pr_metrics"] = {
                "prs_opened": pr_data.get("prs_opened", 0),
                "prs_merged": pr_data.get("prs_merged", 0),
                "prs_closed_unmerged": pr_data.get("prs_closed_unmerged", 0),
                "draft_prs": pr_data.get("draft_prs", 0),
                "repos_with_prs": pr_data.get("repos_with_prs", 0),
                "avg_pr_additions": pr_data.get("avg_pr_additions", 0),
                "avg_pr_deletions": pr_data.get("avg_pr_deletions", 0),
                "avg_pr_changed_files": pr_data.get("avg_pr_changed_files", 0),
                "avg_pr_comments": pr_data.get("avg_pr_comments", 0),
                "avg_pr_review_comments": pr_data.get("avg_pr_review_comments", 0),
                "avg_pr_merge_time_hours": pr_data.get("avg_pr_merge_time_hours", 0),
                "last_pr_date": pr_data.get("last_pr_date")
            }
            
            # Review metrics
            review_data = step2_employee.get("review_metrics", {})
            merged[employee]["review_metrics"] = {
                "reviews_given": review_data.get("reviews_given", 0),
                "approvals_given": review_data.get("approvals_given", 0),
                "change_requests_given": review_data.get("change_requests_given", 0),
                "review_comments_left": review_data.get("review_comments_left", 0),
                "unique_prs_reviewed": review_data.get("unique_prs_reviewed", 0),
                "unique_repos_reviewed": review_data.get("unique_repos_reviewed", 0),
                "last_review_date": review_data.get("last_review_date")
            }
        else:
            merged[employee]["pr_metrics"] = deepcopy(defaults["pr_metrics"])
            merged[employee]["review_metrics"] = deepcopy(defaults["review_metrics"])
    
    return merged


def derive_additional_features(merged_data):
    """
    Compute derived features from merged metrics.
    
    Args:
        merged_data: Merged employee metrics
    
    Returns:
        dict: Merged data with derived metrics added
    """
    print("Deriving additional features...")
    
    for employee, data in merged_data.items():
        commit_metrics = data["commit_metrics"]
        pr_metrics = data["pr_metrics"]
        review_metrics = data["review_metrics"]
        
        # Extract values
        total_commits = commit_metrics["total_commits"]
        repos_contributed_to = commit_metrics["repos_contributed_to"]
        prs_opened = pr_metrics["prs_opened"]
        prs_merged = pr_metrics["prs_merged"]
        prs_closed_unmerged = pr_metrics["prs_closed_unmerged"]
        repos_with_prs = pr_metrics["repos_with_prs"]
        reviews_given = review_metrics["reviews_given"]
        approvals_given = review_metrics["approvals_given"]
        change_requests_given = review_metrics["change_requests_given"]
        
        # Compute derived metrics
        derived = {}
        
        # Total contribution repos (use max since we don't have repo lists to union)
        derived["total_contribution_repos"] = max(repos_contributed_to, repos_with_prs)
        
        # PR merge rate
        derived["pr_merge_rate"] = round(prs_merged / prs_opened, 2) if prs_opened > 0 else 0
        
        # PR close rate
        derived["pr_close_rate"] = round((prs_merged + prs_closed_unmerged) / prs_opened, 2) if prs_opened > 0 else 0
        
        # Review approval rate
        derived["review_approval_rate"] = round(approvals_given / reviews_given, 2) if reviews_given > 0 else 0
        
        # Review change request rate
        derived["review_change_request_rate"] = round(change_requests_given / reviews_given, 2) if reviews_given > 0 else 0
        
        # Commit to PR ratio
        derived["commit_to_pr_ratio"] = round(total_commits / prs_opened, 2) if prs_opened > 0 else total_commits
        
        # Activity score proxy
        derived["activity_score_proxy"] = total_commits + prs_opened + reviews_given
        
        data["derived_metrics"] = derived
    
    return merged_data


def save_output(merged_data):
    """
    Save merged feature table to JSON and CSV files.
    
    Args:
        merged_data: Merged employee metrics with derived features
    """
    print("\nSaving output...")
    
    # Save JSON
    with open("step3_employee_features.json", "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2)
    print("  Saved step3_employee_features.json")
    
    # Save CSV
    with open("step3_employee_features.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            "employee_name",
            "total_commits",
            "repos_contributed_to",
            "active_days",
            "last_commit_date",
            "prs_opened",
            "prs_merged",
            "prs_closed_unmerged",
            "draft_prs",
            "repos_with_prs",
            "avg_pr_additions",
            "avg_pr_deletions",
            "avg_pr_changed_files",
            "avg_pr_comments",
            "avg_pr_review_comments",
            "avg_pr_merge_time_hours",
            "last_pr_date",
            "reviews_given",
            "approvals_given",
            "change_requests_given",
            "review_comments_left",
            "unique_prs_reviewed",
            "unique_repos_reviewed",
            "last_review_date",
            "total_contribution_repos",
            "pr_merge_rate",
            "pr_close_rate",
            "review_approval_rate",
            "review_change_request_rate",
            "commit_to_pr_ratio",
            "activity_score_proxy"
        ])
        
        # Write data rows
        for employee in sorted(merged_data.keys()):
            data = merged_data[employee]
            cm = data["commit_metrics"]
            pm = data["pr_metrics"]
            rm = data["review_metrics"]
            dm = data["derived_metrics"]
            
            writer.writerow([
                employee,
                cm["total_commits"],
                cm["repos_contributed_to"],
                cm["active_days"],
                cm["last_commit_date"],
                pm["prs_opened"],
                pm["prs_merged"],
                pm["prs_closed_unmerged"],
                pm["draft_prs"],
                pm["repos_with_prs"],
                pm["avg_pr_additions"],
                pm["avg_pr_deletions"],
                pm["avg_pr_changed_files"],
                pm["avg_pr_comments"],
                pm["avg_pr_review_comments"],
                pm["avg_pr_merge_time_hours"],
                pm["last_pr_date"],
                rm["reviews_given"],
                rm["approvals_given"],
                rm["change_requests_given"],
                rm["review_comments_left"],
                rm["unique_prs_reviewed"],
                rm["unique_repos_reviewed"],
                rm["last_review_date"],
                dm["total_contribution_repos"],
                dm["pr_merge_rate"],
                dm["pr_close_rate"],
                dm["review_approval_rate"],
                dm["review_change_request_rate"],
                dm["commit_to_pr_ratio"],
                dm["activity_score_proxy"]
            ])
    
    print("  Saved step3_employee_features.csv")


def main():
    """Main execution function."""
    print("="*60)
    print("Employee Feature Merge - Step 3")
    print("="*60 + "\n")
    
    # Step 1: Load data from previous steps
    step1_data = load_step1_data()
    step2_data = load_step2_data()
    
    if not step1_data and not step2_data:
        print("\nERROR: No data available from previous steps")
        sys.exit(1)
    
    # Step 2: Merge employee metrics
    merged_data = merge_employee_metrics(step1_data, step2_data)
    
    # Step 3: Derive additional features
    merged_data = derive_additional_features(merged_data)
    
    # Step 4: Save output
    save_output(merged_data)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Employees in Step 1: {len(step1_data)}")
    print(f"Employees in Step 2: {len(step2_data)}")
    print(f"Total unique employees: {len(merged_data)}")
    print("\nEmployee Feature Summary:")
    for employee in sorted(merged_data.keys()):
        data = merged_data[employee]
        print(f"  {employee}:")
        print(f"    Commits: {data['commit_metrics']['total_commits']}")
        print(f"    PRs: {data['pr_metrics']['prs_opened']}")
        print(f"    Reviews: {data['review_metrics']['reviews_given']}")
        print(f"    Activity score: {data['derived_metrics']['activity_score_proxy']}")
    print("="*60)


if __name__ == "__main__":
    main()
