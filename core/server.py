import importlib
import inspect
import os
from pathlib import Path # Added for path operations
import yaml # Added for perch.lock operations
from mcp.server.fastmcp import FastMCP

class MCPServer:
    def __init__(self, name: str = "Perch MCP Server"):
        self.mcp = FastMCP(name)
        self._sync_integrations_with_lock_file() # Call sync on init
        self.register_tools()

    def _sync_integrations_with_lock_file(self):
        perch_lock_path = Path("perch.lock")
        integrations_dir = Path("integrations")

        if not perch_lock_path.exists():
            print("Warning: perch.lock not found. Cannot sync integrations.")
            return

        try:
            with open(perch_lock_path, "r") as f:
                perch_data = yaml.safe_load(f)
        except Exception as e:
            print(f"Error reading perch.lock: {e}")
            return

        if "integrations" not in perch_data or not isinstance(perch_data["integrations"], list):
            perch_data["integrations"] = []

        # Get integrations from file system
        fs_integrations = {d.name for d in integrations_dir.iterdir() if d.is_dir() and not d.name.startswith('__')}

        # Get integrations from perch.lock
        lock_integrations = set(perch_data["integrations"])

        new_integrations = fs_integrations - lock_integrations
        removed_integrations = lock_integrations - fs_integrations

        if new_integrations or removed_integrations:
            print("Syncing integrations in perch.lock...")
            perch_data["integrations"] = sorted(list(fs_integrations))
            try:
                with open(perch_lock_path, "w") as f:
                    yaml.dump(perch_data, f, sort_keys=False)
                if new_integrations:
                    print(f"Added new integrations to perch.lock: {', '.join(new_integrations)}")
                if removed_integrations:
                    print(f"Removed integrations from perch.lock: {', '.join(removed_integrations)}")
            except Exception as e:
                print(f"Error writing to perch.lock during sync: {e}")

    def register_tools(self, tools_path='interfaces/tools'):
        for root, _, files in os.walk(tools_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    module_path = os.path.join(root, file)
                    module_name = os.path.splitext(os.path.relpath(module_path, tools_path))[0].replace(os.sep, '.')

                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)

                    try:
                        spec.loader.exec_module(module)
                    except Exception as e:
                        print(f"❌ Failed to import {module_path}: {e}")
                        continue

                    functions = sorted(
                        inspect.getmembers(module, inspect.isfunction),
                        key=lambda item: item[0]
                    )

                    for name, func in functions:
                        if name.endswith('_tool'):
                            exposed_name = name.replace('_tool', '')
                            decorated = self.mcp.tool(name=exposed_name)(func)
                            setattr(self, exposed_name, decorated)
                            print(f"✅ Registered tool: {exposed_name}")

    def run(self, transport: str = "streamable-http"):
        self.mcp.run(transport=transport)
