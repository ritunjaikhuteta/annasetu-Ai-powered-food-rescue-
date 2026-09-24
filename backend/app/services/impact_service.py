"""Impact Service domain boundary."""
from app.db.supabase import SupabaseClient


class ImpactService:
    def __init__(self, db: SupabaseClient):
        self.db = db
