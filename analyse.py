import requests
import os
from collections import defaultdict
from datetime import datetime
import urllib3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_user_contributions(username=None, enterprise_url=None, github_token=None, is_enterprise=False, start_date=None, end_date=None, verify_ssl=None):
    """Retrieves user contributions from all accessible repositories."""

    username = username or os.getenv("GITHUB_USERNAME")
    enterprise_url = enterprise_url or os.getenv("GITHUB_ENTERPRISE_URL")
    github_token = github_token or os.getenv("GITHUB_TOKEN")
    is_enterprise = is_enterprise or os.getenv("GITHUB_IS_ENTERPRISE", "False").lower() == "true"
    start_date = start_date or os.getenv("GITHUB_START_DATE")
    end_date = end_date or os.getenv("GITHUB_END_DATE")

    if verify_ssl is None:
        verify_ssl = os.getenv("GITHUB_VERIFY_SSL", "True").lower() == "true"

    if not username or not github_token:
        logging.error("Missing required inputs.")
        return None

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }

    base_api_url = f"{enterprise_url}/api/v3" if is_enterprise else "https://api.github.com"

    pull_requests_reviewed = 0
    valid_comments = 0
    lines_added = 0
    lines_deleted = 0
    repo_contributions = defaultdict(int)

    start_datetime = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

    repos_url = f"{base_api_url}/user/repos?per_page=100"
    all_repos = []
    page = 1
    while True:
        try:
            response = requests.get(f"{repos_url}&page={page}", headers=headers, verify=verify_ssl)
            response.raise_for_status()
            repos = response.json()
            if not repos:
                break
            all_repos.extend(repos)
            page += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching repositories: {e}")
            return None

    logging.info(f"Processing {len(all_repos)} repositories.")

    for repo in all_repos:
        repo_full_name = repo["full_name"]
        logging.info(f"Processing repository: {repo_full_name}")
        repo_contributions[repo_full_name] = 0

        pulls_url = f"{base_api_url}/repos/{repo_full_name}/pulls?state=all"
        try:
            response = requests.get(pulls_url, headers=headers, verify=verify_ssl)
            response.raise_for_status()
            pulls = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching pulls for {repo_full_name}: {e}")
            continue

        logging.info(f"Processing {len(pulls)} pull requests for {repo_full_name}")

        for pull in pulls:
            pull_number = pull.get('number')
            logging.info(f"Processing pull request {pull_number} in {repo_full_name}")

            pull_created_at = datetime.strptime(pull.get('created_at'), "%Y-%m-%dT%H:%M:%SZ")
            if (start_datetime and pull_created_at < start_datetime) or (end_datetime and pull_created_at > end_datetime):
                logging.info(f"Pull request {pull_number} out of date range. Skipping.")
                continue

            if pull.get('user', {}).get('login') == username:
                repo_contributions[repo_full_name] += 1
                commits_url = pull.get('commits_url')
                try:
                    commits_response = requests.get(commits_url, headers=headers, verify=verify_ssl)
                    commits_response.raise_for_status()
                    commits = commits_response.json()
                except requests.exceptions.RequestException as e:
                    logging.error(f"Error fetching commits for PR {pull_number} in {repo_full_name}: {e}")
                    continue

                logging.info(f"Processing {len(commits)} commits for PR {pull_number} in {repo_full_name}")
                for commit in commits:
                    commit_sha = commit.get('sha')
                    logging.info(f"Processing commit {commit_sha} in PR {pull_number} in {repo_full_name}")
                    commit_url = commit.get('url')
                    try:
                        commit_details_response = requests.get(commit_url, headers=headers, verify=verify_ssl)
                        commit_details_response.raise_for_status()
                        commit_details = commit_details_response.json()
                    except requests.exceptions.RequestException as e:
                        logging.error(f"Error fetching commit details for commit {commit_sha} in {repo_full_name}: {e}")
                        continue

                    lines_added += commit_details.get('stats', {}).get('additions', 0)
                    lines_deleted += commit_details.get('stats', {}).get('deletions', 0)

            reviews_url = pull.get('review_comments_url').replace("comments", "reviews")
            try:
                reviews_response = requests.get(reviews_url, headers=headers, verify=verify_ssl)
                reviews_response.raise_for_status()
                reviews = reviews_response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching reviews for PR {pull_number} in {repo_full_name}: {e}")
                continue

            logging.info(f"Processing {len(reviews)} reviews for PR {pull_number} in {repo_full_name}")
            for review in reviews:
                if review.get('user', {}).get('login') == username:
                    pull_requests_reviewed += 1
                    if review.get('body') and len(review.get('body')) > 10:
                        valid_comments += 1

    top_repos = sorted(repo_contributions.items(), key=lambda item: item[1], reverse=True)[:3]

    user_name = username
    try:
        user_info_url = f"{base_api_url}/users/{username}"
        response = requests.get(user_info_url, headers=headers, verify=verify_ssl)
        response.raise_for_status()
        user_info = response.json()
        user_name = user_info.get("name", username)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching user info: {e}")

    results = {
        "user_name": user_name,
        "pull_requests_reviewed": pull_requests_reviewed,
        "valid_comments": valid_comments,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "lines_modified": lines_added + lines_deleted,
        "top_repositories": top_repos,
        "start_date": start_date,
        "end_date": end_date,
    }

    return results

def generate_html_report(results):
    """Generates an HTML report from the user contribution results."""

    html = """
    <html>
    <head>
    <style>
    body { font-family: 'Roboto', sans-serif; margin: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    .header { background-color: #1976d2; color: white; padding: 10px; text-align: center; }
    .repo-list { list-style-type: none; padding: 0; }
    .repo-list li { margin-bottom: 5px; }
    </style>
    </head>
    <body>
    <div class="header"><h2>User Contribution Report</h2></div>
    """

    if results['start_date'] or results['end_date']:
        html += f"<p><strong>Date Range:</strong> {results['start_date'] or 'N/A'} - {results['end_date'] or 'N/A'}</p>"

    html += f"<p><strong>User:</strong> {results['user_name']}</p>"

    html += """
    <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Pull Requests Reviewed</td><td>{pull_requests_reviewed}</td></tr>
    <tr><td>Valid Comments</td><td>{valid_comments}</td></tr>
    <tr><td>Lines Added</td><td>{lines_added}</td></tr>
    <tr><td>Lines Deleted</td><td>{lines_deleted}</td></tr>
    <tr><td>Lines Modified</td><td>{lines_modified}</td></tr>
    <tr><td>Top 3 Active Repositories</td><td><ul class="repo-list">""".format(**results)

    for repo, count in results['top_repositories']:
        html += f"<li>{repo}: {count} interactions</li>"
    html += "</ul></td></tr></table></body></html>"

    return html

# Example usage (using environment variables):
results = get_user_contributions()

if results:
    html_report = generate_html_report(results)
    print(html_report)