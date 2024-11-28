import flask
import os
from flask import Flask, request, jsonify, send_from_directory
app = flask.Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='images/favicon.png')
# @app.route('/webhook', methods=['POST'])
# def webhook():
#     if request.method == 'POST':
#         return 'ok'
    

@app.route('/')
@app.route("/home")
def home():
    return "Hello World"



# Example of a hardcoded authentication key (replace with a secure method in production)
AUTH_KEY = "my_secure_auth_key"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Parse input data
        data = request.json
        if not data:
            return jsonify({"error": "Invalid input, JSON body is required."}), 400

        name = data.get('name')
        auth_key = data.get('auth_key')

        # Validate inputs
        if not name or not auth_key:
            return jsonify({"error": "Both 'name' and 'auth_key' are required."}), 400

        # Check authentication key
        if auth_key != AUTH_KEY:
            return jsonify({"error": "Unauthorized: Invalid authentication key."}), 401

        # Generate response
        response_message = f"Hello, {name}! Welcome to the chat application."
        return jsonify({"message": response_message}), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/dance', methods=['GET'])
def dance():
    try:
        # Read parameters from the URL
        name = request.args.get('name')
        auth_key = request.args.get('auth_key')

        # Validate inputs
        if not name or not auth_key:
            return jsonify({"error": "Both 'name' and 'auth_key' are required."}), 400

        # Check authentication key
        if auth_key != AUTH_KEY:
            return jsonify({"error": "Unauthorized: Invalid authentication key."}), 401

        # Generate response
        response_message = f"Hello, {name}! Time to dance!"
        return jsonify({"message": response_message}), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
    app.secret_key = 'super secret key'