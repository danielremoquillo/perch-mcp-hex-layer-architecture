from pydantic import BaseModel
from typing import Optional

class UserInputSchema(BaseModel):
    sample1: str
    sample2: str

class UserResponseSchema(BaseModel):
    sample1: str
    sample2: str
    # Add other fields as necessary, e.g., id, created_at
