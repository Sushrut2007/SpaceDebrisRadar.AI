import streamlit as st
import requests
import time
import os

def trigger_github_workflow(repo_name, workflow_filename, github_token, update_status_func, progress_bar):
    """
    Triggers a GitHub Action workflow and polls for its status.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
    }
    
    # Stage 1: Trigger
    update_status_func("Triggering Remote GitHub Action...", 1)
    progress_bar.progress(20, text="Contacting GitHub API...")
    
    url = f"https://api.github.com/repos/{repo_name}/actions/workflows/{workflow_filename}/dispatches"
    data = {"ref": "main"}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code != 204:
            st.error(f"GitHub API Error: {response.status_code} - {response.text}")
            return False
            
        progress_bar.progress(25, text="Signal Sent! Waiting for GitHub to start...")
        update_status_func("Waiting for job to appear...", 1)
        
        # Stage 2: Poll for Run Status
        runs_url = f"https://api.github.com/repos/{repo_name}/actions/workflows/{workflow_filename}/runs"
        
        # Give it a moment to register
        time.sleep(5)
        
        max_retries = 100 # Approx 8-10 mins max
        for i in range(max_retries):
            try:
                r = requests.get(runs_url, headers=headers)
                if r.status_code == 200:
                    runs = r.json().get("workflow_runs", [])
                    if runs:
                        latest_run = runs[0]
                        run_status = latest_run.get("status") # queued, in_progress, completed
                        conclusion = latest_run.get("conclusion") # success, failure, etc.
                        
                        if run_status == "queued":
                            progress_bar.progress(35, text="Job is Queued on GitHub...")
                            update_status_func("Waiting for runner...", 1)
                        
                        elif run_status == "in_progress":
                            progress_bar.progress(65, text="Pipeline is Running on GitHub...")
                            update_status_func(f"Processing data... (Elapsed: {i*5}s)", 3)
                            
                        elif run_status == "completed":
                            if conclusion == "success":
                                progress_bar.progress(100, text="Pipeline Finished Successfully!")
                                return True
                            else:
                                st.error(f"Remote Pipeline Failed: {conclusion}")
                                return False
                
                time.sleep(5)
            except Exception as e:
                st.warning(f"Polling warning: {e}")
                time.sleep(5)
        
        st.info("Polling Timed Out: The pipeline may still be running.")
        return False

    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return False
