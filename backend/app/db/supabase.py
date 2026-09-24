"""Centralized Supabase Database and Auth Client."""

import logging
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.utils.exceptions import AppException, NotFoundException

logger = logging.getLogger("annasetu.db")


class SupabaseClient:
    """Server-side client for interacting with Supabase REST (PostgREST) and Auth APIs."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.SUPABASE_URL).rstrip("/")
        self.secret_key = secret_key or settings.SUPABASE_SECRET_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.secret_key)

    def _get_headers(self, user_token: Optional[str] = None) -> Dict[str, str]:
        auth_bearer = user_token if user_token else self.secret_key
        headers = {
            "apikey": self.secret_key,
            "Authorization": f"Bearer {auth_bearer}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        return headers

    async def verify_user_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Supabase JWT token against the Supabase Auth server."""
        if not self.is_configured:
            logger.warning("Supabase credentials not configured. Cannot verify JWT against Supabase.")
            return None

        url = f"{self.base_url}/auth/v1/user"
        headers = {
            "apikey": self.secret_key,
            "Authorization": f"Bearer {token}",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                logger.warning("Supabase auth verification failed with status: %s", response.status_code)
                return None
        except httpx.RequestError as exc:
            logger.error("Supabase auth connection error: %s", exc)
            return None

    async def get_by_id(
        self,
        table: str,
        id_value: str,
        id_column: str = "id",
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single record by its ID or identifier column."""
        if not self.is_configured:
            return None

        url = f"{self.base_url}/rest/v1/{table}?{id_column}=eq.{id_value}&select=*"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return data[0] if data else None
                return None
        except httpx.RequestError as exc:
            logger.error("Supabase GET error on %s: %s", table, exc)
            raise AppException("Database query error occurred.", status_code=502)

    async def update_by_id(
        self,
        table: str,
        id_value: str,
        payload: Dict[str, Any],
        id_column: str = "id",
    ) -> Dict[str, Any]:
        """Update a single record by its ID column using server-side service credentials."""
        if not self.is_configured:
            raise AppException("Supabase is not configured on the backend.", status_code=503)

        url = f"{self.base_url}/rest/v1/{table}?{id_column}=eq.{id_value}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.patch(url, headers=headers, json=payload)
                if response.status_code in (200, 204):
                    data = response.json() if response.status_code == 200 else []
                    if data:
                        return data[0]
                    # If empty response, fetch the updated record
                    updated = await self.get_by_id(table, id_value, id_column)
                    if updated:
                        return updated
                    raise NotFoundException(f"Resource in {table} not found.")
                logger.error("Supabase update error on %s: %s %s", table, response.status_code, response.text)
                raise AppException("Failed to update database record.", status_code=response.status_code)
        except httpx.RequestError as exc:
            logger.error("Supabase PATCH error on %s: %s", table, exc)
            raise AppException("Database update error occurred.", status_code=502)

    async def insert(self, table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single record into a table."""
        if not self.is_configured:
            raise AppException("Supabase is not configured on the backend.", status_code=503)

        url = f"{self.base_url}/rest/v1/{table}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code in (200, 201):
                    data = response.json()
                    return data[0] if data else payload
                logger.error("Supabase insert error on %s: %s %s", table, response.status_code, response.text)
                raise AppException("Failed to insert database record.", status_code=response.status_code)
        except httpx.RequestError as exc:
            logger.error("Supabase POST error on %s: %s", table, exc)
            raise AppException("Database insert error occurred.", status_code=502)


    async def query(
        self,
        table: str,
        params: Optional[Dict[str, str]] = None,
        select: str = "*",
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query records from a table with PostgREST query parameters."""
        if not self.is_configured:
            return []

        query_params = {"select": select}
        if params:
            query_params.update(params)
        if order:
            query_params["order"] = order
        if limit:
            query_params["limit"] = str(limit)

        url = f"{self.base_url}/rest/v1/{table}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=query_params)
                if response.status_code == 200:
                    return response.json()
                logger.error("Supabase query error on %s: %s %s", table, response.status_code, response.text)
                return []
        except httpx.RequestError as exc:
            logger.error("Supabase query connection error on %s: %s", table, exc)
            raise AppException("Database query error occurred.", status_code=502)

    async def upsert(
        self,
        table: str,
        payload: Dict[str, Any],
        on_conflict: str = "id",
    ) -> Dict[str, Any]:
        """Upsert a record with conflict resolution."""
        if not self.is_configured:
            raise AppException("Supabase is not configured on the backend.", status_code=503)

        url = f"{self.base_url}/rest/v1/{table}?on_conflict={on_conflict}"
        headers = self._get_headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code in (200, 201):
                    data = response.json()
                    return data[0] if data else payload
                logger.error("Supabase upsert error on %s: %s %s", table, response.status_code, response.text)
                raise AppException("Failed to upsert database record.", status_code=response.status_code)
        except httpx.RequestError as exc:
            logger.error("Supabase upsert error on %s: %s", table, exc)
            raise AppException("Database upsert error occurred.", status_code=502)

    async def compare_and_swap_update(
        self,
        table: str,
        id_value: str,
        expected_field: str,
        expected_val: Any,
        new_values: Dict[str, Any],
        id_column: str = "id",
    ) -> Optional[Dict[str, Any]]:
        """Atomically update a record only if expected_field equals expected_val (optimistic lock)."""
        if not self.is_configured:
            raise AppException("Supabase is not configured on the backend.", status_code=503)

        url = f"{self.base_url}/rest/v1/{table}?{id_column}=eq.{id_value}&{expected_field}=eq.{expected_val}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.patch(url, headers=headers, json=new_values)
                if response.status_code in (200, 204):
                    data = response.json() if response.status_code == 200 else []
                    return data[0] if data else None
                return None
        except httpx.RequestError as exc:
            logger.error("Supabase CAS update error on %s: %s", table, exc)
            raise AppException("Database atomic update error occurred.", status_code=502)

    async def _raw_delete(
        self,
        table: str,
        id_value: str,
        id_column: str = "id",
    ) -> bool:
        """Delete a single record by ID. Intended for admin/development-only workflows (demo reset).

        Supabase REST API deletes by filter on PostgREST. Returns True if status 200/204.
        """
        if not self.is_configured:
            return False

        url = f"{self.base_url}/rest/v1/{table}?{id_column}=eq.{id_value}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(url, headers=headers)
                return response.status_code in (200, 204)
        except httpx.RequestError as exc:
            logger.warning("Supabase delete error on %s: %s", table, exc)
            return False


# Centralized singleton instance
supabase_client = SupabaseClient()


def get_supabase_client() -> SupabaseClient:
    """Dependency injector for SupabaseClient."""
    return supabase_client
