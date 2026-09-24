"""Verification Service domain boundary."""
from app.db.supabase import SupabaseClient


class VerificationService:
    def __init__(self, db: SupabaseClient):
        self.db = db
