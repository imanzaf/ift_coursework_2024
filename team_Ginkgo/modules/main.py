'''
This module contains the main function that allows the user to choose between running the scripts now, scheduling the scripts to run every quarter, or exiting the program.
The main function uses the scheduler module to run the scripts and start the scheduled tasks in the background.
The user can choose to run the scripts immediately, schedule the scripts to run every quarter, or exit the program.

Example usage:

1. Run scripts now: Run all scripts immediately.
2. Schedule scripts to run every quarter: Start scheduled tasks in the background.
3. Exit: Exit the program.

'''
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

# Run
if __name__ == "__main__":
    main()
