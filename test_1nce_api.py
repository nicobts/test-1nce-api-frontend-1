"""
Simple FastAPI service to test 1NCE API authentication and data fetching.

Run with: uvicorn test_1nce_api:app --reload --port 8000
Then visit: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="1NCE API Test Service",
    description="Backend API for 1NCE IoT Management.\n\n[**Go to Streamlit Frontend**](/)",
    version="1.0.0"
)

# Configuration - set these as environment variables or update directly
USERNAME = os.getenv("ONCE_USERNAME", "your_username_here")
PASSWORD = os.getenv("ONCE_PASSWORD", "your_password_here")
# Organization ID is optional - if not provided, it will be fetched from the token
ORGANIZATION_ID = os.getenv("ONCE_ORGANIZATION_ID", None)

TOKEN_URL = "https://api.1nce.com/management-api/oauth/token"
BASE_URL = "https://api.1nce.com/management-api/v1"

# In-memory token storage (for testing only)
token_cache = {
    "access_token": None,
    "expires_at": None,
    "organization_id": None
}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class HealthResponse(BaseModel):
    status: str
    authenticated: bool
    token_expires_in: Optional[int] = None
    error: Optional[str] = None


async def get_access_token() -> str:
    """Get or refresh the access token using Basic Authentication."""

    # Check if we have a valid cached token
    if (token_cache["access_token"] and
        token_cache["expires_at"] and
        datetime.now() < token_cache["expires_at"]):
        return token_cache["access_token"]

    # Request new token using Basic Authentication (Base64 encoded credentials)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                TOKEN_URL,
                auth=(USERNAME, PASSWORD),  # httpx handles Basic Auth encoding automatically
                data={"grant_type": "client_credentials"},  # Required by 1NCE API
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            data = response.json()
            token_cache["access_token"] = data["access_token"]
            # Set expiry with 5 minute buffer
            token_cache["expires_at"] = datetime.now() + timedelta(seconds=data["expires_in"] - 300)
            
            # Extract organization ID from token if not already set
            # The token response may include organization info
            if not ORGANIZATION_ID and "organisation" in data:
                token_cache["organization_id"] = data["organisation"].get("id")
            elif not ORGANIZATION_ID and "organization" in data:
                token_cache["organization_id"] = data["organization"].get("id")
            else:
                token_cache["organization_id"] = ORGANIZATION_ID
            
            return data["access_token"]
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Failed to get access token: {str(e)}")


def get_org_id() -> str:
    """Get the organization ID from cache or environment."""
    return token_cache.get("organization_id") or ORGANIZATION_ID or ""


async def make_api_request(endpoint: str) -> Dict[Any, Any]:
    """Make an authenticated request to the 1NCE API."""
    token = await get_access_token()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}{endpoint}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=getattr(e.response, 'status_code', 500),
                detail=f"API request failed: {str(e)}"
            )


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint that verifies authentication."""
    try:
        token = await get_access_token()
        
        expires_in = None
        if token_cache["expires_at"]:
            expires_in = int((token_cache["expires_at"] - datetime.now()).total_seconds())
        
        return {
            "status": "healthy",
            "authenticated": True,
            "token_expires_in": expires_in
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "authenticated": False,
            "token_expires_in": None,
            "error": str(e)
        }


@app.get("/test-auth")
async def test_authentication():
    """Test authentication by requesting a token."""
    try:
        token = await get_access_token()
        return {
            "success": True,
            "message": "Authentication successful",
            "token_prefix": token[:20] + "...",
            "expires_at": token_cache["expires_at"].isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/sims")
async def get_sims(page: int = 1, page_size: int = 50):
    """
    Fetch list of SIMs.
    
    Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 500)
    """
    org_id = get_org_id()
    endpoint = f"/sims?organisationId={org_id}&page={page}&pageSize={page_size}"
    return await make_api_request(endpoint)


@app.get("/sims/{iccid}")
async def get_sim_details(iccid: str):
    """
    Get details for a specific SIM by ICCID.
    
    Parameters:
    - iccid: The ICCID of the SIM card
    """
    endpoint = f"/sims/{iccid}"
    return await make_api_request(endpoint)


@app.get("/sims/{iccid}/quota")
async def get_sim_quota(iccid: str):
    """
    Get quota information for a specific SIM.
    
    Parameters:
    - iccid: The ICCID of the SIM card
    """
    endpoint = f"/sims/{iccid}/quota"
    return await make_api_request(endpoint)


@app.get("/sims/{iccid}/usage")
async def get_sim_usage(
    iccid: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get usage data for a specific SIM card.

    Parameters:
    - iccid: The ICCID of the SIM card
    - start_date: Start date (YYYY-MM-DD format, defaults to 30 days ago)
    - end_date: End date (YYYY-MM-DD format, defaults to today)
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    endpoint = f"/sims/{iccid}/usage?startDate={start_date}&endDate={end_date}"
    return await make_api_request(endpoint)


@app.get("/sims/{iccid}/sms")
async def get_sim_sms(
    iccid: str,
    page: int = 1,
    page_size: int = 50
):
    """
    Get SMS messages for a specific SIM card.

    Parameters:
    - iccid: The ICCID of the SIM card
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50)
    """
    endpoint = f"/sims/{iccid}/sms?page={page}&pageSize={page_size}"
    return await make_api_request(endpoint)


@app.get("/sims/{iccid}/events")
async def get_sim_events(
    iccid: str,
    page: int = 1,
    page_size: int = 50
):
    """
    Get diagnostic/event information for a specific SIM card.

    Parameters:
    - iccid: The ICCID of the SIM card
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50)
    """
    endpoint = f"/sims/{iccid}/events?page={page}&pageSize={page_size}"
    return await make_api_request(endpoint)


@app.get("/sim-status-summary")
async def get_sim_status_summary():
    """
    Get a summary of SIM statuses (count by status).
    This endpoint fetches all SIMs and aggregates by status.
    """
    try:
        org_id = get_org_id()
        sims_data = await make_api_request(
            f"/sims?organisationId={org_id}&page=1&pageSize=500"
        )
        
        # Aggregate by status
        status_counts = {}
        for sim in sims_data.get("items", []):
            status = sim.get("status", {}).get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_sims": len(sims_data.get("items", [])),
            "status_breakdown": status_counts,
            "raw_data": sims_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("""
    1NCE API Test Service
    =====================
    
    Before running, set your credentials:
    export ONCE_USERNAME='your_username'
    export ONCE_PASSWORD='your_password'
    
    Organization ID is optional (will be auto-detected from token):
    export ONCE_ORGANIZATION_ID='your_org_id'
    
    Or update them directly in the script.
    
    Starting server...
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
