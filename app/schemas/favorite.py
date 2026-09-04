from pydantic import BaseModel


class FavoriteStatus(BaseModel):
    is_favorite: bool
