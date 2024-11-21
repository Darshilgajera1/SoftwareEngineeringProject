import os
import subprocess

def push_to_github():
    """Push the generated files to GitHub."""
    
    # Retrieve the GitHub token stored as a Streamlit secret
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        raise ValueError("GitHub token is not available in Streamlit secrets.")
    
    repo_url = "https://github.com/yourusername/yourrepository.git"  # Replace with your repository URL
    commit_message = "Automated tool generation update"
    
    # Initialize a git repository if it's not already initialized
    if not os.path.exists(".git"):
        subprocess.run(["git", "init"], check=True)

    # Add changes to staging area
    subprocess.run(["git", "add", "."], check=True)

    # Commit changes
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # Set the remote repository with GitHub token for authentication
    remote_url_with_token = f"https://{github_token}:x-oauth-basic@github.com/yourusername/yourrepository.git"
    subprocess.run(["git", "remote", "add", "origin", remote_url_with_token], check=True)

    # Push changes to the repository
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

    print("Code pushed to GitHub successfully.")

# Trigger the GitHub push after tool generation
push_to_github()
