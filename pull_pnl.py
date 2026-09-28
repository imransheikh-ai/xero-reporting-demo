import csv
import json

from xero_client import get_report

# ---- Settings ----
MONTH_START = "2026-09-01"   # current month
MONTH_END = "2026-09-30"
MIN_CHANGE = 500             # flag if the change is at least this amount...
MIN_PCT = 20                 # ...and at least this % (or the line is new)


def to_number(value):
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return 0.0


# 1. Get P&L for this month, compared with 1 previous month
report, company = get_report("ProfitAndLoss", {
    "fromDate": MONTH_START,
    "toDate": MONTH_END,
    "periods": 1,
    "timeframe": "MONTH",
})

header = next(r for r in report["Rows"] if r["RowType"] == "Header")
current_label = header["Cells"][1]["Value"]
previous_label = header["Cells"][2]["Value"]

# 2. Turn Xero's nested report into a simple list of lines
lines = []
for section in report["Rows"]:
    if section["RowType"] != "Section":
        continue
    title = section.get("Title") or "Summary"
    for row in section.get("Rows", []):
        cells = row["Cells"]
        lines.append({
            "section": title,
            "account": cells[0]["Value"],
            "is_total": row["RowType"] == "SummaryRow" or title == "Summary",
            "current": to_number(cells[1]["Value"]),
            "previous": to_number(cells[2]["Value"]),
        })

# 3. Calculate variances in code (not by AI)
for line in lines:
    change = line["current"] - line["previous"]
    pct = round(change / abs(line["previous"]) * 100, 1) if line["previous"] else None
    line["change"] = round(change, 2)
    line["change_pct"] = pct
    line["flag"] = (
        not line["is_total"]
        and abs(change) >= MIN_CHANGE
        and (pct is None or abs(pct) >= MIN_PCT)
    )

# 4. Print a simple table
print(f"\n{company} - Profit and Loss: {current_label} vs {previous_label}\n")
print(f"{'Account':35} {current_label:>12} {previous_label:>12} {'Change':>12} {'%':>8}")
print("-" * 83)
for line in lines:
    pct_text = f"{line['change_pct']}%" if line["change_pct"] is not None else "new"
    mark = "  <-- check" if line["flag"] else ""
    print(f"{line['account'][:35]:35} {line['current']:>12,.2f} {line['previous']:>12,.2f} "
          f"{line['change']:>12,.2f} {pct_text:>8}{mark}")

# 5. Save results for the Claude step
with open("variance.json", "w") as f:
    json.dump({
        "company": company,
        "current_period": current_label,
        "previous_period": previous_label,
        "lines": lines,
    }, f, indent=2)

with open("variance.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=lines[0].keys())
    writer.writeheader()
    writer.writerows(lines)

print("\nSaved variance.json and variance.csv")