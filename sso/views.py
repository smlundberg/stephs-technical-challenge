import os
from django.core.exceptions import PermissionDenied
from workos import WorkOSClient
import json
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# BASE_DIR is the project root (where manage.py is located)
# views.py is at: python-django-sso-example/sso/views.py
# So we need to go up 2 levels to get to python-django-sso-example/
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path, override=False)  # Don't override existing env vars


# Initialize WorkOS client
# Note: In SDK v5+, we use WorkOSClient instance instead of workos.client module
def get_workos_client():
    """Get WorkOS client instance (initialized lazily)"""
    if not hasattr(get_workos_client, '_instance'):
        # Reload .env file in case it wasn't loaded at import time
        load_dotenv(env_path, override=False)

        api_key = os.getenv("WORKOS_API_KEY")
        client_id = os.getenv("WORKOS_CLIENT_ID")
        if not api_key or not client_id:
            raise ValueError(
                "WorkOS API key and client ID must be set via WORKOS_API_KEY and WORKOS_CLIENT_ID environment variables. "
                "Please check your .env file or export these variables."
            )
        get_workos_client._instance = WorkOSClient(
            api_key=api_key,
            client_id=client_id
        )
    return get_workos_client._instance

# For compatibility with other examples, create workos_client variable
# Initialize it if env vars are available, otherwise it will be created on first use
try:
    if os.getenv("WORKOS_API_KEY") and os.getenv("WORKOS_CLIENT_ID"):
        workos_client = WorkOSClient(
            api_key=os.getenv("WORKOS_API_KEY"),
            client_id=os.getenv("WORKOS_CLIENT_ID")
        )
    else:
        workos_client = None
except ValueError:
    # If env vars aren't set at import time, use lazy initialization
    workos_client = None


# Constants
CUSTOMER_ORGANIZATION_ID = os.getenv("CUSTOMER_ORGANIZATION_ID")
WORKOS_CONNECTION_ID = os.getenv("WORKOS_CONNECTION_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")


def login(request):
    if request.session.get("session_active") is None:
        return render(request, "sso/login.html")

    if request.session.get("session_active"):
        directories = []
        dir_error = None
        try:
            client = workos_client if workos_client else get_workos_client()
            result = client.directory_sync.list_directories(limit=10)
            directories = result.data
        except Exception as e:
            dir_error = str(e)

        return render(
            request,
            "sso/login_successful.html",
            {
                "p_profile": request.session.get("p_profile"),
                "first_name": request.session.get("first_name"),
                "last_name": request.session.get("last_name"),
                "raw_profile": json.dumps(request.session.get("raw_profile"), indent=2),
                "directories": directories,
                "dir_error": dir_error,
            },
        )


def _require_session(request):
    """Returns a redirect response if no active session, else None."""
    if not request.session.get("session_active"):
        return redirect("login")
    return None


def get_directory(request):
    redir = _require_session(request)
    if redir:
        return redir
    directory_id = request.GET.get("id")
    if not directory_id:
        return redirect("login")
    client = workos_client if workos_client else get_workos_client()
    directory = client.directory_sync.get_directory(directory_id)
    json_directory = directory.model_dump_json(indent=2)
    return render(request, "sso/dir_detail.html", {
        "directory_id": directory_id,
        "directory": directory,
        "json_directory": json_directory,
        "first_name": request.session.get("first_name"),
        "last_name": request.session.get("last_name"),
    })


def get_directory_users(request):
    redir = _require_session(request)
    if redir:
        return redir
    directory_id = request.GET.get("id")
    if not directory_id:
        return redirect("login")
    client = workos_client if workos_client else get_workos_client()
    users = client.directory_sync.list_users(directory_id=directory_id, limit=100)
    return render(request, "sso/dir_users.html", {
        "users": users,
        "directory_id": directory_id,
        "first_name": request.session.get("first_name"),
        "last_name": request.session.get("last_name"),
    })


def get_directory_groups(request):
    redir = _require_session(request)
    if redir:
        return redir
    directory_id = request.GET.get("id")
    if not directory_id:
        return redirect("login")
    client = workos_client if workos_client else get_workos_client()
    groups = client.directory_sync.list_groups(directory_id=directory_id, limit=100)
    return render(request, "sso/dir_groups.html", {
        "groups": groups,
        "directory_id": directory_id,
        "first_name": request.session.get("first_name"),
        "last_name": request.session.get("last_name"),
    })


def auth(request):
    # original view: handles either saml (org ID) or provider logins
    if not REDIRECT_URI:
        return render(
            request,
            "sso/login.html",
            {"error": "configuration_error", "error_description": "REDIRECT_URI is not configured"},
        )

    login_type = request.POST.get("login_method")
    if not login_type:
        return render(
            request,
            "sso/login.html",
            {"error": "missing_login_method", "error_description": "Login method is required"},
        )

    params = {"redirect_uri": REDIRECT_URI, "state": {}}

    if login_type == "saml":
        if WORKOS_CONNECTION_ID:
            params["connection_id"] = WORKOS_CONNECTION_ID
        elif CUSTOMER_ORGANIZATION_ID:
            params["organization_id"] = CUSTOMER_ORGANIZATION_ID
        else:
            return render(
                request,
                "sso/login.html",
                {"error": "configuration_error", "error_description": "WORKOS_CONNECTION_ID or CUSTOMER_ORGANIZATION_ID is not configured"},
            )
    else:
        params["provider"] = login_type

    client = workos_client if workos_client else get_workos_client()
    authorization_url = client.sso.get_authorization_url(**params)

    return redirect(authorization_url)


def auth_org(request):
    """Initiate SSO for an explicit organization ID passed in the request."""

    if not REDIRECT_URI:
        return render(
            request,
            "sso/login.html",
            {"error": "configuration_error", "error_description": "REDIRECT_URI is not configured"},
        )

    org_id = request.GET.get("organization_id") or request.POST.get("organization_id")
    if not org_id:
        return render(
            request,
            "sso/login.html",
            {"error": "missing_organization_id", "error_description": "Organization ID is required"},
        )

    params = {"redirect_uri": REDIRECT_URI, "state": {}, "organization_id": org_id}

    client = workos_client if workos_client else get_workos_client()
    authorization_url = client.sso.get_authorization_url(**params)

    return redirect(authorization_url)

def callback(request):
    code = request.GET["code"]
    profile_and_token = workos_client.sso.get_profile_and_token(code)

    profile = profile_and_token.profile

    organization = CUSTOMER_ORGANIZATION_ID

    # Validate that this profile belongs to the organization used for authentication
    if profile.organization_id != organization:
        raise PermissionDenied

    # Use the information in `profile` for further business logic.

    return redirect("/")


def auth_callback(request):
    # Check for error response from WorkOS
    if "error" in request.GET:
        error = request.GET.get("error")
        error_description = request.GET.get("error_description", "An error occurred during authentication")
        # Log the error and redirect back to login with error message
        return render(
            request,
            "sso/login.html",
            {"error": error, "error_description": error_description},
        )

    # Get the authorization code
    code = request.GET.get("code")
    if not code:
        return render(
            request,
            "sso/login.html",
            {"error": "missing_code", "error_description": "No authorization code received"},
        )

    try:
        client = workos_client if workos_client else get_workos_client()
        profile = client.sso.get_profile_and_token(code)
        # In SDK v5+, ProfileAndToken is a Pydantic model - use .dict() to convert to dict
        p_profile = profile.dict()
        request.session["p_profile"] = p_profile
        request.session["first_name"] = p_profile["profile"]["first_name"]
        request.session["last_name"] = p_profile["profile"]["last_name"]
        request.session["raw_profile"] = p_profile["profile"]
        request.session["session_active"] = True
        return redirect("login")
    except Exception as e:
        return render(
            request,
            "sso/login.html",
            {"error": "authentication_error", "error_description": str(e)},
        )


def logout(request):
    request.session.clear()
    return redirect("login")
