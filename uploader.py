import os
import base64
import json
import urllib.request

TOKEN = os.environ.get("GITHUB_TOKEN", "your_github_token_here")
REPO = "Kg12398/TalentIQ-Agentic-RAG-Intelligence-Suite"
BRANCH = "main"

def github_api_request(method, url, data=None):
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(f"https://api.github.com{url}", headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode("utf-8")
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        if e.code == 404 and method == "GET":
             return None # Common for empty repos
        print(f"Error {e.code}: {err_msg}")
        return None

def upload_to_github():
    print(f"🚀 Starting upload to {REPO}...")
    
    # 1. Collect files (Safety FIRST: strictly skip .env)
    ignore_list = [".env", ".venv", ".git", "__pycache__", ".streamlit", "uploader.py", "push_batch.py"]
    files_to_upload = []
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ignore_list]
        for file in files:
            # Skip ignored files, temp files, and most txt files (keep requirements.txt)
            if file in ignore_list: continue
            if file.startswith("~$"): continue
            if file.endswith(".txt") and file != "requirements.txt": continue
            
            rel_path = os.path.relpath(os.path.join(root, file), ".").replace("\\", "/")
            if rel_path.startswith("."): continue
            
            with open(os.path.join(root, file), "rb") as f:
                content = f.read()
                files_to_upload.append({
                    "path": rel_path,
                    "content": base64.b64encode(content).decode("utf-8")
                })

    # 2. Check if repo is empty by getting current ref
    ref = github_api_request("GET", f"/repos/{REPO}/git/refs/heads/{BRANCH}")
    
    if not ref:
        print("Repository is empty. Initializing with first file...")
        # Create the first file to initialize the branch
        first = files_to_upload[0]
        init_res = github_api_request("PUT", f"/repos/{REPO}/contents/{first['path']}", {
            "message": "Initial commit",
            "content": first["content"],
            "branch": BRANCH
        })
        if not init_res:
            print("Failed to initialize repository.")
            return
        # Refresh ref
        print("Waiting for GitHub to initialize...")
        import time; time.sleep(2)
        ref = github_api_request("GET", f"/repos/{REPO}/git/refs/heads/{BRANCH}")
        if not ref: return
        files_to_upload = files_to_upload[1:] # Skip the one we already uploaded

    base_sha = ref["object"]["sha"]
    
    # 3. Create Tree logic for many files
    print(f"Uploading {len(files_to_upload)} remaining files...")
    tree_nodes = []
    for f in files_to_upload:
        print(f"  Uploading {f['path']}...")
        blob = github_api_request("POST", f"/repos/{REPO}/git/blobs", {
            "content": f["content"],
            "encoding": "base64"
        })
        if blob:
            tree_nodes.append({
                "path": f["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob["sha"]
            })

    # 4. Finalize commit (No base_tree = clean sync, deletes missing files)
    new_tree = github_api_request("POST", f"/repos/{REPO}/git/trees", {
        "tree": tree_nodes
    })
    
    new_commit = github_api_request("POST", f"/repos/{REPO}/git/commits", {
        "message": "Added Automated PDF Uploader, Dynamic UI Sync, Candidate Deletion, and Native PDF Export Features",
        "tree": new_tree["sha"],
        "parents": [base_sha]
    })
    
    github_api_request("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}", {"sha": new_commit["sha"]})
    print(f"\n✅ SUCCESS! Project pushed to https://github.com/{REPO}")

if __name__ == "__main__":
    upload_to_github()
