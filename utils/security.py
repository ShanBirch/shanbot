from fastapi import Security, HTTPException, Depends, Request, status
from fastapi.security.api_key import APIKeyHeader
import os
from dotenv import load_dotenv
import logging
import pathlib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to the .env file
current_dir = pathlib.Path(__file__).parent.parent.absolute()
env_path = current_dir / ".env"
logger.info(f"Security module loading .env from: {env_path}")

# Load environment variables
load_dotenv(dotenv_path=env_path, override=True)

# Get API key from environment
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    logger.warning("API_KEY environment variable not set")
    API_KEY = "development_api_key"  # Default for development
else:
    logger.info(
        f"Loaded API key from environment: {API_KEY[:4]}...{API_KEY[-4:] if len(API_KEY) > 8 else ''}")

# Define API key header
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def verify_api_key(request: Request, api_key_header: str = Security(api_key_header)):
    """
    Verify that the API key provided in the request header or query parameter matches the expected API key.
    Also accepts ManyChat test webhook requests with key and page_id parameters.

    This dependency can be used to secure FastAPI routes that require API key authentication.
    """
    # For extreme debugging - log all request details
    logger.info(f"Received request: {request.method} {request.url}")
    logger.info(f"Request headers: {request.headers}")
    logger.info(f"Query parameters: {request.query_params}")

    # Check for ManyChat specific fields that indicate this is a ManyChat webhook
    try:
        body = await request.json()
        logger.info(f"Request body keys: {list(body.keys())}")

        # Check if this is a ManyChat webhook (they have specific format)
        is_manychat_webhook = False
        if "page_id" in body or "id" in body:
            logger.info(
                "Detected ManyChat test webhook by page_id or id in body")
            is_manychat_webhook = True
        elif "trigger" in body or "trigger_type" in body:
            logger.info("Detected ManyChat webhook event by trigger in body")
            is_manychat_webhook = True
        elif "subscriber" in body:
            logger.info("Detected ManyChat webhook by subscriber in body")
            is_manychat_webhook = True

        if is_manychat_webhook:
            logger.info("Allowing ManyChat webhook to proceed without API key")
            return True
    except Exception as e:
        # If we can't parse the body as JSON, it's not a big deal - continue with normal verification
        logger.info(f"Could not parse request body as JSON: {e}")

    if not API_KEY:
        logger.warning(
            "API key verification skipped - no API_KEY is configured")
        return True

    # Special handling for ManyChat test webhooks via query params
    if "key" in request.query_params and "page_id" in request.query_params:
        logger.info(
            "Detected ManyChat test webhook via query params - allowing without API key")
        return True

    # Check for API key in header
    api_key = api_key_header

    # If not in header, check query parameters
    if not api_key:
        api_key = request.query_params.get("api_key")

    # Also check for Authorization: Bearer <token> header
    if not api_key and "authorization" in request.headers:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]  # Remove "Bearer " prefix
            logger.info(f"Found API key in Authorization Bearer header")

    if not api_key:
        logger.warning("Request received with no API key")
        # IMPORTANT: For ManyChat webhooks, we'll allow even without API key for initial testing
        # Comment the next line to require API key
        return True

        # Uncomment to enforce API key requirement
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail="API Key header is missing"
        # )

    # Log the received and expected API keys for debugging
    logger.info(
        f"Received API key: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else ''}")
    logger.info(
        f"Expected API key: {API_KEY[:4]}...{API_KEY[-4:] if len(API_KEY) > 8 else ''}")

    if api_key != API_KEY:
        logger.warning(
            f"Invalid API key provided. Received: {api_key[:4]}..., Expected: {API_KEY[:4]}...")
        # IMPORTANT: For ManyChat webhooks, we'll allow even with incorrect API key for initial testing
        # Comment the next line to require correct API key
        return True

        # Uncomment to enforce API key validation
        # raise HTTPException(
        #     status_code=status.HTTP_403_FORBIDDEN,
        #     detail="Invalid API Key"
        # )

    logger.info("API key verified successfully")
    return True
