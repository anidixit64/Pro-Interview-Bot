# backend/config.py
# Or you can name it secrets.py - convention varies, config.py is also common
# for application-wide settings, including secrets retrieval logic.

import os
import sys
from google.cloud import secretmanager_v1
# Import specific exceptions if you want more granular error handling later
# from google.api_core.exceptions import PermissionDenied, NotFound

# --- Configuration Constants ---

# Your Google Cloud Project ID.
# GCP PaaS services like Cloud Run, App Engine automatically set the 'GCP_PROJECT' env var.
# If running on a VM or other environment, ensure this env var is set or replace
# os.environ.get('GCP_PROJECT') with your actual project ID string,
# though using the env var is more flexible.
PROJECT_ID = 'pro-interview-bot'

# The names of the secrets you created in Google Cloud Secret Manager.
# MAKE SURE THESE MATCH THE NAMES IN YOUR GCP SECRET MANAGER!
OPENAI_SECRET_NAME = "PIBCloud"
GEMINI_SECRET_NAME = "PIBGemini"

# --- Google Cloud Secret Manager Client Singleton ---

_secrets_client = None # Use a leading underscore to indicate it's intended for internal use

def _get_secrets_client():
    """Initializes and returns the Secret Manager client (singleton pattern)."""
    global _secrets_client
    if _secrets_client is None:
        try:
            # The client automatically picks up credentials from the environment
            # when running on GCP with a Service Account attached.
            _secrets_client = secretmanager_v1.SecretManagerServiceClient()
            print("Google Cloud Secret Manager client initialized.")
        except Exception as e:
            # Log initialization errors but might not be fatal until a secret is needed
            print(f"Warning: Could not initialize Google Cloud Secret Manager client: {e}", file=sys.stderr)
            # Depending on your app, this might be a fatal error
            # raise RuntimeError(f"Failed to initialize Secret Manager client: {e}") from e
    return _secrets_client

# --- Secret Retrieval Functions ---

def get_openai_api_key():
    """
    Retrieves the OpenAI API key from Google Cloud Secret Manager.

    Returns:
        str: The OpenAI API key.

    Raises:
        EnvironmentError: If the GCP_PROJECT environment variable is not set.
        RuntimeError: If the secret cannot be retrieved from Secret Manager
                      (e.g., not found, permission denied, network issue).
    """
    if not PROJECT_ID:
        raise EnvironmentError(
            "GCP_PROJECT environment variable not set! "
            "Cannot retrieve secrets. Ensure your GCP environment is configured correctly."
        )

    # Construct the full resource path to the latest version of the secret.
    # Using ':latest' is convenient but be mindful of secret versioning in production.
    secret_path = f"projects/{PROJECT_ID}/secrets/{OPENAI_SECRET_NAME}/versions/latest"

    try:
        client = _get_secrets_client()
        if client is None:
             raise RuntimeError("Secret Manager client failed to initialize.")

        # Access the secret version.
        response = client.access_secret_version(name=secret_path)

        # Extract the payload data (which is bytes) and decode it to a string.
        api_key = response.payload.data.decode('UTF-8')

        # Log that the secret was retrieved, but NEVER log the key itself.
        print(f"Successfully retrieved secret: {OPENAI_SECRET_NAME}")

        return api_key

    # Handle potential exceptions during retrieval
    # You could add specific exceptions like PermissionDenied, NotFound here
    except Exception as e:
        print(f"ERROR retrieving secret '{OPENAI_SECRET_NAME}' from Secret Manager: {e}", file=sys.stderr)
        # Re-raise a runtime error, as the application likely cannot proceed without this key.
        raise RuntimeError(f"Failed to retrieve OpenAI API key from Secret Manager: {e}") from e

def get_gemini_api_key():
    """
    Retrieves the Gemini API key from Google Cloud Secret Manager.
    Note: For Gemini on GCP, Service Account based authentication using
    Google's client libraries is often preferred over API keys. This
    function is useful if you *must* use an API key for some reason.

    Returns:
        str: The Gemini API key.

    Raises:
        EnvironmentError: If the GCP_PROJECT environment variable is not set.
        RuntimeError: If the secret cannot be retrieved from Secret Manager.
    """
    if not PROJECT_ID:
         raise EnvironmentError(
            "GCP_PROJECT environment variable not set! "
            "Cannot retrieve secrets. Ensure your GCP environment is configured correctly."
        )

    secret_path = f"projects/{PROJECT_ID}/secrets/{GEMINI_SECRET_NAME}/versions/latest"

    try:
        client = _get_secrets_client()
        if client is None:
             raise RuntimeError("Secret Manager client failed to initialize.")

        response = client.access_secret_version(name=secret_path)
        api_key = response.payload.data.decode('UTF-8')

        print(f"Successfully retrieved secret: {GEMINI_SECRET_NAME}")

        return api_key

    except Exception as e:
        print(f"ERROR retrieving secret '{GEMINI_SECRET_NAME}' from Secret Manager: {e}", file=sys.stderr)
        raise RuntimeError(f"Failed to retrieve Gemini API key from Secret Manager: {e}") from e

# --- Optional: Initial Secrets Check Function ---

def check_required_secrets():
    """
    Attempts to retrieve all required secrets on application startup
    to verify configuration and permissions.
    Exits the application if any required secret cannot be accessed.
    """
    print("Performing initial check for required secrets in Secret Manager...")
    try:
        # Simply calling the retrieval functions will trigger the access attempt
        # and raise an error if unsuccessful.
        get_openai_api_key()
        get_gemini_api_key()
        print("All required secrets are accessible. Startup check successful.")
    except (EnvironmentError, RuntimeError) as e:
        print(f"FATAL: Failed to access one or more required secrets on startup: {e}", file=sys.stderr)
        print("Please check the following:", file=sys.stderr)
        print(f"- Ensure secrets '{OPENAI_SECRET_NAME}' and '{GEMINI_SECRET_NAME}' exist in Secret Manager in project '{PROJECT_ID}'.", file=sys.stderr)
        print(f"- Ensure the Service Account '{os.environ.get('K_SERVICE_ACCOUNT', 'default')}' attached to your Cloud Run service (or equivalent) has the 'Secret Manager Secret Accessor' role.", file=sys.stderr)
        print("- Ensure the IAM role condition allows access to the specific secret names.", file=sys.stderr)
        print("- Ensure the GCP_PROJECT environment variable is set correctly.", file=sys.stderr)
        sys.exit(1) # Exit the application if secrets are not accessible on startup
    except Exception as e:
        print(f"An unexpected error occurred during secrets startup check: {e}", file=sys.stderr)
        sys.exit(1)


# --- How to Use ---
# In your backend code (e.g., an API endpoint handler):
# from .config import get_openai_api_key, get_gemini_api_key
#
# def handle_openai_request(prompt):
#     try:
#         openai_key = get_openai_api_key()
#         # Use openai_key to initialize the OpenAI client or pass it to a function
#         # ... call OpenAI API ...
#         return result
#     except RuntimeError as e:
#         # Handle the specific error if key retrieval failed
#         print(f"Could not process OpenAI request due to missing key: {e}")
#         # Return an error response to the frontend
#         return {"error": "Failed to access OpenAI key"}, 500 # Example Flask/FastAPI error response

# In your main application startup file (e.g., app.py):
# from .config import check_required_secrets
#
# if __name__ == "__main__": # Or at the start of your app's entry point
#     check_required_secrets() # Verify secrets are accessible before starting the web server
#     # ... then start your Flask/FastAPI app ...