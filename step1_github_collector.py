#!/usr/bin/env python3
"""
Step 1: GitHub Commit Data Collection and Aggregation

Collects commit history from a GitHub organization and aggregates
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


def fetch_commits(repo):
    """
    Fetch commits from a repository within the time window.
    
    Args:
        repo: Repository name
    
    Returns:
        list: List of commit objects
    """
    commits = []
    since_date = (datetime.now() - timedelta(days=DAYS_BACK)).isoformat()
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo}/commits"
    headers = get_headers()
    page = 1
    
    print(f"  Fetching commits from {repo}...")
    
    while True:
        try:
            response = requests.get(
                url,
                headers=headers,
                params={"since": since_date, "page": page, "per_page": 100}
            )
            
            if response.status_code == 409:
                print(f"    Empty repository: {repo}")
                break
            
            if response.status_code != 200:
                print(f"    WARNING: Failed to fetch commits (status {response.status_code})")
                break
            
            data = response.json()
            
            if not data:
                break
            
            for commit in data:
                commit["_repo"] = repo
            
            commits.extend(data)
            page += 1
            
        except Exception as e:
            print(f"    WARNING: Error fetching commits: {e}")
            break
    
    print(f"    Found {len(commits)} commits")
    return commits


def filter_commits(commit):
    """
    Filter out bot commits and merge commits.
    
    Args:
        commit: Commit object
    
    Returns:
        bool: True if commit should be included, False otherwise
    """
    # Check for bot commits
    if commit.get("author"):
        login = commit["author"].get("login", "")
        if "bot" in login.lower():
            return False
    else:
        # Author is null - check commit author name
        commit_author = commit.get("commit", {}).get("author", {})
        name = commit_author.get("name", "")
        email = commit_author.get("email", "")
        if "bot" in name.lower() or "bot" in email.lower():
            return False
    
    # Check for merge commits (commented out to include all commits)
    # message = commit.get("commit", {}).get("message", "")
    # if message.startswith("Merge"):
    #     return False
    
    return True


def map_commit_to_employee(commit):
    """
    Map a commit to an employee name.
    
    Args:
        commit: Commit object
    
    Returns:
        str or None: Employee name if mapped, None otherwise
    """
    # Try to get GitHub login
    if commit.get("author") and commit["author"].get("login"):
        login = commit["author"]["login"]
        if login in EMPLOYEE_MAP:
            return EMPLOYEE_MAP[login]
    
    # Fallback to commit author name or email
    commit_author = commit.get("commit", {}).get("author", {})
    name = commit_author.get("name", "")
    email = commit_author.get("email", "")
    
    # Try to match by name or email
    for login, employee_name in EMPLOYEE_MAP.items():
        if login.lower() in name.lower() or login.lower() in email.lower():
            return employee_name
    
    return None


def aggregate_metrics(all_commits):
    """
    Aggregate commit metrics per employee.
    
    Args:
        all_commits: List of all commits
    
    Returns:
        dict: Aggregated metrics per employee
    """
    print("\nAggregating metrics...")
    
    employee_data = defaultdict(lambda: {
        "total_commits": 0,
        "repos": set(),
        "dates": set(),
        "last_commit_date": None,
        "commits_per_repo": defaultdict(int)
    })
    
    for commit in all_commits:
        if not filter_commits(commit):
            continue
        
        employee = map_commit_to_employee(commit)
        if not employee:
            continue
        
        repo = commit.get("_repo")
        commit_date_str = commit.get("commit", {}).get("author", {}).get("date")
        
        if not commit_date_str:
            continue
        
        # Parse commit date
        try:
            commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
        except:
            continue
        
        # Update metrics
        employee_data[employee]["total_commits"] += 1
        employee_data[employee]["repos"].add(repo)
        employee_data[employee]["dates"].add(commit_date.date().isoformat())
        employee_data[employee]["commits_per_repo"][repo] += 1
        
        # Update last commit date
        if (employee_data[employee]["last_commit_date"] is None or 
            commit_date > employee_data[employee]["last_commit_date"]):
            employee_data[employee]["last_commit_date"] = commit_date
    
    # Convert to final format
    results = {}
    for employee, data in employee_data.items():
        results[employee] = {
            "total_commits": data["total_commits"],
            "repos_contributed_to": len(data["repos"]),
            "active_days": len(data["dates"]),
            "last_commit_date": data["last_commit_date"].isoformat() if data["last_commit_date"] else None,
            "commits_per_repo": dict(data["commits_per_repo"])
        }
    
    return results


def save_output(results):
    """
    Save aggregated results to JSON and CSV files.
    
    Args:
        results: Dictionary of employee metrics
    """
    print("\nSaving output...")
    
    # Save JSON
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("  Saved output.json")
    
    # Save CSV
    with open("output.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["employee_name", "total_commits", "repos_contributed_to", "active_days", "last_commit_date"])
        
        for employee, data in sorted(results.items()):
            writer.writerow([
                employee,
                data["total_commits"],
                data["repos_contributed_to"],
                data["active_days"],
                data["last_commit_date"]
            ])
    print("  Saved output.csv")


def main():
    """Main execution function."""
    print("="*60)
    print("GitHub Commit Data Collection - Step 1")
    print("="*60)
    print(f"Organization: {ORG_NAME}")
    print(f"Time window: Last {DAYS_BACK} days")
    print("="*60 + "\n")
    
    # Step 1: Discover repositories
    repos = discover_repos()
    
    if not repos:
        print("No repositories found")
        sys.exit(1)
    
    # Step 2: Fetch commits from all repos
    all_commits = []
    for repo in repos:
        commits = fetch_commits(repo)
        all_commits.extend(commits)
    
    print(f"\nTotal commits collected: {len(all_commits)}")
    
    # Step 3: Aggregate metrics
    results = aggregate_metrics(all_commits)
    
    # Step 4: Save output
    save_output(results)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Repositories scanned: {len(repos)}")
    print(f"Total commits: {len(all_commits)}")
    print(f"Employees tracked: {len(results)}")
    print("\nEmployee Metrics:")
    for employee, data in sorted(results.items()):
        print(f"  {employee}:")
        print(f"    Commits: {data['total_commits']}")
        print(f"    Repos: {data['repos_contributed_to']}")
        print(f"    Active days: {data['active_days']}")
    print("="*60)


if __name__ == "__main__":
    main()
