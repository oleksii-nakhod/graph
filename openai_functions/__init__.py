import os
import importlib

def load_functions():
    functions = {}
    base_dir = os.path.dirname(__file__)
    
    for category in os.listdir(base_dir):
        category_dir = os.path.join(base_dir, category)
        if os.path.isdir(category_dir):
            for file_name in os.listdir(category_dir):
                if file_name.endswith('.py') and file_name != '__init__.py':
                    module_name = f"openai_functions.{category}.{file_name[:-3]}"
                    module = importlib.import_module(module_name)
                    function_name = file_name[:-3]
                    function = getattr(module, function_name)
                    functions[f"{category}.{function_name}"] = {
                        "function": function,
                        "category": category,
                        "name": function_name,
                        "description": function.__doc__,
                    }
    
    return functions

functions = load_functions()
print(functions)