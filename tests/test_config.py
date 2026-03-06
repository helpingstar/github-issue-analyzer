from pathlib import Path

from github_issue_analyzer.config import load_file_config


def test_load_file_config_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "repos.toml"
    config_path.write_text(
        """
[defaults]
trigger_label = "ai:analyze"
clarification_reminder_days = 7
polling_interval_seconds = 30

[[repos]]
owner_repo = "helpingstar/example"
""".strip(),
        encoding="utf-8",
    )

    config = load_file_config(config_path)

    assert config.defaults.trigger_label == "ai:analyze"
    assert config.repos[0].owner_repo == "helpingstar/example"
