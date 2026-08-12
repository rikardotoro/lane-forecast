"""Download the full CC0 source dataset. Not required to run the tool."""
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

URL = "https://www.kaggle.com/api/v1/datasets/download/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis"
TARGET = Path(__file__).parent.parent / "data" / "raw"


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    archive = TARGET / "dataco.zip"
    print(f"Downloading to {archive} ...")
    urlretrieve(URL, archive)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(TARGET)
    print(f"Extracted to {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
