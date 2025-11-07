from flask import Flask, jsonify, request
import itertools
import requests

app = Flask(__name__)

# TODO: Add backend server URL for round-robin distribution
BACKEND_SERVERS = [
    # Kubernetes service DNS name for the backend, which resolves to the service's ClusterIP.
    "http://flask-backend-service:5001"
]

# Round-robin iterator for distributing requests
server_pool = itertools.cycle(BACKEND_SERVERS)

@app.route('/model-info')
def load_balance():
    backend_url = next(server_pool)
    try:
        response = requests.get(f"{backend_url}/model-info", headers=request.headers)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Backend service is unavailable", "details": str(e)}), 503

@app.route('/predict', methods=['POST'])
def predict():
    backend_url = next(server_pool)
    url = f"{backend_url}/predict"

    try:
        # Create a clean set of headers to forward, avoiding restricted headers like 'Host'.
        # We only need to forward the Content-Type for this POST request.
        forward_headers = {'Content-Type': request.headers.get('Content-Type')}

        # Forward the request to the selected backend server
        response = requests.post(url, json=request.get_json(), headers=forward_headers)

        # Return the backend's response to the client
        return response.json(), response.status_code

    except requests.exceptions.RequestException as e:
        # Handle cases where the backend is unreachable
        return jsonify({"error": "Backend service is unavailable", "details": str(e)}), 503

if __name__ == '__main__':
    # TODO: Change the port if necessary (default is 8080)
    app.run(host='0.0.0.0', port=8080)
