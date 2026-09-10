from pydantic import BaseModel, ConfigDict, Field


class ProfilePermissionsUpdate(BaseModel):
    permission_codes: list[str] = Field(min_length=1)


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    module: str

class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    active: bool
    is_system: bool
    permissions: list[PermissionResponse]
