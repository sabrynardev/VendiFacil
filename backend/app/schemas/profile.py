from pydantic import BaseModel


class PermissionResponse(BaseModel):
    code: str
    name: str
    module: str

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    id: int
    name: str
    code: str
    active: bool
    is_system: bool
    permissions: list[PermissionResponse]

    class Config:
        from_attributes = True
