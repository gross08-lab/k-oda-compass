from __future__ import annotations

import argparse
from pathlib import Path

import qrcode


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a QR code PNG for a URL.")
    parser.add_argument("url")
    parser.add_argument("--out", default="koda_qr.png")
    args = parser.parse_args()

    image = qrcode.make(args.url)
    out = Path(args.out)
    image.save(out)
    print(out.resolve())


if __name__ == "__main__":
    main()
