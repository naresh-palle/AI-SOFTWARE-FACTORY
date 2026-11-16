"""
Docker sandbox for generated projects.

Generated code runs only inside a container. The container sees the project
backend directory, a dropped capability set, a memory limit, and no host
environment variables.
"""

import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from typing import List, Sequence

from factory.generator.workspace import WorkspaceManager


DENIED_COMMAND_MARKERS = (
    "terraform apply",
    "kubectl apply",
    "kubectl delete",
    "helm upgrade",
    "helm install",
    "docker compose up",
    "git push --force",
    "git push -f",
)


@dataclass
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str
    status: str

    @property
    def output(self) -> str:
        return f"{self.stdout}\n{self.stderr}".strip()


class DockerExecutionSandbox:
    """Run backend installation and pytest inside python:3.10-slim."""

    image = "python:3.10-slim"

    def run_backend_tests(self, workspace: WorkspaceManager) -> SandboxResult:
        backend = workspace.workspace_path / "backend"
        tests = backend / "tests"
        if not tests.is_dir():
            return SandboxResult(0, "No tests found in backend/tests.", "", "not_run")
        if not self.docker_available():
            return SandboxResult(
                127,
                "",
                "Docker is not available. Generated tests were not executed on the host.",
                "unavailable",
            )

        deps = backend / ".sandbox-deps"
        if not (deps / "fastapi").is_dir() or not (deps / "pytest").is_dir():
            install = self._docker(
                workspace,
                backend,
                [
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-cache-dir",
                    "--target",
                    "/work/.sandbox-deps",
                    "-r",
                    "requirements.txt",
                ],
                network="bridge",
                read_only=False,
                timeout_seconds=180,
            )
            if install.status != "completed" or install.returncode != 0:
                install.status = "failed" if install.status == "completed" else install.status
                return install

        test = self._docker(
            workspace,
            backend,
            [
                "python",
                "-m",
                "pytest",
                "tests",
                "-q",
                "-p",
                "no:cacheprovider",
                "--basetemp=/tmp/pytest",
            ],
            network="none",
            read_only=True,
            timeout_seconds=90,
            extra_env=["PYTHONPATH=/work/.sandbox-deps:/work", "PYTHONDONTWRITEBYTECODE=1", "HOME=/tmp"],
        )
        if test.status == "completed":
            test.status = "passed" if test.returncode == 0 else "failed"
        return test

    def run_rejected_command(self, command: Sequence[str]) -> SandboxResult:
        rendered = " ".join(command)
        if any(marker in rendered for marker in DENIED_COMMAND_MARKERS):
            return SandboxResult(126, "", f"Rejected irreversible command: {rendered}", "rejected")
        return SandboxResult(1, "", "No sandbox command was executed.", "rejected")

    def docker_available(self) -> bool:
        return shutil.which("docker") is not None

    def _docker(
        self,
        workspace: WorkspaceManager,
        mount: os.PathLike,
        command: List[str],
        network: str,
        read_only: bool,
        timeout_seconds: int,
        extra_env: Sequence[str] = (),
    ) -> SandboxResult:
        rendered = " ".join(command)
        if any(marker in rendered for marker in DENIED_COMMAND_MARKERS):
            return SandboxResult(126, "", f"Rejected irreversible command: {rendered}", "rejected")

        name = f"factory-sbx-{workspace.project_id[:8]}-{uuid.uuid4().hex[:8]}"
        stat = workspace.workspace_path.stat()
        mount_spec = f"{os.fspath(mount)}:/work"
        if read_only:
            mount_spec += ":ro"
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "--name",
            name,
            "--network",
            network,
            "--memory",
            "768m",
            "--cpus",
            "1",
            "--pids-limit",
            "256",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--user",
            f"{stat.st_uid}:{stat.st_gid}",
            "--tmpfs",
            "/tmp:rw,nosuid,size=64m",
            "-v",
            mount_spec,
            "-w",
            "/work",
            "-e",
            "HOME=/tmp",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
        ]
        for item in extra_env:
            docker_cmd.extend(["-e", item])
        if read_only:
            docker_cmd.extend(["--read-only"])
        docker_cmd.append(self.image)
        docker_cmd.extend(command)

        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                env=_docker_cli_env(),
            )
        except subprocess.TimeoutExpired as exc:
            subprocess.run(["docker", "kill", name], capture_output=True, text=True, timeout=20, env=_docker_cli_env())
            stdout = exc.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            return SandboxResult(124, _clip(stdout), f"Sandbox timed out after {timeout_seconds}s", "timed_out")
        except OSError as exc:
            return SandboxResult(127, "", f"Docker could not be started: {exc.__class__.__name__}", "unavailable")

        status = "completed"
        stderr = proc.stderr or ""
        if proc.returncode != 0 and "Unable to find image" in stderr:
            status = "unavailable"
        return SandboxResult(proc.returncode, _clip(proc.stdout or ""), _clip(stderr), status)


def _docker_cli_env() -> dict:
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "HOME"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    return env


def _clip(value: str, limit: int = 8000) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]
