from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from core.keycloak import keycloak_openid, oauth2_scheme, extract_token
from typing import List, Callable

def roles_within(allowed_roles: List[str]) -> Callable:
    """Create a dependency that checks if user has any of the specified roles"""
    async def check_roles(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
        try:
            # Extract token string
            token = extract_token(credentials)
            
            # Decode token to get roles
            token_info = keycloak_openid.introspect(token)
            
            # Get realm roles
            realm_roles = token_info.get('realm_access', {}).get('roles', [])
            
            # Check if user has any of the allowed roles
            user_has_role = any(role in realm_roles for role in allowed_roles)
            
            if not user_has_role:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            return token
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=401, 
                detail=f"Could not validate token: {str(e)}"
            )
    
    return check_roles

# Convenience function for superadmin only
require_superadmin = roles_within(['superadmin'])