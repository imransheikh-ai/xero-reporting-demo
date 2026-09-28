"""
Step 5: AI writes first-draft management commentary from the P&L variance data.

- Reads variance.json (created by pull_pnl.py)
- Sends it to the AI with strict finance rules
- Checks every number the AI wrote against the real Xero data
- Saves the result to commentary.md

Switch AI provider with the PROVIDER setting below:
  "openai"  -> needs OPENAI_API_KEY in .env   (pip install openai)
  "claude"  -> needs ANTHROPIC_API_KEY in .env (pip install anthropic)
"""

import json
import re

from dotenv import load_dotenv

load_dotenv()

# ---- Settings ----
PROVIDER = "openai"               # change to "claude" before recording the demo video
OPENAI_MODEL = "gpt-4.1"          # change if your OpenAI account uses a different model
CLAUDE_MODEL = "claude-sonnet-5"
MAX_TOKENS = 1500


SYSTEM_PROMPT = """You are a senior management accountant at a UK outsourced finance firm.
You write the first draft of monthly management commentary on a client's Profit and Loss.
A qualified accountant will review your draft before it goes to the client.

Rules:
- Use only the numbers in the data. Do not calculate any new totals or percentages.
- Write money rounded to the nearest whole number, for example 2,599. Do not use a currency symbol.
- Lines with "flag": true are the main movements. Cover them first.
- For expenses, a decrease improves profit. Say this clearly.
- If the previous month was a loss, describe the change as a move from loss to profit. Do not quote a percentage for it.
- You do not know the real reasons for any movement. Give possible reasons only as questions for the client, never as facts.
- Plain British English, short sentences, no jargon.

Format in Markdown:
## Summary
3 to 4 sentences on the month overall. State Total Income, Gross Profit and Net Profit
for both months, and the change in Total Operating Expenses.
## Key movements
One short paragraph for each flagged line. Give this month, last month and the change,
for example "Advertising was 2,309 against 7,347 last month, a fall of 5,038 (69%)."
Use the change_pct from the data when it is not null.
## Items to investigate
Bullet list. Say what should be checked (for example invoices, coding, timing, accruals),
not just the line name. Do not repeat the questions for the client.
## Questions for the client
Bullet list, maximum 5.
"""


def ask_openai(system_prompt, user_message):
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content, OPENAI_MODEL


def ask_claude(system_prompt, user_message):
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text, CLAUDE_MODEL


def check_numbers(commentary, lines):
    """Return numbers the AI wrote that do not match the Xero data (within 1 for rounding)."""
    allowed = []
    for line in lines:
        for key in ("current", "previous", "change", "change_pct"):
            if line[key] is not None:
                allowed.append(abs(line[key]))

    unverified = []
    for text in re.findall(r"\d[\d,]*(?:\.\d+)?", commentary):
        value = float(text.replace(",", ""))
        if value < 100:
            continue  # skip small numbers like counts
        if "," not in text and "." not in text and 1900 <= value <= 2100:
            continue  # skip years
        if not any(abs(value - a) <= 1.0 for a in allowed):
            unverified.append(text)
    return unverified


def main():
    with open("variance.json") as f:
        data = json.load(f)

    user_message = (
        f"Company: {data['company']}\n"
        f"Current period: {data['current_period']}\n"
        f"Previous period: {data['previous_period']}\n\n"
        f"P&L data (JSON):\n{json.dumps(data['lines'], indent=2)}"
    )

    # 1. Ask the AI for the draft commentary
    if PROVIDER == "claude":
        commentary, model_used = ask_claude(SYSTEM_PROMPT, user_message)
    elif PROVIDER == "openai":
        commentary, model_used = ask_openai(SYSTEM_PROMPT, user_message)
    else:
        raise SystemExit('PROVIDER must be "openai" or "claude"')

    # 2. Check every number against the real data
    unverified = check_numbers(commentary, data["lines"])
    if unverified:
        check_note = "Numbers NOT found in the Xero data (review these): " + ", ".join(unverified)
    else:
        check_note = "All numbers in this commentary match the Xero data."

    # 3. Save and show the result
    output = (
        f"# Management Commentary - {data['company']}\n"
        f"**{data['current_period']} vs {data['previous_period']}**\n\n"
        f"*Draft generated by AI ({model_used}) for accountant review.*\n\n"
        f"{commentary}\n\n"
        f"---\n**Number check:** {check_note}\n"
    )

    with open("commentary.md", "w", encoding="utf-8") as f:
        f.write(output)

    print(output)
    print("Saved commentary.md")


if __name__ == "__main__":
    main()
