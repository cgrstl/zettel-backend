import os
from flask import Flask, request

# Create the web application
app = Flask(__name__)

# Define the /ingest endpoint. It only accepts POST requests.
@app.route("/ingest", methods=["POST"])
def ingest_data():
    """Receives data from ingestion tools and prints it."""
    
    # Get the JSON data sent from the shortcut or bookmarklet
    data = request.json
    
    # For now, we just print the data to the logs so we can see it.
    # This is our temporary debugging tool.
    # Later, this is where we will add logic to process PDFs, URLs, etc.
    print(f"Received data: {data}")
    
    # Send back a simple success message
    return ("Data received successfully", 200)

# This part allows the app to be run by Google Cloud Run
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))