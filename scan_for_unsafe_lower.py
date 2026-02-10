
import ast
import os

def check_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            content = f.read()
            tree = ast.parse(content, filename=filepath)
        except Exception:
            return []
    
    unsafe_calls = []
    
    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "lower":
                obj = node.func.value
                
                # Check for safe patterns
                is_safe = False
                
                # 1. str(x).lower()
                if isinstance(obj, ast.Call) and isinstance(obj.func, ast.Name) and obj.func.id == "str":
                    is_safe = True
                
                # 2. "literal".lower()
                elif isinstance(obj, ast.Constant) and isinstance(obj.value, str):
                    is_safe = True
                
                # 3. df['col'].str.lower()
                elif isinstance(obj, ast.Attribute) and obj.attr == "str":
                    is_safe = True
                
                if not is_safe:
                    try:
                        code_snippet = ast.unparse(node)
                    except:
                        code_snippet = "???"
                    unsafe_calls.append((node.lineno, code_snippet))
            self.generic_visit(node)

    Visitor().visit(tree)
    return unsafe_calls

def main():
    import sys
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    skip_dirs = {".git", ".venv", "__pycache__", "node_modules", ".agent", ".system_generated"}
    
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                issues = check_file(path)
                if issues:
                    print(f"File: {path}")
                    for lineno, code in issues:
                        print(f"  Line {lineno}: {code}")

if __name__ == "__main__":
    main()
