'''
This script is used to schedule the running of the database, scraper, and minio_client scripts.
The scripts are run every quarter (Jan 1st, Apr 1st, Jul 1st, Oct 1st) at 00:00.
The script uses the apscheduler library to schedule the tasks in the background.
The run_script function is used to run a specific script, and the run_all_scripts function is used to run all the scripts.
The start_scheduled_tasks function is used to start the background scheduler.
The script is run as the main module to start the scheduled tasks.  

'''
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Function to run a specific script
def run_script(script_name):
    try:
        print(f"Running {script_name}...")
        subprocess.run(['python', script_name], check=True, capture_output=False, text=True)
        print(f"{script_name} completed successfully.")
    except FileNotFoundError:
        print(f"Error: {script_name} not found.")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")

# Function to run all scripts
def run_all_scripts():
    scripts = ['database.py', 'scraper.py', 'minio_client.py']
    for script in scripts:
        try:
            run_script(script)
        except Exception as e:
            print(f"Warning: {script} failed with error: {e}")
    print("All scripts have completed successfully.")

# Set up a background scheduler to avoid blocking
scheduler = BackgroundScheduler()

# Run every quarter (Jan 1st, Apr 1st, Jul 1st, Oct 1st) at 00:00
scheduler.add_job(run_all_scripts, CronTrigger(month='1,4,7,10', day='1', hour=0, minute=0))

def start_scheduled_tasks():
    print("Starting the background scheduler...")
    scheduler.start()

# Run
if __name__ == "__main__":
    start_scheduled_tasks()
