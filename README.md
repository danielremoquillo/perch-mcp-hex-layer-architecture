# MCP HexLayer Architecture Guide

This guide provides step-by-step instructions on how to set up an MCP server following a MCP HexLayer Architecture. It outlines this architectural pattern and serves as a template for building robust and maintainable MCP servers from scratch using `uv` and following the MCP Python SDK recommendations. It covers environment setup, manual creation of core files and directories, configuration, and how to add new functionalities.

## 1. Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+**: The project is built with Python.
- **`uv`**: For fast and efficient Python project and dependency management.

## 2. Architectural Overview

This guide adheres to a **MCP HexLayer Architecture**. This design promotes a clear separation of concerns, enhancing maintainability, scalability, and testability by assigning distinct responsibilities to each layer, consistent with the principles of **Clean Architecture** and **Hexagonal Architecture (Ports and Adapters)**. The primary layers are:

- **Integration Layer (`integrations/`)**: Manages interactions with external systems and third-party services. It abstracts away the complexities of external APIs.
- **Service Layer (`services/`)**: Encapsulates the core business logic and orchestrates operations across different components. It acts as the central hub for application features.
- **Interface Layer (`interfaces/`)**: Defines the public API of the MCP server, exposing its capabilities as tools (actions) and resources (data access points) to clients.
- **Data Layer (`schemas/`)**: Ensures data integrity through validation and serialization schemas.
- **Core Layer (`core/`)**: Contains foundational components like custom exceptions, common utilities, and cross-cutting concerns.

This layered approach facilitates independent development, testing, and allows for technology changes within a layer with minimal impact on others.

## 3. Project Initialization (From Scratch)

### Step 2.1: Create Your Project Directory

Start by creating the main directory for your new MCP server project. Let's name it `my-mcp-server`.

```bash
mkdir my-mcp-server
cd my-mcp-server
```

### Step 2.2: Initialize `uv` Project and Virtual Environment

Initialize a `uv` project in the current directory. This will create a `.venv` virtual environment and a `pyproject.toml` file.

```bash
uv init .
```

This command sets up the current directory (`my-mcp-server/`) as your `uv`-managed project root.

### Step 2.3: Install Core MCP Dependencies

Add the `mcp[cli]` dependency to your new project. This provides the core MCP server functionalities and command-line tools.

```bash
uv add "mcp[cli]"
```

This command will install `mcp-server` and its dependencies into your project's virtual environment.

### Step 2.4: Create Core Project Structure and Files

Now, manually create the essential directories and files that form the foundation of your MCP server structure. Note that `[integration_name]` is a placeholder for your specific integration (e.g., `database`, `storage`, `api`). This name should be consistent across `integrations/`, `interfaces/resources/`, `interfaces/tools/`, `schemas/`, and `services/` for a given integration.

```bash
# Create core architectural directories
mkdir core integrations interfaces schemas services
mkdir core/exceptions core/data
mkdir integrations/[integration_name] # e.g., integrations/github
mkdir interfaces/prompts interfaces/resources interfaces/tools
mkdir interfaces/resources/[integration_name] # e.g., interfaces/resources/github
mkdir interfaces/tools/[integration_name] # e.g., interfaces/tools/github
mkdir schemas/[integration_name] # e.g., schemas/github
mkdir services/[integration_name] # e.g., services/github

# Create core application files
touch main.py
touch core/server.py
```

### Step 2.5: Populate Core Files

Now, add the content to `main.py` and `core/server.py`.

**`main.py`**:

```python
from core.server import MCPServer

if __name__ == "__main__":
    server = MCPServer(name="My New MCP Server")
    server.run()
```

**`core/server.py`**:

```python
import importlib
import inspect
import os
from mcp.server.fastmcp


class MCPServer:
    def __init__(self, name: str = "ToyChad MCP Server"):
        self.mcp = FastMCP(name)
        self.register_tools()


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

                    # Sort functions alphabetically by name before registering
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
```

## 3. Configuration

This template is designed to be configurable. For a new project, you would typically:

1.  **Create a `config/` directory**:
    ```bash
    mkdir config
    ```
2.  **Add `settings.py` or `environment_variables.py`**:
    Create `config/settings.py` to manage application settings.

    Example `config/settings.py`:

    ```python
    import os

    # Example: Application environment
    APP_ENV = os.getenv("APP_ENV", "development")
    # Example: A generic service endpoint
    SERVICE_ENDPOINT = os.getenv("SERVICE_ENDPOINT", "http://localhost:8080/api")

    # Add other configurations as needed
    ```

    You would then load these settings in `main.py`.

3.  **Environment Variables**:
    Set environment variables before running the server.

    ```bash
    export APP_ENV="production"
    export SERVICE_ENDPOINT="https://api.example.com"
    # ... other environment variables
    ```

## 4. Extending the Project: Adding a Simple Logging Tool

This section demonstrates how to add a simple entity management tool that showcases the architectural pattern (schema, service, interface tool) without requiring external dependencies. This tool will use the `ToolResponse` schema for structured output and demonstrate `[Action]**entity**InputSchema` and `**entity**ResponseSchema`.

### Understanding `ToolResponse`

The `ToolResponse` class (defined in `core/data/tool.py` in the original template) is a standardized way to return results from MCP tools. It is now a `dataclass` for simple data container purposes. It provides:

- `status: str`: Indicates the outcome (e.g., "success", "error").
- `message: Optional[str]`: A human-readable message.
- `data: Optional[Any]`: The actual result data, which can be any serializable Python object.

### The Schema -> Service -> Tool Flow

Adding new functionalities to this MCP server typically follows a consistent, repetitive pattern across the layers:

1.  **Define Schemas (`schemas/`)**: Start by defining the input and output data structures (Pydantic models) for your new feature. This ensures data integrity and clear contracts.
2.  **Implement Service Logic (`services/`)**: Develop the core business logic in the service layer, utilizing the defined schemas for input validation and output formatting. Services should focus on the "what" (the business operation) and return raw data.
3.  **Expose as a Tool (`interfaces/`)**: Create the public-facing tool in the interface layer. This tool acts as a wrapper, taking client input, calling the relevant service function, and then formatting the service's raw output into a standardized `ToolResponse`.

This structured flow ensures a clear separation of concerns and promotes maintainability as your server grows.

### CGUDL (Create, Get, Update, Delete, List) Pattern

When designing and implementing tools and resources, we adhere to the CGUDL pattern to ensure consistency and predictability across the MCP server's functionalities. This pattern defines the standard operations for managing entities:

- **Create**: For adding new entities.
- **Get**: For retrieving a single entity by its identifier.
- **Update**: For modifying existing entities.
- **Delete**: For removing entities.
- **List**: For retrieving collections of entities, often with filtering or pagination.

By following CGUDL, clients can expect a consistent interface for interacting with different types of data and functionalities within the MCP server.

### Step 4.1: Define Schemas (`schemas/`)

First, create the `schemas/[integration_name]/` directory and the `user.py` file within it.

```bash
mkdir schemas/[integration_name]
touch schemas/[integration_name]/user.py
```

Then, add content to `schemas/[integration_name]/user.py`:

```python
# schemas/[integration_name]/user.py
from pydantic import BaseModel
from typing import Optional

class CreateUserInputSchema(BaseModel):
    name: str
    email: str

class UserResponseSchema(BaseModel):
    id: str
    name: str
    email: str
    created_at: str
```

And add content to `core/data/tool.py` (if it doesn't exist, create it):

```python
# core/data/tool.py
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class ToolResponse:
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None
```

### Step 4.2: Implement Service Logic (`services/`)

Create the `services/[integration_name]/` directory and the `user.py` file within it.

```bash
mkdir services/[integration_name]
touch services/[integration_name]/user.py
```

Then, add content to `services/[integration_name]/user.py`:

```python
# services/[integration_name]/user.py
from schemas.[integration_name].user import CreateUserInputSchema, UserResponseSchema
import uuid
import datetime

def create_user(input_data: CreateUserInputSchema) -> UserResponseSchema:
    user_id = str(uuid.uuid4())
    created_at = datetime.datetime.now().isoformat()

    item = {
        "id": user_id,
        "name": input_data.name,
        "email": input_data.email,
        "created_at": created_at
    }

    # Process it here eg. Saving to database
    # [integration].save(item)

    return UserResponseSchema(**item)
```

### Step 4.3: Expose as a Tool (`interfaces/`)

Create the `interfaces/tools/[integration_name]/` directory and the `user.py` file within it.

```bash
mkdir interfaces/tools/[integration_name]
touch interfaces/tools/[integration_name]/user.py
```

Then, add content to `interfaces/tools/[integration_name]/user.py`:

```python
# interfaces/tools/[integration_name]/user.py
from pydantic import Field
from schemas.[integration_name].user import CreateUserInputSchema, UserResponseSchema
from core.data.tool import ToolResponse
from services.[integration_name].user import create_user

# Note: You can directly use `CreateUserInputSchema` as a parameter schema here.
# However, when using MCP debugging tools like MCP Inspector, the individual fields
# (e.g. `name`, `email`) may not display properly. Defining them explicitly ensures they show up.

def create_user_tool(
    name: str = Field(..., description="The name of the user."),
    email: str = Field(..., description="The email address of the user. Must be unique.")
) -> ToolResponse:
    """
    Creates a new user with the provided name and email.
    """

    user = create_user(CreateUserInputSchema.model_validate({"name": name, "email": email}))
    if not user:
        return ToolResponse(status="error", message="User creation failed.")

    return ToolResponse(
        status="success",
        message="User created successfully",
        data=UserResponseSchema.model_validate(user)
    )
```

### Step 4.4 Naming Convention for Interfaces

When adding tools, resources, or prompts under the `interfaces/` layer, it's important to **follow strict naming conventions** so the MCP server can automatically discover and register them.

### 📛 Required Suffixes

Functions must be named with the following suffixes:

| Interface Type | Required Suffix | Directory               | Example Function Name    |
| -------------- | --------------- | ----------------------- | ------------------------ |
| Tools          | `_tool`         | `interfaces/tools/`     | `create_user_tool`       |
| Resources      | `_resource`     | `interfaces/resources/` | `get_user_resource`      |
| Prompts        | `_prompt`       | `interfaces/prompts/`   | `welcome_message_prompt` |

> ⚠️ **If you do not follow these suffixes, your function will not be registered or exposed to MCP clients.**

### ✅ Why This Matters

Your `MCPServer` implementation automatically scans and registers any interface function based on these suffixes. This design ensures a clear and predictable method for exposing functionality to the MCP runtime and tools like MCP Inspector.

## 5. Running the Server

Once you have set up your environment and made your desired changes, you can run the MCP server.

```bash
# Ensure your virtual environment is activated
# uv venv activate

# Navigate to the root of your new project (e.g., my-mcp-server/)
python main.py
```

The server will start and listen for MCP client requests. You should see output from the `create_user_tool` if an MCP client invokes it, and the client will receive a `ToolResponse` object.

## 6. Testing

Testing your MCP server ensures that tools and integrations behave correctly across layers. This section focuses on full system behavior using MCP Inspector.

### ✅ MCP Inspector for Manual & Interactive Testing

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is a developer tool that provides a UI and CLI for testing and debugging MCP servers. It’s ideal for:

- Manually invoking tools
- Exploring tool parameters and schemas
- Debugging validation errors
- Quickly iterating on service logic

---

#### 🖥️ UI Mode (Browser Interface)

Start your server:

```
python main.py
```

Then, in a new terminal:

```
npx @modelcontextprotocol/inspector
```

This launches the UI at:

```
http://localhost:6274
```

In the UI, you can:

- Browse tools and resources
- Fill in tool inputs (e.g., `name`, `email`)
- Submit a request and view `ToolResponse` JSON
- Inspect errors, logs, and streaming output (if enabled)

---

## 7. Prompts and Resources (Upcoming)

Support for `prompts/` and `resources/` is planned as part of future development.

These features are key to a complete MCP server implementation and will follow the same layered architecture approach used for tools and services.

### 📝 Prompts (interfaces/prompts/)

Prompts define reusable prompt templates for LLM interaction. In the future, this layer will allow:

- Defining structured prompts using Pydantic models
- Parameterizing prompts for dynamic responses
- Registering prompts for UI and CLI invocation

**Status:** Not implemented yet. Placeholder structure is scaffolded.

### 🌐 Resources (interfaces/resources/)

Resources expose read-only data endpoints. These may represent:

- External data lookups (e.g., GitHub repositories, user info)
- Internal data derived from services or integrations
- Read-only interfaces for client apps

**Status:** Not implemented yet. Directories and imports can be prepared, but logic is pending.

---

## 8. Exception Handling (Upcoming)

A key aspect of robust MCP server development is consistent error handling. In future iterations, an exception wrapper will be introduced to standardize how errors from the service and integration layers are presented to MCP clients.

### 📝 Exception Wrapper

This wrapper will:

- **Catch exceptions**: Intercept errors raised by service or integration functions.
- **Format into `ToolResponse`**: Convert caught exceptions into a `ToolResponse` object with `status="error"` and a descriptive `message`.
- **Centralize error logic**: Ensure all tool invocations return a consistent error structure, improving client-side error handling.

**Status:** Not implemented yet. This will be a core component for production-ready servers.

---

## 9. Credits

GitHub: [@danielremoquillo](https://github.com/danielremoquillo)  
Email: danielremoquillo.se@gmail.com

## References

- https://github.com/modelcontextprotocol/python-sdk
- https://github.com/modelcontextprotocol/inspector
- https://github.com/astral-sh/uv
