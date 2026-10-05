# CLAUDE.md

Personal-finance workspace built on the Moneytor read-only API. Claude pulls the
user's data, analyzes it, and forecasts the checking-account position.

## Privacy rules (this repo is PUBLIC)

- Never commit financial data: balances, amounts, transactions, account or card
  numbers, names of people or payees. Only code and methodology go in git.
- Fetched data lives in `moneytor/data/`, which is git-ignored. Keep it there.
- Don't put figures in commit messages, PR text, or code comments either.
- Deliver results in chat, as downloads (SendUserFile), or to the user's Google
  Drive — not in the repo.
- Never ask the user to paste tokens into chat.

## Data access

- API docs: https://app.moneytor.co.il/llms.txt (also `/docs.md`, `/openapi.json`).
- Auth: the environment's API credentials inject `Authorization` for
  `app.moneytor.co.il` through the egress proxy, so no token env var is needed.
  `MONEYTOR_API_TOKEN` is used instead when set.
- Rate limit: 30 requests/hour, 300/day. A full fetch uses ~5. Don't refetch
  needlessly; reuse `moneytor/data/` within a session.
- Fetch: `python3 moneytor/fetch.py` → `moneytor/data/{asset_worth.json,
  assets.json, assets.csv, transactions.csv, insurance.json}`.

## Data model notes

- `assets.json`: `form: "bank"` = Leumi checking accounts (`accountType` balance)
  and deposits (`saving`). `form: "debt"` includes each credit card; its balance
  is the next pending card charge.
- `transactions.csv` has `type` CHECKING or CARD.
  - Match checking rows to assets by the trailing digits of `accountNumber` (the
    IBAN ends with the asset's account number).
  - For CARD rows, `valueDate` is the date the charge hits the bank. Summing
    card rows by `valueDate` matches the checking-account card debits exactly.
    Use that to find pending charges.
  - Card rows carry the card's last 4 digits in `accountNumber`. Map them to
    issuers via the debt asset names and the checking-debit descriptions.
- Future-dated CHECKING rows are scheduled debits. Assume the reported balance
  does not include them yet, and say so when it matters.
- Some cards charge immediately; those appear in checking ~1 day later.

## The user's monthly cycle

- The financial month ends on the **12th**.
- Salary arrives around the **8th** into the main checking account.
- Credit cards charge around the **10th–11th**.

## End-of-cycle forecast method

Projected checking total on the 12th =
current checking balances
\+ expected salary (ask the user, or use their stated assumption)
− card charges with `valueDate` between today and the 12th (include immediate
  charges not yet in checking)
− scheduled future-dated checking debits up to the 12th (not after)
− recurring debits expected before the 12th, estimated from last month.

Also report:
- Per-account projections, and the total with and without the savings deposit.
- Cycle P&L: projected value on the 12th minus the value on the previous 12th.
  Back-calculate that value as current balance minus checking transactions
  since then.
- What was excluded: charges after the 12th, irregular transfers, and income
  that hasn't arrived yet.

## Working style

- The user writes in English; transaction descriptions are in Hebrew.
- Amounts are in NIS. Show signs explicitly (+/−) and round sensibly.
- State assumptions plainly and flag anything uncertain.
