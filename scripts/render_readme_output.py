"""Regenerate the README terminal block so it can never drift from behaviour."""
import re
import subprocess
import sys
from pathlib import Path

README = Path(__file__).parent.parent / "README.md"
MARKER = re.compile(
    r"(<!-- BEGIN OUTPUT -->\n```\n).*?(\n```\n<!-- END OUTPUT -->)", re.DOTALL
)


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "lane_forecast.cli", "--demo",
         "--lane", "CNSHA-USA", "--min-shipments", "30"],
        capture_output=True, text=True, check=True,
    )
    text = README.read_text()
    README.write_text(MARKER.sub(rf"\1{result.stdout.strip()}\2", text))
    print("README output block updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
