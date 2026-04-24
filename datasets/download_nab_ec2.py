from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve


BASE_URL = "https://raw.githubusercontent.com/numenta/NAB/master/data/realAWSCloudwatch"
FILES = [
    "ec2_cpu_utilization_24ae8d.csv",
    "ec2_cpu_utilization_53ea38.csv",
    "ec2_cpu_utilization_5f5533.csv",
    "ec2_cpu_utilization_ac20cd.csv",
]


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "nab_realAWSCloudwatch"
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in FILES:
        dst = out_dir / name
        url = f"{BASE_URL}/{name}"
        urlretrieve(url, dst)
        print(f"Downloaded: {dst}")


if __name__ == "__main__":
    main()
