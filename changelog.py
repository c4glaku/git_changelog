import os
import sys
import subprocess
import re
import argparse
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("OPENAI_API_KEY environment variable not set in environment.")
    sys.exit(1)

def get_recent_commits(n: int):
    """
    Retrieves last n commits from the git repository.
    Returns a list of commit directories with keys: hash, author, date, message.
    """
    format_str = "--pretty=format:%H|%an|%ad|%s"
    try:
        result = subprocess.run(
            ["git", "log", f"-n{n}", format_str],
            capture_output=True,
            text=True,
            check=True
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) == 4:
                commit_hash, author, date, message = parts
                commits.append({
                    "hash": commit_hash,
                    "author": author,
                    "date": date,
                    "message": message
                })
        return commits
    
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving commits: {e.stderr.strip()}")
        return []


def get_commit_details(commit_hash: str):
    """
    Retrieves detailed information about a specific commit.
    Returns a dictionary with the ocmmit's full message, changes, and diff_stats.
    """
    try:
        message = subprocess.run(
            ["git", "show", "--format=%B", commit_hash],
            capture_output=True,
            text=True,
            check=True
        )
        changes = subprocess.run(
            ["git", "show", "--name-status", commit_hash],
            capture_output=True,
            text=True,
            check=True
        )
        num_stats = subprocess.run(
            ["git", "show", "--numstat", commit_hash],
            capture_output=True,
            text=True,
            check=True
        )
        
        diff_stats = []
        pattern = re.compile(r"(\d+|-)\s+(\d+|-)\s+(.+)")
        for line in num_stats.stdout.strip().split("\n"):
            match = pattern.match(line)
            if match:
                additions = match.group(1)
                deletions = match.group(2)
                file_path = match.group(3)
                diff_stats.append({
                    "file": file_path,
                    "additions": additions,
                    "deletions": deletions,
                })
        return {
            'hash': commit_hash,
            "full_message": message.stdout.strip(),
            'changes': changes.stdout.strip(),
            'diff_stats': diff_stats,
        }
    
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving commit details for {commit_hash}: {e.stderr}")
        return {}
    
def prepare_prompt(commits):
    """
    Prepares the prompt for the OpenAI API based on the commit information.
    """
    prompt = ("Based on the following git commit history, generate a user-friendly changelog "
            "that summarizes the changes in a way that would be meaningful to the end user. "
            "Git Commit History:\n")
    
    for commit in commits:
        prompt += f"Commit Hash: {commit['hash'][:8]}\n"
        prompt += f"Author: {commit['author']}\n"
        prompt += f"Date: {commit['date']}\n"
        prompt += f"Message: {commit['message']}\n"
        if 'full_message' in commit and commit["full_message"] != commit["message"]:
            prompt += f"Details: {commit['full_message']}\n"
        if "diff_stats" in commit and commit["diff_stats"]:
            for stat in commit["diff_stats"]:
                prompt += f"File: {stat['file']} (+" f"{stat['additions']} / -{stat['deletions']})\n"
        prompt += "\n"
    
    prompt += ("Please generate a changelog with clear sections (e.g., Features, Improvements, Bug Fixes) "
                "using markdown formatting. Provide a concise summary that focues on the changes that matter most to the end user.")
    return prompt

def generate_changelog(n: int) -> str:
    """
    Generates a changelog from the n most recent git commits.
    """
    commits = get_recent_commits(n)
    if not commits:
        return "No commit history found or not in a git repository"
    
    detailed_commits = []
    for commit in commits:
        details = get_commit_details(commit["hash"])
        detailed_commit = {**commit, **details}
        detailed_commits.append(detailed_commit)
    
    prompt = prepare_prompt(detailed_commits)
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "You are a helpful assistant that generates changelogs from git commit histories"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # Adjust temperature for creativity vs. accuracy
        )
    except Exception as e:
        return f"Error generating changelog: {e}"
    

def main():
    parser = argparse.ArgumentParser(
        description="Generate a changelog from recent git commits using OpenAI API"
    )
    parser.add_argument(
        "n",
        type=int,
        help="Number of recent commits to include in the changelog"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional: specify an output file to write the changelog (default: write to stdout)"
    )
    args = parser.parse_args()
    
    changelog = generate_changelog(args.n)
    
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(changelog)
            print(f"Changelog written to {args.output}")
        except IOError as e:
            print(f"Error writing to file {args.output}: {e}")
    else:
        print(changelog)
        
    
if __name__ == "__main__":
    main()