"""Authorization policy engine."""

from dataclasses import dataclass
from enum import Enum
from observability.logger import get_logger
from pydantic import BaseModel
from security.jwt.tokens import AuthenticatedUser
from typing import Any
from typing import Optional
from uuid import UUID

logger = get_logger(__name__)


class PolicyEffect(str, Enum):
    """Policy evaluation effects."""
    ALLOW = "allow"
    DENY  = "deny"


class PolicyType(str, Enum):
    """Types of authorization policies."""
    ROLE_BASED      = "rbac"               # Role-Based Access Control
    ATTRIBUTE_BASED = "abac"               # Attribute-Based Access Control
    RESOURCE_BASED  = "rbac_resource"      # Resource-specific RBAC
    CONDITIONAL     = "conditional"        # Conditional policies


@dataclass
class AuthContext:
    """Authorization context for policy evaluation."""
    user                 : AuthenticatedUser
    resource             : str
    action               : str
    tenant_id            : Optional[UUID]           = None
    ip_address           : Optional[str]            = None
    user_agent           : Optional[str]            = None
    request_time         : Optional[str]            = None
    additional_attributes: Optional[dict[str, Any]] = None


class Policy(BaseModel):
    """Authorization policy model."""
    id         : str
    name       : str
    policy_type: PolicyType
    effect     : PolicyEffect
    resources  : list[str]                        # Resource patterns
    actions    : list[str]                        # Action patterns
    roles      : Optional[list[str]]      = None
    permissions: Optional[list[str]]      = None
    conditions : Optional[dict[str, Any]] = None  # Conditional logic
    priority   : int                      = 100   # Higher numbers = higher priority
    enabled    : bool                     = True
    tenant_id  : Optional[UUID]           = None  # Tenant-specific policies


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation."""
    decision          : PolicyEffect
    matched_policies  : list[str]
    evaluation_time_ms: float
    details           : dict[str, Any]


class AuthorizationPolicyEngine:
    """Authorization policy engine."""
    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._role_permissions_cache: dict[str, set[str]] = {}
        self.logger = get_logger(__name__)

    async def evaluate_access(
        self,
        context: AuthContext
    ) -> PolicyEvaluationResult:
        """Evaluate access based on policies and context."""
        import time
        start_time = time.time()

        applicable_policies = await self._get_applicable_policies(context)

        if not applicable_policies:
            return PolicyEvaluationResult(
                decision           = PolicyEffect.DENY,
                matched_policies   = [],
                evaluation_time_ms = (time.time() - start_time) * 1000,
                details            = {"reason": "no_applicable_policies"}
            )

        """Evaluate policies in priority order (highest first)"""
        sorted_policies  = sorted(applicable_policies, key=lambda p: p.priority, reverse=True)
        matched_policies = []
        final_decision   = PolicyEffect.DENY

        for policy in sorted_policies:
            if await self._evaluate_single_policy(policy, context):
                matched_policies.append(policy.id)
                final_decision = policy.effect

                # If we have an explicit DENY, stop evaluation
                if policy.effect == PolicyEffect.DENY:
                    break

                # If we have an ALLOW and it's the highest priority, we can allow
                if policy.effect  == PolicyEffect.ALLOW:
                    final_decision = PolicyEffect.ALLOW

        evaluation_time = (time.time() - start_time) * 1000

        """Log authorization decision"""
        await self._log_authorization_decision(context, final_decision, matched_policies, evaluation_time)

        return PolicyEvaluationResult(
            decision           = final_decision,
            matched_policies   = matched_policies,
            evaluation_time_ms = evaluation_time,
            details            = {
                "evaluated_policies": len(applicable_policies),
                "user_roles"        : context.user.roles,
                "user_permissions"  : context.user.permissions
            }
        )

    async def load_tenant_policies(self, tenant_id: UUID) -> list[Policy]:
        """Load policies specific to a tenant."""
        # TODO: Implement database-backed policy loading
        tenant_policies = [
            policy for policy in self._policies.values()
            if policy.tenant_id == tenant_id or policy.tenant_id is None
        ]
        return tenant_policies

    async def add_policy(self, policy: Policy) -> None:
        """Add or update a policy in the engine."""
        self._policies[policy.id] = policy
        self.logger.info(f"Policy added/updated: {policy.id}", extra = {
            "policy_id"  : policy.id,
            "policy_type": policy.policy_type.value,
            "effect"     : policy.effect.value
        })

    async def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy from the engine."""
        if policy_id in self._policies:
            del self._policies[policy_id]
            self.logger.info(f"Policy removed: {policy_id}")
            return True
        return False

    async def validate_user_permission(
        self,
        user      : AuthenticatedUser,
        permission: str,
        resource  : str = "*"
    ) -> bool:
        """Validate if user has a specific permission."""
        context = AuthContext(
            user      = user,
            resource  = resource,
            action    = "check_permission",
            tenant_id = user.tenant_id
        )

        # Check direct permissions
        if permission in user.permissions or "*" in user.permissions:
            return True

        # Check role-based permissions
        for role in user.roles:
            role_permissions = await self._get_role_permissions(role)
            if permission in role_permissions or "*" in role_permissions:
                return True

        # Check policy-based permissions
        result = await self.evaluate_access(context)
        return result.decision == PolicyEffect.ALLOW

    async def _get_applicable_policies(self, context: AuthContext) -> list[Policy]:
        """Get policies that apply to the given context."""
        applicable = []

        for policy in self._policies.values():
            if not policy.enabled:
                continue

            # Check tenant scope
            if policy.tenant_id and policy.tenant_id != context.tenant_id:
                continue

            # Check resource patterns
            if not self._matches_patterns(context.resource, policy.resources):
                continue

            # Check action patterns
            if not self._matches_patterns(context.action, policy.actions):
                continue

            applicable.append(policy)

        return applicable

    async def _evaluate_single_policy(self, policy: Policy, context: AuthContext) -> bool:
        """Evaluate a single policy against the context."""
        if policy.policy_type == PolicyType.ROLE_BASED:
            return await self._evaluate_rbac_policy(policy, context)

        elif policy.policy_type == PolicyType.ATTRIBUTE_BASED:
            return await self._evaluate_abac_policy(policy, context)

        elif policy.policy_type == PolicyType.CONDITIONAL:
            return await self._evaluate_conditional_policy(policy, context)

        else:
            return False

    async def _evaluate_rbac_policy(self, policy: Policy, context: AuthContext) -> bool:
        """Evaluate Role-Based Access Control policy."""
        if not policy.roles:
            return False

        # Check if user has any of the required roles
        user_roles     = set(context.user.roles)
        required_roles = set(policy.roles)

        return bool(user_roles.intersection(required_roles))

    async def _evaluate_abac_policy(self, policy: Policy, context: AuthContext) -> bool:
        """Evaluate Attribute-Based Access Control policy."""
        if not policy.permissions:
            return False

        # Check if user has any of the required permissions
        user_permissions     = set(context.user.permissions)
        required_permissions = set(policy.permissions)

        return bool(user_permissions.intersection(required_permissions))

    async def _evaluate_conditional_policy(self, policy: Policy, context: AuthContext) -> bool:
        """Evaluate conditional policy with dynamic conditions."""
        if not policy.conditions:
            return True

        # TODO: Condition evaluation
        # This would support expressions like:
        # - time-based access (business hours only)
        # - IP-based restrictions
        # - resource attribute checks
        # - user attribute checks

        return True

    def _matches_patterns(self, value: str, patterns: list[str]) -> bool:
        """Check if a value matches any of the given patterns."""
        for pattern in patterns:
            if pattern == "*" or pattern == value:
                return True
            # TODO: Add support for glob patterns and regex
        return False

    async def _get_role_permissions(self, role: str) -> set[str]:
        """Get permissions associated with a role (cached)."""
        if role not in self._role_permissions_cache:
            # TODO: Load from database
            # For now, return empty set
            self._role_permissions_cache[role] = set()

        return self._role_permissions_cache[role]

    async def _log_authorization_decision(
        self,
        context         : AuthContext,
        decision        : PolicyEffect,
        matched_policies: list[str],
        evaluation_time : float
    ) -> None:
        """Log authorization decisions for audit purposes."""
        self.logger.info(
            f"Authorization decision: {decision.value}",
            extra={
                "user_id"           : str(context.user.user_id),
                "tenant_id"         : str(context.tenant_id) if context.tenant_id else None,
                "resource"          : context.resource,
                "action"            : context.action,
                "decision"          : decision.value,
                "matched_policies"  : matched_policies,
                "evaluation_time_ms": evaluation_time,
                "user_roles"        : context.user.roles,
                "ip_address"        : context.ip_address
            }
        )


# Default policies for common scenarios
DEFAULT_POLICIES = [
    Policy(
        id          = "admin_full_access",
        name        = "Administrator Full Access",
        policy_type = PolicyType.ROLE_BASED,
        effect      = PolicyEffect.ALLOW,
        resources   = ["*"],
        actions     = ["*"],
        roles       = ["admin", "super_admin"],
        priority    = 1000
    ),
    Policy(
        id          = "user_read_own_data",
        name        = "Users Can Read Own Data",
        policy_type = PolicyType.ATTRIBUTE_BASED,
        effect      = PolicyEffect.ALLOW,
        resources   = ["user_profile", "user_data"],
        actions     = ["read", "view"],
        permissions = ["user:read_own"],
        priority    = 500
    )
]

_policy_engine: Optional[AuthorizationPolicyEngine] = None


async def get_authorization_policy_engine() -> AuthorizationPolicyEngine:
    """Get authorization policy engine singleton instance."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = AuthorizationPolicyEngine()

        for policy in DEFAULT_POLICIES:
            await _policy_engine.add_policy(policy)

    return _policy_engine
