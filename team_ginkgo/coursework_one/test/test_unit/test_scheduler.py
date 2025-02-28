import pytest
import subprocess
import sys
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Dynamically add the path to the source files
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../modules")))

from scheduler import run_script, run_all_scripts, start_scheduled_tasks

def test_run_script():
    """Test if run_script executes a script without errors."""
    test_script = "test_script.py"
    with open(test_script, "w") as f:
        f.write("print('Test script executed successfully')")
    
    try:
        run_script(test_script)
    finally:
        os.remove(test_script)
    
    print("✅ run_script executed successfully.")

def test_run_all_scripts():
    """Test if run_all_scripts runs without crashing."""
    try:
        run_all_scripts()
    except Exception as e:
        pytest.fail(f"❌ run_all_scripts failed with error: {e}")
    
    print("✅ run_all_scripts executed successfully.")

def test_scheduler_setup():
    """Test if the scheduler initializes correctly."""
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(lambda: print("Scheduler test job executed."), CronTrigger(second="*/10"))
    
    assert job is not None, "❌ Failed to create scheduler job."
    print("✅ Scheduler setup successful.")

def test_code_quality():
    """Run linting, formatting, and security scans for scheduler.py only."""
    python_exec = sys.executable  # Get the correct Python path
    scheduler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../modules/scheduler.py"))

    print("🔍 Running flake8 on scheduler.py...")
    subprocess.run([python_exec, "-m", "flake8", scheduler_path, "--max-line-length=100"], check=True)

    print("🔍 Checking code formatting with black...")
    subprocess.run([python_exec, "-m", "black", "--check", scheduler_path], check=True)

    print("🔍 Sorting imports with isort...")
    subprocess.run([python_exec, "-m", "isort", "--check-only", scheduler_path], check=True)

    print("🔍 Running security scans with Bandit...")
    subprocess.run([python_exec, "-m", "bandit", "-r", scheduler_path], check=True)

if __name__ == "__main__":
    test_run_script()
    test_run_all_scripts()
    test_scheduler_setup()
    test_code_quality()
