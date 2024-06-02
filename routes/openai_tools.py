from flask import Blueprint, request, jsonify
from utils.helpers import list_tools, use_tool

openai_tools_bp = Blueprint('openai_tools', __name__)


@openai_tools_bp.route('/api/tools', methods=['GET'])
def api_list_tools():
    tools = list_tools()
    return jsonify({'tools': tools})


@openai_tools_bp.route('/api/tools', methods=['POST'])
def api_use_tool():
    data = request.json
    tool_name = data.get('name')
    tool_arguments = data.get('arguments')
    if not tool_name:
        return jsonify({'message': 'Tool name is required'}), 400
    result = use_tool(tool_name, tool_arguments)
    if result.get('error'):
        return jsonify(result), 400
    return jsonify(result), 200
