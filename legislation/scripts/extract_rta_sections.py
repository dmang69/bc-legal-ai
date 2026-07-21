"""Extract key RTA sections from official BC Laws HTML download."""
from __future__ import annotations

import re
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "raw" / "rta-02078.html"
OUT = Path(__file__).resolve().parents[1] / "extracts"


def html_to_plain(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.I | re.S)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.I | re.S)
    plain = re.sub(r"<[^>]+>", "\n", text)
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    plain = re.sub(r"[ \t]+\n", "\n", plain)
    return plain


def main() -> None:
    html = RAW.read_text(encoding="utf-8", errors="replace")
    plain = html_to_plain(html)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rta-full-plain.txt").write_text(plain, encoding="utf-8")

    # Capture currency line
    currency = ""
    m = re.search(r"This Act is current to ([^\n]+)", plain)
    if m:
        currency = m.group(1).strip()

    needles = [
        "This Act cannot be avoided",
        "Protection of tenant's right to quiet enjoyment",
        "Landlord's right to enter rental unit restricted",
        "Landlord and tenant obligations to repair and maintain",
        "Return of security deposit and pet damage deposit",
        "Timing and notice of rent increases",
        "Amount of rent increase",
        "Landlord's notice: non-payment of rent",
        "Landlord's notice: cause",
        "Landlord's notice: landlord's use of property",
        "Application and processing fees prohibited",
        "Limits on amount of deposits",
        "Landlord prohibitions respecting deposits",
        "Service of documents",
        "When documents are considered received",
        "Application for review of a decision or order",
    ]

    report = []
    report.append("OFFICIAL SOURCE: BC Laws — Government of British Columbia")
    report.append("URL: https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01")
    report.append(f"Currency line from BC Laws: This Act is current to {currency}")
    report.append(f"HTML bytes: {len(html)}")
    report.append("")

    for needle in needles:
        i = plain.find(needle)
        if i < 0:
            # case-insensitive
            i = plain.lower().find(needle.lower())
        report.append(f"=== SEARCH: {needle} (index={i}) ===")
        if i >= 0:
            chunk = plain[max(0, i - 120) : i + 1200]
            report.append(chunk.strip())
        else:
            report.append("[NOT FOUND in plain extract]")
        report.append("")

    (OUT / "rta-key-provisions-search.txt").write_text("\n".join(report), encoding="utf-8")
    print("Wrote", OUT / "rta-key-provisions-search.txt")
    print("Currency:", currency)


if __name__ == "__main__":
    main()
