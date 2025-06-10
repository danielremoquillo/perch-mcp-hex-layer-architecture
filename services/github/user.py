from schemas.github.user import UserInputSchema, UserResponseSchema
import uuid
import datetime

def create_user(input_data: UserInputSchema) -> UserResponseSchema:
    # Example Process
    item = {
        "sample1": input_data.sample1,
        "sample2": input_data.sample2,
    }
    return UserResponseSchema(**item)
