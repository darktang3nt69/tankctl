from app.schemas.error import ErrorResponse

@app.get("/openapi-error-model", response_model=ErrorResponse, include_in_schema=False)
def _openapi_error_model():
    return {"detail": "This is a dummy endpoint to include ErrorResponse in OpenAPI."} 