from pydantic import BaseModel


class FunnelUpdate(BaseModel):
    funnel_config: dict


class TenantResponse(BaseModel):
    id: str
    name: str
    funnel_config: dict

    model_config = {"from_attributes": True}
