from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend to communicate

@app.route('/test', methods=['GET'])
def test():
    """Simple test endpoint to verify backend is working"""
    return jsonify({
        'status': 'success',
        'message': 'Backend is working!'
    })

@app.route('/solve', methods=['POST'])
def solve():
    """Endpoint for solving thermodynamic properties"""
    data = request.json
    
    # Extract data from request
    state = data.get('state')
    find_properties = data.get('findProperties', [])
    using_properties = data.get('usingProperties', [])
    
    # For now, just echo back what we received
    return jsonify({
        'status': 'success',
        'message': 'Received solve request',
        'data': {
            'state': state,
            'findProperties': find_properties,
            'usingProperties': using_properties
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
