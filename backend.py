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
    """Endpoint for solving thermodynamic properties using CoolProp"""
    import CoolProp.CoolProp as CP
    
    try:
        data = request.json
        
        # Extract data from request
        state = data.get('state')
        find_properties = data.get('findProperties', [])
        using_properties = data.get('usingProperties', [])
        
        if len(using_properties) < 2:
            return jsonify({
                'status': 'error',
                'message': 'Need at least 2 properties to use for solving'
            }), 400
        
        if len(find_properties) < 1:
            return jsonify({
                'status': 'error',
                'message': 'Need at least 1 property to find'
            }), 400
        
        # Map our property names to CoolProp names
        coolprop_map = {
            'P': 'P',
            'T': 'T',
            'h': 'H',
            's': 'S',
            'x': 'Q'
        }
        
        # Parse the using properties to get property type and value
        # Format: "state3-P" -> extract property 'P' from state 3
        using_props_parsed = []
        for prop_id in using_properties:
            parts = prop_id.split('-')
            prop_name = parts[1]  # e.g., 'P', 'T', 'h', 's', 'x'
            coolprop_name = coolprop_map.get(prop_name, prop_name)
            
            # For now, we'll get the value from the given values
            # This will be passed from frontend in the next step
            using_props_parsed.append({
                'name': coolprop_name,
                'prop_id': prop_id
            })
        
        # Parse the find properties
        find_props_parsed = []
        for prop_id in find_properties:
            parts = prop_id.split('-')
            prop_name = parts[1]
            coolprop_name = coolprop_map.get(prop_name, prop_name)
            find_props_parsed.append({
                'name': coolprop_name,
                'prop_id': prop_id
            })
        
        # For now, return the parsed structure
        # Next step: we'll add actual CoolProp calculation with values
        return jsonify({
            'status': 'success',
            'message': 'Properties parsed successfully',
            'data': {
                'state': state,
                'usingProperties': using_props_parsed,
                'findProperties': find_props_parsed,
                'note': 'Next step: will calculate actual values using CoolProp'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error solving properties: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
