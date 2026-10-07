"""The packages role merges its Docker config over the one Docker Desktop keeps."""

import pathlib

import yaml

ROLE = pathlib.Path(__file__).resolve().parents[2] / "roles/packages"
CONFIG = yaml.safe_load((ROLE / "tasks/config.yml").read_text(encoding="utf-8"))
DOCKER = next(task for task in CONFIG if task["name"] == "config | docker")


def _task(needle):
    return next(task for task in DOCKER["block"] if needle in task["name"])


def test_both_cask_names_enable_it():
    assert "intersect(['docker', 'docker-desktop'])" in DOCKER["when"][0]


def test_existing_file_is_merged_not_replaced():
    merged = _task("merge docker config")["ansible.builtin.set_fact"]["packages_docker_config_merged"]
    assert "combine(packages_docker_config, recursive=True)" in merged
    assert not (ROLE / "templates/docker.j2").exists()


def test_write_is_skipped_when_content_already_matches():
    write = _task("create docker config")
    assert write["when"] == ["packages_docker_config_merged != packages_docker_config_existing"]


def test_credentials_are_never_logged():
    for needle in ("read docker config", "merge docker config", "create docker config"):
        assert _task(needle)["no_log"] is True, needle


def test_file_is_private():
    assert _task("create docker config")["ansible.builtin.copy"]["mode"] == "0600"
    assert _task("docker config permissions")["ansible.builtin.file"]["mode"] == "0600"
