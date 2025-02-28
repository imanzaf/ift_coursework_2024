import subprocess

def run_script(script_name):
    """Helper function to run a script."""
    try:
        result = subprocess.run(['python', script_name], check=True)
        if result.returncode == 0:
            print(f"Successfully ran {script_name}")
        else:
            print(f"Error running {script_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run {script_name}: {e}")

def main():
    while True:
        print("\nChoose an option:")
        print("1. Run all processes (create database → scrap url → storage url → download and upload reports)")
        print("2. Exit")

        choice = input("Enter your choice (1 or 2): ").strip()

        if choice == '1':
            print("Running all processes...")

            # Step 1: Run create_table.py
            run_script('modules/create_table.py')

            # Step 2: Run website+google.py
            run_script('modules/website+google.py')

            # Step 3: Run integrate_urls.py
            run_script('modules/integrate_urls.py')

            # Step 4: Run kafka_minio_integration.py and kafka_producer.py concurrently
            print("Running kafka_minio_integration.py and kafka_producer.py concurrently...")
            proc1 = subprocess.Popen(['python', 'modules/kafka_minio_integration.py'])
            proc2 = subprocess.Popen(['python', 'modules/kafka_producer.py'])

            proc1.wait()
            proc2.wait()
            print("All processes completed.")

            input("Press Enter to return to the main menu...")

        elif choice == '2':
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()
