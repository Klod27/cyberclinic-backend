from pydantic import BaseModel
from typing import List, Optional

class ControlResult(BaseModel):
    control_id: str
    title: str
    status: str
    severity: str
    description: str
    remediation: Optional[str]

class ScanResponse(BaseModel):
    score: float
    passed: int
    failed: int
    controls: List[ControlResult]