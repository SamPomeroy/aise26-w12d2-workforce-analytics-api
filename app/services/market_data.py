import httpx
from typing import Optional, Dict, Any
from app.config import settings


async def fetch_bls_data(series_id: str) -> Optional[Dict[str, Any]]:
    """
    fetch labor statistics from bureau of labor statistics api
    demonstrates async external api call pattern
    
    series_id examples:
    - CES0000000001: total nonfarm employment
    - LNS14000000: unemployment rate
    """
    if not settings.bls_api_key:
        # return mock data if no api key configured
        return {
            "status": "mock",
            "message": "no bls api key configured, returning mock data",
            "series_id": series_id,
            "data": [
                {"year": "2024", "period": "M01", "value": "157000"},
                {"year": "2024", "period": "M02", "value": "157200"},
            ]
        }
    
    url = settings.bls_api_url
    headers = {"Content-Type": "application/json"}
    payload = {
        "seriesid": [series_id],
        "registrationkey": settings.bls_api_key,
        "startyear": "2023",
        "endyear": "2024"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"bls api error: {e}")
        return None


async def analyze_skill_demand(skill_name: str) -> Dict[str, Any]:
    """
    placeholder for analyzing skill demand across job postings
    in a real system this might call multiple external apis or ml models
    demonstrates background task processing pattern
    """
    # simulate async processing
    await httpx.AsyncClient().aclose()
    
    return {
        "skill": skill_name,
        "demand_score": 75.5,
        "trending": "up",
        "related_skills": ["python", "sql", "data-analysis"],
        "avg_salary": 95000
    }
