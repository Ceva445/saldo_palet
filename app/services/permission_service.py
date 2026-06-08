class PermissionService:
    """Maps roles to the UI/API modules they may write to.

    Modules mirror the dashboard components:
    masterdata, receipts, releases, corrections, reports.
    """

    ROLE_PERMISSIONS = {
        "admin": {"*"},
        "operator": {
            "receipts",
            "releases",
            "corrections",
            "reports",
        },
        "viewer": {
            "reports",
        },
    }

    # All modules a user may interact with, used by the frontend to gate the UI.
    ALL_MODULES = (
        "masterdata",
        "receipts",
        "releases",
        "corrections",
        "reports",
        "users",
    )

    def has_access(self, role: str, module: str) -> bool:
        permissions = self.ROLE_PERMISSIONS.get(role, set())

        return "*" in permissions or module in permissions

    def allowed_modules(self, role: str) -> list[str]:
        return [m for m in self.ALL_MODULES if self.has_access(role, m)]
