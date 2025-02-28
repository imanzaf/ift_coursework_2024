import sys
import os

# Get the directory of the current script (main.py)
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the "modules" directory
modules_dir = os.path.join(base_dir, "modules")

# Add the "modules" directory to sys.path to allow module imports
sys.path.append(modules_dir)

# Import the scheduler module from the "modules" directory
import scheduler

# Main function to handle scheduling and manual execution
def main():
    while True:
        print("\nChoose an option:")
        print("1. Run scripts now")
        print("2. Schedule scripts to run every quarter")
        print("3. Exit")

        choice = input("Enter your choice (1, 2, or 3): ").strip()

        if choice == '1':
            print("Running scripts now...")
            scheduler.run_all_scripts()
            input("Press Enter to return to the main menu...")
        elif choice == '2':
            print("Starting scheduled tasks in the background...")
            scheduler.start_scheduled_tasks()
            input("Scheduled tasks started. Press Enter to return to the main menu...")
        elif choice == '3':
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

# Run the main function if the script is executed directly
if __name__ == "__main__":
    main()
