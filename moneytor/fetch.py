"""Pull data from the Moneytor read-only API into local CSV/JSON files.

Usage: MONEYTOR_API_TOKEN=... python moneytor/fetch.py [--out moneytor/data] [--from YYYY-MM-DD] [--to YYYY-MM-DD]

Each run uses 4+ requests (one per endpoint, plus one per 2000 transactions);
the API allows 30 per hour and 300 per day.
"""
import argparse
import csv
import json
import os
import sys
import urllib.parse
import urllib.request

BASE = "https://app.moneytor.co.il/api/v1"


def get(path, token, params=None):
    url = f"{BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")


def write_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_csv(rows, path):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    # utf-8-sig so Excel shows Hebrew correctly
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                        for k, v in row.items()})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    p.add_argument("--from", dest="date_from")
    p.add_argument("--to", dest="date_to")
    args = p.parse_args()

    token = os.environ.get("MONEYTOR_API_TOKEN")
    if not token:
        sys.exit("MONEYTOR_API_TOKEN is not set")
    os.makedirs(args.out, exist_ok=True)

    worth = get("assetWorth", token)
    write_json(worth, f"{args.out}/asset_worth.json")
    print(f"Net worth: {worth['netWorth']:,.2f} {worth['baseCurrency']}")

    assets = get("assets", token)
    write_json(assets, f"{args.out}/assets.json")
    write_csv(assets["assets"], f"{args.out}/assets.csv")
    print(f"Assets: {assets['count']}")

    txs, offset = [], 0
    while offset is not None:
        page = get("transactions", token, {"from": args.date_from, "to": args.date_to,
                                           "limit": 2000, "offset": offset})
        txs.extend(page["transactions"])
        offset = page["nextOffset"]
    write_csv(txs, f"{args.out}/transactions.csv")
    print(f"Transactions: {len(txs)}")

    insurance = get("insurance", token)
    write_json(insurance, f"{args.out}/insurance.json")
    write_csv(insurance.get("policies", []), f"{args.out}/insurance_policies.csv")
    print(f"Insurance policies: {len(insurance.get('policies', []))}")


if __name__ == "__main__":
    main()
