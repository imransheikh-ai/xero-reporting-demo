# Xero AI Reporting Demo

A working prototype that pulls a Profit and Loss report from **Xero**, calculates month-on-month variances in code, and uses an **AI model (Claude or OpenAI)** to write first-draft management commentary for accountant review. The output is an Excel report ready for a finance team.

Built by **Imran Sheikh** – [LinkedIn](https://www.linkedin.com/in/imranazhar/)

---

## What it does

```
Xero (read-only API)
      │
      ▼
pull_pnl.py ──► P&L this month vs last month
      │         variances calculated in Python (not by AI)
      │         large movements flagged for review
      ▼
write_commentary.py ──► AI writes draft commentary using strict finance rules
      │                 every number the AI writes is checked against Xero data
      ▼
build_report.py ──► Excel report
                    Sheet 1: P&L variance table (live formulas, flagged lines highlighted)
                    Sheet 2: draft commentary for accountant review
```

## Key design choices

- **Numbers come from code, not AI.** All totals, changes and percentages are calculated in Python and Excel formulas. The AI only explains them.
- **Automatic number check.** After the AI writes the commentary, the script checks every figure against the Xero data and reports any number that does not match.
- **Read-only, minimum access.** The Xero app requests only two read-only scopes: Profit and Loss and Balance Sheet. Nothing in Xero can be changed.
- **Human in the loop.** The commentary is labelled as a draft. Possible reasons for movements are written as questions for the client, never as facts.
- **Traceable Excel output.** Change and Change % are live Excel formulas, so an accountant can click any cell and see how it was calculated.
- **Secrets stay local.** Keys and tokens live in `.env` and `tokens.json`, both excluded from Git.

## Files

| File | Purpose |
| --- | --- |
| `connect_xero.py` | One-time Xero login (OAuth 2.0). Saves tokens locally. |
| `xero_client.py` | Refreshes the Xero token and fetches reports. |
| `pull_pnl.py` | Pulls the P&L, calculates variances, flags large movements. |
| `write_commentary.py` | Sends variances to the AI, checks the numbers, saves `commentary.md`. |
| `build_report.py` | Builds the Excel management report. |
| `sample_output/` | Example outputs from the Xero demo company (fictional data). |

## How to run

1. Create a free app at [developer.xero.com](https://developer.xero.com) (Web app, redirect URI `http://localhost:8080/callback`).
2. Copy `.env.example` to `.env` and add your keys.
3. Install and run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python connect_xero.py      # one time: log in and choose your Xero organisation
python pull_pnl.py          # P&L and variances
python write_commentary.py  # AI draft commentary
python build_report.py      # Excel report
```

Settings such as the month, the review threshold and the AI provider (`"claude"` or `"openai"`) are at the top of each script.

## Next steps for a production version

- Year-to-date and budget vs actual analysis
- Balance sheet and cash flow commentary
- Output into the firm's own PowerPoint board-pack template
- Multi-client runs with role-based access and an audit log
- Hosted version with a simple review screen for the finance team
