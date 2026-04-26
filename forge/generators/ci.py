from pathlib import Path

from jinja2 import Environment, PackageLoader


def generate_ci(
    project_dir: Path,
    project_type: str,
    project_name: str,
    docker: bool = False,
    sonar: bool = False,
    sonar_project_key: str = "",
    sonar_organization: str = "",
    coverage_threshold: int = 80,
    test_secret_keys: list = None,
    job_lint: bool = True,
    job_test: bool = True,
    job_security: bool = True,
    lint_tool: str = "",
    test_tool: str = "",
    docker_build_in_ci: bool = True,
    cd_job_build: bool = True,
    cd_job_push: bool = True,
    cd_job_trivy: bool = True,
    cd_job_trivyhub: bool = False,
    cd_job_sbom: bool = True,
    cd_job_deploy: bool = False,
    deploy_port: int = 3000,
    ssh_auth: str = "key",
    custom_domain: str = "",
) -> None:
    env = Environment(
        loader=PackageLoader("forge", "config/templates"),
        keep_trailing_newline=True,
    )

    workflows_dir = project_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    ctx = dict(
        project_name=project_name,
        docker=docker and docker_build_in_ci,
        sonar=sonar,
        sonar_project_key=sonar_project_key or project_name,
        sonar_organization=sonar_organization,
        coverage_threshold=coverage_threshold,
        test_secret_keys=test_secret_keys or [],
        job_lint=job_lint,
        job_test=job_test,
        job_security=job_security,
        lint_tool=lint_tool,
        test_tool=test_tool,
    )

    try:
        ci_template = env.get_template(f"ci/{project_type}.yml.j2")
        (workflows_dir / "ci.yml").write_text(ci_template.render(**ctx))
    except Exception:
        return

    if docker and (cd_job_build or cd_job_push):
        cd_ctx = {**ctx, "cd_job_build": cd_job_build, "cd_job_push": cd_job_push, "cd_job_trivy": cd_job_trivy, "cd_job_trivyhub": cd_job_trivyhub, "cd_job_sbom": cd_job_sbom, "cd_job_deploy": cd_job_deploy, "deploy_port": deploy_port, "ssh_auth": ssh_auth, "custom_domain": custom_domain}
        try:
            cd_template = env.get_template(f"cd/{project_type}.yml.j2")
            (workflows_dir / "cd.yml").write_text(cd_template.render(**cd_ctx))
        except Exception:
            pass

    # .prettierignore (for node/react — exclude generated YAML from prettier check)
    if project_type in ("node", "react"):
        try:
            prettierignore_template = env.get_template("prettierignore.j2")
            (project_dir / ".prettierignore").write_text(
                prettierignore_template.render()
            )
        except Exception:
            pass

    # dependabot
    try:
        dependabot_template = env.get_template("dependabot.yml.j2")
        (project_dir / ".github" / "dependabot.yml").write_text(
            dependabot_template.render(project_type=project_type)
        )
    except Exception:
        pass
