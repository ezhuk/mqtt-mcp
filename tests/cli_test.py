from typer.testing import CliRunner

from mqtt_mcp.cli import app


def test_cli(cli):
    runner = CliRunner()
    result = runner.invoke(app)
    assert result.exit_code == 0
