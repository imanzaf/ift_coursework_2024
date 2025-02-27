'''
This script is used to run both FastAPI and Flask servers simultaneously.
The FastAPI server is used to query CSR reports from the database, while the Flask server is used to provide a web interface for users to search for a company's financial report by entering the company name and year.
The script starts the FastAPI server in a separate thread and the Flask server in the main thread. It also provides a simple menu for users to open the web page in a browser or close the servers.

'''

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
    """Start FastAPI server"""
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="error", log_config=None)


def run_flask():
    """Start Flask server"""
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
