"""AI Service domain boundary."""
from app.db.supabase import SupabaseClient


class AIService:
    def __init__(self, db: SupabaseClient):
        self.db = db
