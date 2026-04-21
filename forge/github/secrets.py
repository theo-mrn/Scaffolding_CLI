import base64

from forge.config.settings import settings
from forge.github.client import github_client


def set_repo_secrets(repo_name: str, secrets: dict) -> None:
    """Encrypt and upload CI/CD secrets to the GitHub repo."""
    owner = settings.github_org or _get_authenticated_user()

    with github_client() as client:
        public_key_id, public_key = _get_repo_public_key(client, owner, repo_name)

        for secret_name, secret_value in secrets.items():
            encrypted = _encrypt_secret(public_key, secret_value)
            response = client.put(
                f"/repos/{owner}/{repo_name}/actions/secrets/{secret_name}",
                json={"encrypted_value": encrypted, "key_id": public_key_id},
            )
            response.raise_for_status()


def _get_repo_public_key(client, owner: str, repo_name: str) -> tuple[str, str]:
    response = client.get(f"/repos/{owner}/{repo_name}/actions/secrets/public-key")
    response.raise_for_status()
    data = response.json()
    return data["key_id"], data["key"]


def _encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    """Encrypt a secret using the repo's public key (libsodium sealed box)."""
    try:
        from nacl import encoding, public
    except ImportError as exc:
        raise RuntimeError(
            "PyNaCl is required for secret encryption: pip install PyNaCl"
        ) from exc

    public_key_bytes = base64.b64decode(public_key_b64)
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def _get_authenticated_user() -> str:
    with github_client() as client:
        response = client.get("/user")
        response.raise_for_status()
        return response.json()["login"]
