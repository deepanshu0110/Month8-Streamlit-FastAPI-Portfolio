from fastapi import Header, HTTPException, status

VALID_API_KEYS = {
    "freelancehub-2024-secret": "admin",
    "client-readonly-key-001":  "readonly",
}

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return VALID_API_KEYS[x_api_key]