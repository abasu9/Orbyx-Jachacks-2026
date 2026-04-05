#!/usr/bin/env python3
"""
Step 2: GitHub Pull Request and Review Data Collection and Aggregation

Collects PR and review history from a GitHub organization and aggregates
performance metrics per employee.
"""

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

import requests


# Configuration
ORG_NAME = "orbyx-ai"
DAYS_BACK = 365

EMPLOYEE_MAP = {
    "abasu9": "Abhishek Basu",
    "soureeshdalal": "Soureesh Dalal",
    "Anand-SK": "Anand Singh",
    "ExperimenterX": "Bhavani Shankar",
    "vrbaghel": "Vinayak Baghel"
}


def get_headers():
    """
    Get GitHub API headers with authentication token.
    
    Returns:
        dict: Headers for GitHub API requests
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }


def discover_repos():
    """
    Fetch all repositories from the organization.
    
    Returns:
        list: List of repository names
    """
    repos = []
    url = f"https://api.github.com/orgs/{ORG_NAME}/repos"
    headers = get_headers()
    page = 1
    
    print(f"Discovering repositories in {ORG_NAME}...")
    
    while True:
        try:
            response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
            
            if response.status_code == 404:
                print(f"ERROR: Organization '{ORG_NAME}' not found or not accessible")
                sys.exit(1)
            
            if response.status_code != 200:
                print(f"WARNING: Failed to fetch repos (status {response.status_code})")
                break
            
            data = response.json()
            
            if not data:
                break
            
            for repo in data:
                repos.append(repo["name"])
            
            page += 1
            
        except Exception as e:
            print(f"WARNING: Error fetching repos: {e}")
            break
    
    print(f"Found {len(repos)} repositories")
    return repos


def fetch_pull_requests(repo):
    """
    Fetch pull requests from a repository within the time window.
    
    Args:
        repo: Repository name
    
    Returns:
        list: List of PR objects
    """
    prs = []
    cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=DAYS_BACK)
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo}/pulls"
    headers = get_headers()
    page = 1
    
    print(f"  Fetching PRs from {repo}...")
    
    while True:
        try:
            response = requests.get(
                url,
                headers=headers,
                params={"state": "all", "page": page, "per_page": 100, "sort": "created", "direction": "desc"}
            )
            
            if response.status_code != 200:
                print(f"    WARNING: Failed to fetch PRs (status {response.status_code})")
                break
            
            data = response.json()
            
            if not data:
                break
            
            # Filter PRs by creation date
            for pr in data:
                created_at_str = pr.get("created_at")
                if not created_at_str:
                    continue
                
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                except:
                    continue
                
                # Stop if PR is older than cutoff
                if created_at < cutoff_date:
                    print(f"    Reached PRs older than {DAYS_BACK} days")
                    return prs
                
                pr["_repo"] = repo
                prs.append(pr)
            
            page += 1
            
        except Exception as e:
            print(f"    WARNING: Error fetching PRs: {e}")
            break
    
    print(f"    Found {len(prs)} PRs")
    return prs


def fetch_reviews(repo, pr_number):
    """
    Fetch reviews for a pull request.
    
    Args:
        repo: Repository name
        pr_number: Pull request number
    
    Returns:
        list: List of review objects
    """
    reviews = []
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo}/pulls/{pr_number}/reviews"
    headers = get_headers()
    page = 1
    
    while True:
        try:
            response = requests.get(url, headers=headers, params={"page": page, "per_page": 100})
            
            if response.status_code != 200:
                break
            
            data = response.json()
            
            if not data:
                break
            
            reviews.extend(data)
            page += 1
            
        except Exception as e:
            break
    
    return reviews


def map_user_to_employee(login):
    """
    Map a GitHub login to an employee name.
    
    Args:
        login: GitHub username
    
    Returns:
        str or None: Employee name if mapped, None otherwise
    """
    if not login:
        return None
    return EMPLOYEE_MAP.get(login)


def aggregate_pr_metrics(all_prs):
    """
    Aggregate PR metrics per employee.
    
    Args:
        all_prs: List of all pull requests
    
    Returns:
        dict: PR metrics per employee
    """
    print("\nAggregating PR metrics...")
    
    employee_pr_data = defaultdict(lambda: {
        "prs_opened": 0,
        "prs_merged": 0,
        "prs_closed_unmerged": 0,
        "draft_prs": 0,
        "repos": set(),
        "additions": [],
        "deletions": [],
        "changed_files": [],
        "comments": [],
        "review_comments": [],
        "merge_times": [],
        "last_pr_date": None
    })
    
    for pr in all_prs:
        # Get PR author
        author_login = pr.get("user", {}).get("login") if pr.get("user") else None
        employee = map_user_to_employee(author_login)
        
        if not employee:
            continue
        
        repo = pr.get("_repo")
        created_at_str = pr.get("created_at")
        
        if not created_at_str:
            continue
        
        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except:
            continue
        
        # Update metrics
        employee_pr_data[employee]["prs_opened"] += 1
        employee_pr_data[employee]["repos"].add(repo)
        
        # Check if merged
        if pr.get("merged_at"):
            employee_pr_data[employee]["prs_merged"] += 1
            
            # Calculate merge time
            try:
                merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                merge_time_hours = (merged_at - created_at).total_seconds() / 3600
                employee_pr_data[employee]["merge_times"].append(merge_time_hours)
            except:
                pass
        
        # Check if closed but not merged
        if pr.get("state") == "closed" and not pr.get("merged_at"):
            employee_pr_data[employee]["prs_closed_unmerged"] += 1
        
        # Check if draft
        if pr.get("draft"):
            employee_pr_data[employee]["draft_prs"] += 1
        
        # Collect PR statistics
        if pr.get("additions") is not None:
            employee_pr_data[employee]["additions"].append(pr["additions"])
        if pr.get("deletions") is not None:
            employee_pr_data[employee]["deletions"].append(pr["deletions"])
        if pr.get("changed_files") is not None:
            employee_pr_data[employee]["changed_files"].append(pr["changed_files"])
        if pr.get("comments") is not None:
            employee_pr_data[employee]["comments"].append(pr["comments"])
        if pr.get("review_comments") is not None:
            employee_pr_data[employee]["review_comments"].append(pr["review_comments"])
        
        # Update last PR date
        if (employee_pr_data[employee]["last_pr_date"] is None or 
            created_at > employee_pr_data[employee]["last_pr_date"]):
            employee_pr_data[employee]["last_pr_date"] = created_at
    
    # Convert to final format with averages
    results = {}
    for employee, data in employee_pr_data.items():
        results[employee] = {
            "prs_opened": data["prs_opened"],
            "prs_merged": data["prs_merged"],
            "prs_closed_unmerged": data["prs_closed_unmerged"],
            "draft_prs": data["draft_prs"],
            "repos_with_prs": len(data["repos"]),
            "avg_pr_additions": round(sum(data["additions"]) / len(data["additions"]), 2) if data["additions"] else 0,
            "avg_pr_deletions": round(sum(data["deletions"]) / len(data["deletions"]), 2) if data["deletions"] else 0,
            "avg_pr_changed_files": round(sum(data["changed_files"]) / len(data["changed_files"]), 2) if data["changed_files"] else 0,
            "avg_pr_comments": round(sum(data["comments"]) / len(data["comments"]), 2) if data["comments"] else 0,
            "avg_pr_review_comments": round(sum(data["review_comments"]) / len(data["review_comments"]), 2) if data["review_comments"] else 0,
            "avg_pr_merge_time_hours": round(sum(data["merge_times"]) / len(data["merge_times"]), 2) if data["merge_times"] else 0,
            "last_pr_date": data["last_pr_date"].isoformat() if data["last_pr_date"] else None
        }
    
    return results


def aggregate_review_metrics(all_prs):
    """
    Aggregate review metrics per employee.
    
    Args:
        all_prs: List of all pull requests
    
    Returns:
        dict: Review metrics per employee
    """
    print("Aggregating review metrics...")
    
    employee_review_data = defaultdict(lambda: {
        "reviews_given": 0,
        "approvals_given": 0,
        "change_requests_given": 0,
        "review_comments_left": 0,
        "prs_reviewed": set(),
        "repos_reviewed": set(),
        "last_review_date": None
    })
    
    for pr in all_prs:
        repo = pr.get("_repo")
        pr_number = pr.get("number")
        
        if not pr_number:
            continue
        
        # Fetch reviews for this PR
        reviews = fetch_reviews(repo, pr_number)
        
        for review in reviews:
            # Get reviewer
            reviewer_login = review.get("user", {}).get("login") if review.get("user") else None
            employee = map_user_to_employee(reviewer_login)
            
            if not employee:
                continue
            
            submitted_at_str = review.get("submitted_at")
            if not submitted_at_str:
                continue
            
            try:
                submitted_at = datetime.fromisoformat(submitted_at_str.replace("Z", "+00:00"))
            except:
                continue
            
            # Update metrics
            employee_review_data[employee]["reviews_given"] += 1
            employee_review_data[employee]["prs_reviewed"].add((repo, pr_number))
            employee_review_data[employee]["repos_reviewed"].add(repo)
            
            # Check review state
            state = review.get("state")
            if state == "APPROVED":
                employee_review_data[employee]["approvals_given"] += 1
            elif state == "CHANGES_REQUESTED":
                employee_review_data[employee]["change_requests_given"] += 1
            
            # Note: review_comments_left is set to reviews_given count
            # as per-review comment count is not directly available from reviews endpoint
            # This counts the number of review submissions by the employee
            
            # Update last review date
            if (employee_review_data[employee]["last_review_date"] is None or 
                submitted_at > employee_review_data[employee]["last_review_date"]):
                employee_review_data[employee]["last_review_date"] = submitted_at
    
    # Convert to final format
    results = {}
    for employee, data in employee_review_data.items():
        # review_comments_left is set to reviews_given as a proxy
        # since individual comment counts per review are not available from the reviews endpoint
        results[employee] = {
            "reviews_given": data["reviews_given"],
            "approvals_given": data["approvals_given"],
            "change_requests_given": data["change_requests_given"],
            "review_comments_left": data["reviews_given"],
            "unique_prs_reviewed": len(data["prs_reviewed"]),
            "unique_repos_reviewed": len(data["repos_reviewed"]),
            "last_review_date": data["last_review_date"].isoformat() if data["last_review_date"] else None
        }
    
    return results


def save_output(pr_metrics, review_metrics):
    """
    Save aggregated results to JSON and CSV files.
    
    Args:
        pr_metrics: Dictionary of PR metrics per employee
        review_metrics: Dictionary of review metrics per employee
    """
    print("\nSaving output...")
    
    # Combine metrics
    all_employees = set(pr_metrics.keys()) | set(review_metrics.keys())
    combined = {}
    
    for employee in all_employees:
        combined[employee] = {
            "pr_metrics": pr_metrics.get(employee, {
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
            }),
            "review_metrics": review_metrics.get(employee, {
                "reviews_given": 0,
                "approvals_given": 0,
                "change_requests_given": 0,
                "review_comments_left": 0,
                "unique_prs_reviewed": 0,
                "unique_repos_reviewed": 0,
                "last_review_date": None
            })
        }
    
    # Save JSON
    with open("step2_pr_review_metrics.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)
    print("  Saved step2_pr_review_metrics.json")
    
    # Save CSV
    with open("step2_pr_review_metrics.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "employee_name",
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
            "last_review_date"
        ])
        
        for employee in sorted(combined.keys()):
            pr = combined[employee]["pr_metrics"]
            rev = combined[employee]["review_metrics"]
            writer.writerow([
                employee,
                pr["prs_opened"],
                pr["prs_merged"],
                pr["prs_closed_unmerged"],
                pr["draft_prs"],
                pr["repos_with_prs"],
                pr["avg_pr_additions"],
                pr["avg_pr_deletions"],
                pr["avg_pr_changed_files"],
                pr["avg_pr_comments"],
                pr["avg_pr_review_comments"],
                pr["avg_pr_merge_time_hours"],
                pr["last_pr_date"],
                rev["reviews_given"],
                rev["approvals_given"],
                rev["change_requests_given"],
                rev["review_comments_left"],
                rev["unique_prs_reviewed"],
                rev["unique_repos_reviewed"],
                rev["last_review_date"]
            ])
    print("  Saved step2_pr_review_metrics.csv")


def main():
    """Main execution function."""
    print("="*60)
    print("GitHub PR and Review Data Collection - Step 2")
    print("="*60)
    print(f"Organization: {ORG_NAME}")
    print(f"Time window: Last {DAYS_BACK} days")
    print("="*60 + "\n")
    
    # Step 1: Discover repositories
    repos = discover_repos()
    
    if not repos:
        print("No repositories found")
        sys.exit(1)
    
    # Step 2: Fetch PRs from all repos
    all_prs = []
    for repo in repos:
        prs = fetch_pull_requests(repo)
        all_prs.extend(prs)
    
    print(f"\nTotal PRs collected: {len(all_prs)}")
    
    # Step 3: Aggregate PR metrics
    pr_metrics = aggregate_pr_metrics(all_prs)
    
    # Step 4: Aggregate review metrics
    review_metrics = aggregate_review_metrics(all_prs)
    
    # Step 5: Save output
    save_output(pr_metrics, review_metrics)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Repositories scanned: {len(repos)}")
    print(f"Total PRs: {len(all_prs)}")
    print(f"Employees with PR activity: {len(pr_metrics)}")
    print(f"Employees with review activity: {len(review_metrics)}")
    print("\nPR Metrics:")
    for employee, data in sorted(pr_metrics.items()):
        print(f"  {employee}:")
        print(f"    PRs opened: {data['prs_opened']}")
        print(f"    PRs merged: {data['prs_merged']}")
    print("\nReview Metrics:")
    for employee, data in sorted(review_metrics.items()):
        print(f"  {employee}:")
        print(f"    Reviews given: {data['reviews_given']}")
        print(f"    Approvals: {data['approvals_given']}")
    print("="*60)


if __name__ == "__main__":
    main()
