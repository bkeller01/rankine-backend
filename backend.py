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

def parse_value(value_str, property_type):
    """Convert display values to SI units for CoolProp"""
    if not value_str:
        return None
    
    value_str = str(value_str).strip()
    
    try:
        if property_type == 'P':
            # Pressure: convert to Pa
            if 'MPa' in value_str:
                return float(value_str.replace('MPa', '').strip()) * 1e6
            elif 'kPa' in value_str:
                return float(value_str.replace('kPa', '').strip()) * 1e3
            elif 'Pa' in value_str:
                return float(value_str.replace('Pa', '').strip())
            else:
                return float(value_str)
                
        elif property_type == 'T':
            # Temperature: convert to K
            if '°C' in value_str or 'C' in value_str:
                celsius = float(value_str.replace('°C', '').replace('C', '').strip())
                return celsius + 273.15
            elif 'K' in value_str:
                return float(value_str.replace('K', '').strip())
            else:
                return float(value_str) + 273.15  # Assume Celsius if no unit
                
        elif property_type == 'H':
            # Enthalpy: convert to J/kg
            if 'kJ/kg' in value_str:
                return float(value_str.replace('kJ/kg', '').strip()) * 1e3
            elif 'J/kg' in value_str:
                return float(value_str.replace('J/kg', '').strip())
            else:
                return float(value_str)
                
        elif property_type == 'S':
            # Entropy: convert to J/(kg·K)
            if 'kJ/(kg·K)' in value_str or 'kJ/kg·K' in value_str:
                return float(value_str.replace('kJ/(kg·K)', '').replace('kJ/kg·K', '').strip()) * 1e3
            elif 'J/(kg·K)' in value_str or 'J/kg·K' in value_str:
                return float(value_str.replace('J/(kg·K)', '').replace('J/kg·K', '').strip())
            else:
                return float(value_str)
                
        elif property_type == 'Q':
            # Quality: dimensionless (0-1)
            return float(value_str)
            
        else:
            return float(value_str)
            
    except ValueError:
        return None

def format_output(value, property_type):
    """Convert SI units from CoolProp to display units"""
    if value is None:
        return None
    
    if property_type == 'P':
        # Convert Pa to MPa
        return f"{value / 1e6:.3f} MPa"
        
    elif property_type == 'T':
        # Convert K to °C
        return f"{value - 273.15:.2f}°C"
        
    elif property_type == 'H':
        # Convert J/kg to kJ/kg
        return f"{value / 1e3:.2f} kJ/kg"
        
    elif property_type == 'S':
        # Convert J/(kg·K) to kJ/(kg·K)
        return f"{value / 1e3:.4f} kJ/(kg·K)"
        
    elif property_type == 'Q':
        # Quality is dimensionless
        return f"{value:.4f}"
        
    else:
        return str(value)

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
        # Format from frontend: [{id: "state3-P", value: "10 MPa"}, ...]
        using_props_parsed = []
        for prop_obj in using_properties:
            prop_id = prop_obj.get('id') if isinstance(prop_obj, dict) else prop_obj
            prop_value = prop_obj.get('value') if isinstance(prop_obj, dict) else None
            
            parts = prop_id.split('-')
            prop_name = parts[1]  # e.g., 'P', 'T', 'h', 's', 'x'
            coolprop_name = coolprop_map.get(prop_name, prop_name)
            
            # Parse the value string into SI units
            si_value = parse_value(prop_value, coolprop_name)
            
            if si_value is None:
                return jsonify({
                    'status': 'error',
                    'message': f'Could not parse value "{prop_value}" for property {prop_name}'
                }), 400
            
            using_props_parsed.append({
                'name': coolprop_name,
                'prop_id': prop_id,
                'value': si_value
            })
        
        # Parse the find properties
        # Format from frontend: [{id: "state3-h"}, ...]
        find_props_parsed = []
        for prop_obj in find_properties:
            prop_id = prop_obj.get('id') if isinstance(prop_obj, dict) else prop_obj
            parts = prop_id.split('-')
            prop_name = parts[1]
            coolprop_name = coolprop_map.get(prop_name, prop_name)
            find_props_parsed.append({
                'name': coolprop_name,
                'prop_id': prop_id
            })
        
        # Get the two using properties for CoolProp
        if len(using_props_parsed) < 2:
            return jsonify({
                'status': 'error',
                'message': 'Need exactly 2 properties for CoolProp calculation'
            }), 400
        
        prop1_name = using_props_parsed[0]['name']
        prop1_value = using_props_parsed[0]['value']
        
        prop2_name = using_props_parsed[1]['name']
        prop2_value = using_props_parsed[1]['value']
        
        # Calculate each find property using CoolProp
        results = {}
        for find_prop in find_props_parsed:
            prop_to_find = find_prop['name']
            prop_id = find_prop['prop_id']
            
            try:
                # Call CoolProp to calculate the property
                calculated_value = CP.PropsSI(
                    prop_to_find,
                    prop1_name, prop1_value,
                    prop2_name, prop2_value,
                    'Water'  # Working fluid
                )
                
                # Format the result for display
                formatted_value = format_output(calculated_value, prop_to_find)
                results[prop_id] = formatted_value
                
            except Exception as calc_error:
                return jsonify({
                    'status': 'error',
                    'message': f'CoolProp calculation failed for {prop_to_find}: {str(calc_error)}'
                }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Properties calculated successfully',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error solving properties: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
