from flask import Flask
from models import app # Import app 
from routes import *  # Import routes

# Start the app
if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode for development
