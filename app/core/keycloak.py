from config import settings

from keycloak import KeycloakAdmin, KeycloakOpenID
from fastapi import HTTPException
server_url = settings.KEYCLOAK_SERVER_URL
realm = settings.KEYCLOAK_REALM
client_id = settings.KEYCLOAK_CLIENT_ID
client_secret = settings.KEYCLOAK_CLIENT_SECRET

admin_user = settings.KEYCLOAK_ADMIN_USER
admin_password = settings.KEYCLOAK_ADMIN_PASSWORD


from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
)
# 🔹 Admin client (for creating users, assigning groups, etc.)
keycloak_admin = KeycloakAdmin(
    server_url=f"{server_url}/",
    username=admin_user,
    password=admin_password,
    realm_name=realm,
    user_realm_name="master",
    verify=True,
)

# 🔹 OpenID Connect client (login / tokens)
keycloak_openid = KeycloakOpenID(
    server_url=server_url,
    client_id=client_id,
    realm_name=realm,
    client_secret_key=client_secret,
)



def get_userinfo_from_keycloak(token: str):
    try:
        userinfo = keycloak_openid.userinfo(token)
        return userinfo
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")    