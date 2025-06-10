from core.data.tool import ToolResponse
from pydantic import Field
from schemas.github.user import UserInputSchema, UserResponseSchema
from services.github.user import create_user

# All tool functions must end with `_tool` to be registered.
def create_user_tool(
    # Note: You can directly use `UserInputSchema` as a parameter schema here.
    # However, when using MCP debugging tools like MCP Inspector, the individual fields
    # (e.g. `sample1`, `sample2`) may not display properly. Defining them explicitly ensures they show up.
    # Either way is correct, if updating or stuff that needs json, It is recommend to use the schema
    sample1: str = Field(..., description="The sample1 of the user."),
    sample2: str = Field(..., description="The sample2 of the user.")
) -> ToolResponse:
    """
    Creates a new user with the provided sample1 and sample2.
    """
    # Calling to service
    user = create_user(UserInputSchema.model_validate({"sample1": sample1, "sample2": sample2}))
    if not user:
        return ToolResponse(status="error", message="User creation failed.")

    return ToolResponse(
        status="success",
        message="User created successfully",
        data=UserResponseSchema.model_validate(user)
    )
