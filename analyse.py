import requests
import os
from collections import defaultdict
from datetime import datetime
import urllib3

# Disable SSL warnings (use with caution!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_user_contributions(username=None, enterprise_url=None, github_token=None, is_enterprise=False, start_date=None, end_date=None, verify_ssl=True):
    """
    Retrieves user contributions from a GitHub instance (public or enterprise) within a date range, using environment variables if available.

    Args:
        username (str, optional): The GitHub username. Defaults to None.
        enterprise_url (str, optional): The enterprise GitHub URL. Defaults to None.
        github_token (str, optional): The personal access token. Defaults to None.
        is_enterprise (bool, optional): Indicates if the target is a GitHub Enterprise instance. Defaults to False.
        start_date (str, optional): Start date for analysis (YYYY-MM-DD). Defaults to None.
        end_date (str, optional): End date for analysis (YYYY-MM-DD). Defaults to None.
        verify_ssl (bool, optional): Verify SSL certificates. Defaults to True.
    Returns:
        dict: A dictionary containing user contribution statistics, or None if an error occurs.
    """

    # Get username, enterprise URL, token, and is_enterprise from environment variables if not provided as arguments.
    username = username or os.getenv("GITHUB_USERNAME")
    enterprise_url = enterprise_url or os.getenv("GITHUB_ENTERPRISE_URL")
    github_token = github_token or os.getenv("GITHUB_TOKEN")
    is_enterprise = is_enterprise or os.getenv("GITHUB_IS_ENTERPRISE", "False").lower() == "true"
    start_date = start_date or os.getenv("GITHUB_START_DATE")
    end_date = end_date or os.getenv("GITHUB_END_DATE")
    verify_ssl = verify_ssl and os.getenv("GITHUB_VERIFY_SSL", "True").lower() == "true" #handle the bool from env.

    if not username or not github_token:
        print("Error: Missing required inputs. Please provide username and GitHub token either as arguments or environment variables.")
        return None

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }

    if is_enterprise and not enterprise_url:
        print("Error: For GitHub Enterprise, please provide the GITHUB_ENTERPRISE_URL.")
        return None

    base_api_url = f"{enterprise_url}/api/v3" if is_enterprise else "https://api.github.com"

    pull_requests_reviewed = 0
    valid_comments = 0
    lines_added = 0
    lines_deleted = 0
    repo_contributions = defaultdict(int)

    # Convert start and end dates to datetime objects if provided.
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

    # 1. Get all repositories the user has contributed to.
    user_repos_url = f"{base_api_url}/search/issues?q=involves:{username}"
    try:
        response = requests.get(user_repos_url, headers=headers, verify=verify_ssl)
        response.raise_for_status()
        repos_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user repositories: {e}")
        return None

    for item in repos_data.get('items', []):
        repo_full_name = item.get('repository_url').replace(f"{base_api_url}/repos/", "")
        if repo_full_name:
            repo_contributions[repo_full_name] += 1

    # 2. Iterate through pull requests and comments.
    for repo_full_name in repo_contributions.keys():
        pull_requests_url = f"{base_api_url}/repos/{repo_full_name}/pulls?state=all"
        try:
            response = requests.get(pull_requests_url, headers=headers, verify=verify_ssl)
            response.raise_for_status()
            pull_requests = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching pull requests for {repo_full_name}: {e}")
            continue

        for pr in pull_requests:
            pr_created_at = datetime.strptime(pr.get('created_at'), "%Y-%m-%dT%H:%M:%SZ")

            # Check if PR is within the date range.
            if (start_datetime and pr_created_at < start_datetime) or (end_datetime and pr_created_at > end_datetime):
                continue

            if pr.get('user', {}).get('login') == username:
                commits_url = pr.get('commits_url')
                try:
                    commits_response = requests.get(commits_url, headers=headers, verify=verify_ssl)
                    commits_response.raise_for_status()
                    commits = commits_response.json()
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching commits for PR {pr.get('number')} in {repo_full_name}: {e}")
                    continue

                for commit in commits:
                    commit_url = commit.get('url')
                    try:
                        commit_details_response = requests.get(commit_url, headers=headers, verify=verify_ssl)
                        commit_details_response.raise_for_status()
                        commit_details = commit_details_response.json()
                    except requests.exceptions.RequestException as e:
                        print(f"Error fetching commit details for commit {commit.get('sha')} in {repo_full_name}: {e}")
                        continue

                    lines_added += commit_details.get('stats', {}).get('additions', 0)
                    lines_deleted += commit_details.get('stats', {}).get('deletions', 0)

            reviews_url = pr.get('review_comments_url').replace("comments","reviews")
            try:
                reviews_response = requests.get(reviews_url, headers=headers, verify=verify_ssl)
                reviews_response.raise_for_status()
                reviews = reviews_response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching reviews for PR {pr.get('number')} in {repo_full_name}: {e}")
                continue

            for review in reviews:
                if review.get('user', {}).get('login') == username:
                    pull_requests_reviewed += 1
                    if review.get('body') and len(review.get('body')) > 10:
                        valid_comments += 1

            comments_url = pr.get('comments_url')
            try:
                comments_response = requests.get(comments_url, headers=headers, verify=verify_ssl)
                comments_response.raise_for_status()
                comments = comments_response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching comments for PR {pr.get('number')} in {repo_full_name}: {e}")
                continue

            for comment in comments:
                if comment.get('user', {}).get('login') == username:
                    if comment.get('body') and len(comment.get('body')) > 10:
                        valid_comments += 1

    top_repos = sorted(repo_contributions.items(), key=lambda item: item[1], reverse=True)[:3]

    return {
        "pull_requests_reviewed": pull_requests_reviewed,
        "valid_comments": valid_comments,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "lines_modified": lines_added + lines_deleted,
        "top_repositories": top_repos,
        "start_date": start_date,
        "end_date": end_date,
    }

# Example usage (using environment variables):
results = get_user_contributions()

if results:
    print("User Contribution Report:")
    if results['start_date'] or results['end_date']:
        print(f"Date Range: {results['start_date'] or 'N/A'} - {results['end_date'] or 'N/A'}")
    print(f"Pull Requests Reviewed: {results['pull_requests_reviewed']}")
    print(f"Valid Comments: {results['valid_comments']}")
    print(f"Lines Added: {results['lines_added']}")
    print(f"Lines Deleted: {results['lines_deleted']}")
    print(f"Lines Modified: {results['lines_modified']}")
    print("Top 3 Active Repositories:")
    for repo, count in results['top_repositories']:
        print(f"  - {repo}: {count} interactions")