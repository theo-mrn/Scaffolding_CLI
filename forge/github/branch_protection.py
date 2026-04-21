from forge.config.settings import settings
from forge.github.client import github_client
from forge.github.errors import GitHubError


def set_branch_protection(repo_name: str) -> None:
    owner = settings.github_org or _get_authenticated_user()
    branch = settings.default_branch

    with github_client() as client:
        response = client.put(
            f"/repos/{owner}/{repo_name}/branches/{branch}/protection",
            json={
                "required_status_checks": {"strict": True, "contexts": []},
                "enforce_admins": True,
                "required_pull_request_reviews": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews": True,
                },
                "restrictions": None,
                "required_linear_history": True,
                "allow_force_pushes": False,
                "allow_deletions": False,
            },
        )
        if response.is_error:
            raise GitHubError(f"GitHub {response.status_code} en appliquant les branch protection rules.")


def _get_authenticated_user() -> str:
    with github_client() as client:
        response = client.get("/user")
        if response.is_error:
            raise GitHubError(f"GitHub {response.status_code} — impossible de récupérer l'utilisateur.")
        return response.json()["login"]
