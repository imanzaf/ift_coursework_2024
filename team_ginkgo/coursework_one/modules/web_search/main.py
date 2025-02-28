import threading
import uvicorn
import sys
import os
import re
import subprocess
import webbrowser
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from web_search.api import app as fastapi_app


def run_fastapi():
    """
    Start the FastAPI server.

    This function uses the `uvicorn` module to run the FastAPI application
    on host `0.0.0.0` and port `8000` with log level set to `error` and no log configuration.
    """
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="error", log_config=None)


def run_flask():
    """
    Start the Flask server.

    This function uses the `subprocess` module to run the Flask application
    on host `0.0.0.0` and port `5000`. It listens to the startup logs of the Flask server
    and waits for the message indicating that the server is running.
    """
    process = subprocess.Popen(
        ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Listen to Flask startup logs, wait for `Running on http://127.0.0.1:5000`
    for line in process.stdout:
        if re.search(r"\* Running on http://127\.0\.0\.1:5000", line):
            print(" ✔️Flask server started successfully!")
            return  # Exit listening, return to main thread


if __name__ == "__main__":
    """
    Main entry point of the script.

    This script starts both FastAPI and Flask servers in separate threads.
    It provides a simple command-line interface to open the web page or close the servers.
    """
    try:
        # Start FastAPI server (thread)
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()

        # Start Flask server and wait for logs
        print(" 🔛Starting server...")
        run_flask()  # Only continue if Flask starts successfully

        print(f" 🔛Server started!")
        print(f" 🔗FastAPI: http://127.0.0.1:8000")
        print(f" 🔗Flask: http://127.0.0.1:5000")

        menu = "\n".join([
            "==========================",
            " [1] Open Web Page",
            " [2] Close server"
        ])

        while True:
            print("\n" + menu)
            command = input(">>> ").strip()

            if command == "1":
                print("\n Opening browser:", "http://127.0.0.1:5000")
                webbrowser.open("http://127.0.0.1:5000")
            elif command == "2":
                print("\n Server is shutting down...")
                print(" Server successfully closed, thank you for using!")
                sys.exit(0)
            else:
                print(" ❌Please enter a valid option [1] or [2]")

    except KeyboardInterrupt:
        print("\n Server manually closed")
        print(" Server successfully closed, thank you for using!")
        sys.exit(0)
