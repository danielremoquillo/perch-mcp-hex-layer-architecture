from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class ToolResponse:
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None
