from flask import Blueprint, request, jsonify
from openai_functions import functions

openai_functions_bp = Blueprint('openai_functions', __name__)


@openai_functions_bp.route('/api/function_call', methods=['GET'])
def list_functions():
    function_list = []
    for function_name, function_data in functions.items():
        function_list.append({
            "name": function_data['name'],
            "category": function_data['category'],
            "description": function_data['description'],
        })
    return jsonify(function_list)


@openai_functions_bp.route('/api/function_call', methods=['POST'])
def function_call():
    data = request.json
    function_name = data.get('function_name')
    function = functions.get(function_name)
    
    if function:
        arguments = data.get('arguments', {})
        result = function(**arguments)
        return jsonify(result)
    else:
        return jsonify({'error': 'Function not found'}), 404
