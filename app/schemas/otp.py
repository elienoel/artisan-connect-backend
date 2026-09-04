from pydantic import BaseModel, Field

from app.models.otp import OtpChannel


class OtpRequest(BaseModel):
    channel: OtpChannel


class OtpVerify(BaseModel):
    channel: OtpChannel
    code: str = Field(..., min_length=6, max_length=6)
