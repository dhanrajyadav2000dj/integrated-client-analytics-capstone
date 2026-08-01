from __future__ import annotations
import os, subprocess, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DATASET = "frtgnn/dunnhumby-the-complete-journey"
def main():
    RAW.mkdir(parents=True, exist_ok=True)
    if list(RAW.glob("*.csv")):
        print("Raw CSV files already present; skipping download.")
        return
    token_file = Path.home() / ".kaggle" / "access_token"
    if not os.environ.get("KAGGLE_API_TOKEN") and not token_file.exists():
        raise SystemExit("Kaggle token not found. Configure KAGGLE_API_TOKEN or ~/.kaggle/access_token.")
    subprocess.run(["python", "-m", "kaggle", "datasets", "download", "-d", DATASET, "-p", str(RAW), "--force"], check=True)
    zips = list(RAW.glob("*.zip"))
    if not zips:
        raise SystemExit("No downloaded zip found.")
    with zipfile.ZipFile(zips[0]) as zf:
        zf.extractall(RAW)
    print(f"Downloaded and extracted to {RAW}")
if __name__ == "__main__":
    main()
