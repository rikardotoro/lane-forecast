import pandas as pd
from typer.testing import CliRunner

from lane_forecast.cli import app

runner = CliRunner()


def _csv(tmp_path):
    rows = [
        {"origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
         "departure": f"2026-01-{day:02d}", "arrival": f"2026-02-{day:02d}"}
        for day in range(1, 29)
    ]
    path = tmp_path / "s.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_cli_runs_and_reports(tmp_path):
    result = runner.invoke(app, [
        "--data", str(_csv(tmp_path)),
        "--lane", "CNSHA-NLRTM",
        "--min-shipments", "10",
    ])
    assert result.exit_code == 0
    assert "CNSHA" in result.stdout


def test_cli_json_output_is_valid(tmp_path):
    import json

    result = runner.invoke(app, [
        "--data", str(_csv(tmp_path)),
        "--lane", "CNSHA-NLRTM",
        "--min-shipments", "10",
        "--json",
    ])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["origin"] == "CNSHA"


def test_unknown_lane_lists_available_lanes(tmp_path):
    result = runner.invoke(app, [
        "--data", str(_csv(tmp_path)),
        "--lane", "XXXXX-YYYYY",
    ])
    assert result.exit_code != 0
    assert "CNSHA-NLRTM" in result.stdout
