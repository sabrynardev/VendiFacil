from pydantic import BaseModel, Field


class ProfilePermissionsUpdate(BaseModel):
    permission_codes: list[str] = Field(min_length=1)


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
