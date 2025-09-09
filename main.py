import os
from flask import Flask, request
from flask_cors import CORS

# ADDED FOR DEBUGGING: Announce that the script has started
print("---- SCRIPT STARTING ----")

try:
    # Create the web application
    app = Flask(__name__)
    print("---- Flask app created ----")

    CORS(app)
    print("---- CORS enabled ----")

    # Define the /ingest endpoint. It only accepts POST requests.
    @app.route("/ingest", methods=["POST"])
    def ingest_data():
        """Receives data from ingestion tools and prints it."""
        print("---- Ingest function called ----")
        data = request.json
        print(f"SUCCESSFULLY RECEIVED: {data}")
        return ({"status": "success", "received": data}, 200)

    print("---- Ingest route defined ----")

except Exception as e:
    # ADDED FOR DEBUGGING: Catch any error during setup
    print(f"!!!! An error occurred during setup: {e}")


# This part allows the app to be run by Google Cloud Run
if __name__ == "__main__":
    print("---- Starting Flask server ----")
    try:
        app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    except Exception as e:
        # ADDED FOR DEBUGGING: Catch any error during server start
        print(f"!!!! An error occurred starting the server: {e}")