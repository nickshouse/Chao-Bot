import openai
import subprocess
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_recent_changes():
    try:
        result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True)
        changes = result.stdout.strip().split("\n")
        changes_summary = "\n".join(f"- {change}" for change in changes)
        return f"Recent changes:\n{changes_summary}" if changes_summary else "No recent changes found."
    except subprocess.CalledProcessError:
        return "Unable to fetch recent changes."

def generate_commit_message():
    changes_summary = get_recent_changes()
    prompt = f"Generate a concise Git commit message for the following changes:\n\n{changes_summary}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for writing Git commit messages."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.5
        )
        commit_message = response['choices'][0]['message']['content'].strip()
        return commit_message
    except Exception as e:
        return f"Error generating commit message: {e}"

if __name__ == "__main__":
    commit_message = generate_commit_message()
    with open("commit_message.txt", "w") as f:
        f.write(commit_message)
