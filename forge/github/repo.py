import httpx

from forge.config.settings import settings
from forge.github.client import github_client
from forge.github.errors import GitHubError

_ERROR_HINTS = {
    401: "Token invalide ou expiré.",
    403: "Token insuffisant — vérifie que le scope 'repo' est activé sur ton token GitHub.",
    422: "Le repo existe peut-être déjà sur GitHub.",
}


def create_github_repo(name: str, private: bool = True) -> str:
    with github_client() as client:
        endpoint = f"/orgs/{settings.github_org}/repos" if settings.github_org else "/user/repos"
        response = client.post(
            endpoint,
            json={"name": name, "private": private, "auto_init": False, "description": "Scaffolded by forge"},
        )
        _raise_for_status(response, "créer le repo")
        return response.json()["clone_url"]


def _raise_for_status(response: httpx.Response, action: str) -> None:
    if response.is_error:
        hint = _ERROR_HINTS.get(response.status_code, "")
        msg = f"GitHub {response.status_code} en essayant de {action}."
        if hint:
            msg += f" {hint}"
        raise GitHubError(msg)
