import pytest
import respx
import httpx

GITHUB_API = "https://api.github.com"


@respx.mock
def test_create_github_repo_user(monkeypatch) -> None:
    import forge.config.settings as cfg
    monkeypatch.setattr(cfg.settings, "github_token", "test-token")
    monkeypatch.setattr(cfg.settings, "github_org", "")

    from forge.github.repo import create_github_repo

    respx.post(f"{GITHUB_API}/user/repos").mock(
        return_value=httpx.Response(
            201, json={"clone_url": "https://github.com/user/my-project.git"}
        )
    )

    url = create_github_repo("my-project", private=True)
    assert url == "https://github.com/user/my-project.git"


@respx.mock
def test_create_github_repo_org(monkeypatch) -> None:
    import forge.config.settings as cfg
    monkeypatch.setattr(cfg.settings, "github_token", "test-token")
    monkeypatch.setattr(cfg.settings, "github_org", "my-org")

    from forge.github.repo import create_github_repo

    respx.post(f"{GITHUB_API}/orgs/my-org/repos").mock(
        return_value=httpx.Response(
            201, json={"clone_url": "https://github.com/my-org/my-project.git"}
        )
    )

    url = create_github_repo("my-project", private=True)
    assert url == "https://github.com/my-org/my-project.git"


@respx.mock
def test_set_branch_protection(monkeypatch) -> None:
    import forge.config.settings as cfg
    monkeypatch.setattr(cfg.settings, "github_token", "test-token")
    monkeypatch.setattr(cfg.settings, "github_org", "my-org")
    monkeypatch.setattr(cfg.settings, "default_branch", "main")

    from forge.github.branch_protection import set_branch_protection

    respx.put(f"{GITHUB_API}/repos/my-org/my-project/branches/main/protection").mock(
        return_value=httpx.Response(200, json={})
    )

    set_branch_protection("my-project")


@respx.mock
def test_set_repo_secrets(monkeypatch) -> None:
    pytest.importorskip("nacl")

    import forge.config.settings as cfg
    monkeypatch.setattr(cfg.settings, "github_token", "test-token")
    monkeypatch.setattr(cfg.settings, "github_org", "my-org")

    from forge.github.secrets import set_repo_secrets

    respx.get(f"{GITHUB_API}/repos/my-org/my-project/actions/secrets/public-key").mock(
        return_value=httpx.Response(
            200,
            json={
                "key_id": "123",
                "key": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            },
        )
    )
    respx.put(f"{GITHUB_API}/repos/my-org/my-project/actions/secrets/MY_SECRET").mock(
        return_value=httpx.Response(201, json={})
    )

    set_repo_secrets("my-project", {"MY_SECRET": "super-secret"})
