"""
Scheduler Module for Pipeline Execution

This module provides scheduling functionality for the CSR report processing pipeline.
It uses APScheduler to manage and execute pipeline tasks in sequence.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess

def create_scheduler():
    """
    Create and configure the scheduler with pipeline tasks.
    
    Returns:
        BlockingScheduler: Configured scheduler instance
    """
    scheduler = BlockingScheduler()
    
    # Define pipeline steps to execute
    tasks = [
        {"step": 1, "script": "a_pipeline/modules/main.py"},
        {"step": 2, "script": "a_pipeline/modules/notfoundclean.py"},
        {"step": 3, "script": "b_pipeline/modules/main.py"},
        {"step": 4, "script": "b_pipeline/modules/check_pdf.py"},
        {"step": 5, "script": "b_pipeline/modules/remove_damaged.py"},
        {"step": 6, "script": "upload_to_minio.py"},
    ]
    
    def run_task(script):
        """
        Execute a pipeline task using poetry run.
        
        Args:
            script (str): Path to the Python script to execute.
            
        Returns:
            None
        """
        print(f"🚀 Executing: {script}")
        try:
            subprocess.run(["poetry", "run", "python", script], check=True)
            print(f"✅ Successfully completed: {script}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Execution failed: {script}, Error: {e}")

    # Set to run once per week (e.g., every Monday at 3:00 AM)
    for task in tasks:
        scheduler.add_job(run_task, "cron", day_of_week="mon", hour=3, minute=0, args=[task["script"]])
    
    return scheduler

def main():
    """
    Main function to start the scheduler.
    """
    scheduler = create_scheduler()
    print("📅 APScheduler started successfully! Pipeline will automatically run every Monday at 3:00 AM.")
    scheduler.start()

if __name__ == "__main__":
    main()
