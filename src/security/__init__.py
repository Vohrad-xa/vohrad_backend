"""Security infrastructure.

This module contains security-related components organized in submodules:

- security.jwt: JWT authentication components (tokens, engine, service, revocation)
- security.password: Password hashing and verification utilities
- security.authorization: Authorization service for permission and role checks
- security.policy: RBAC policy helpers and permission registry

Import from specific submodules:
    from security.jwt import AuthenticatedUser, get_auth_jwt_service
    from security.password import hash_password, verify_password
    from security.authorization import AuthorizationService
    from security.policy import apply_conditional_access
"""
