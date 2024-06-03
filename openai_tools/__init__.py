import inspect
from typing import get_type_hints
from .Transaction import predict_class, get_transaction_details

functions = {
    'Transaction_get_transaction_details': get_transaction_details,
    'Transaction_predict_class': predict_class
}

def generate_tool_object(func):
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    param_descriptions = parse_docstring(func)
    parameters = []
    
    for name in signature.parameters.keys():
        param_type = type_hints.get(name, str)
        parameters.append({
            "name": name,
            "type": get_type_string(param_type),
            "description": param_descriptions.get(name, f"The {name} parameter.")
        })
    
    module_name = func.__module__.split('.')[-1]
    function_name = func.__name__
    full_name = f"{module_name}_{function_name}"
    
    tool_object = {
        "type": "function",
        "function": {
            "name": full_name,
            "description": func.__doc__.strip().split("\n")[0] if func.__doc__ else "No description provided.",
            "parameters": {
                "type": "object",
                "properties": {param["name"]: {"type": param["type"], "description": param["description"]} for param in parameters},
                "required": [param["name"] for param in parameters]
            },
        }
    }
    return tool_object


def get_type_string(annotation):
    if annotation == str:
        return "string"
    elif annotation == int:
        return "integer"
    elif annotation == list:
        return "array"
    else:
        return "string"


def parse_docstring(func):
    docstring = inspect.getdoc(func)
    param_descriptions = {}
    if docstring:
        lines = docstring.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("Parameters:"):
                for param_line in lines[i+1:]:
                    if not param_line.strip():
                        continue
                    if '(' in param_line and ')' in param_line:
                        param_name = param_line.split('(')[0].strip()
                        param_description = param_line.split('):')[1].strip() if '):' in param_line else ""
                        param_descriptions[param_name] = param_description
    return param_descriptions

tools = [generate_tool_object(func) for func in functions.values()]
tool_names = [tool['function']['name'] for tool in tools if tool['type'] == 'function']

print(tools)