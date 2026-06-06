class PermissionService:

    ROLE_PERMISSIONS = {
        "admin": {"*"},
        "operator": {
            "receipts",
            "releases",
            "reports",
        },
        "viewer": {
            "reports",
        },
    }

    def has_access(self, role: str, module: str) -> bool:
        permissions = self.ROLE_PERMISSIONS.get(role, set())

        return "*" in permissions or module in permissions