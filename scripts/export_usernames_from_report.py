import csv
import os

SRC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "ready_to_join_vegan_challenge.csv")
OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "ready_to_join_vegan_challenge_usernames.txt")


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"Source report not found: {SRC}")

    usernames = []
    seen = set()
    with open(SRC, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = (row.get("ig_username") or "").strip()
            if u and u not in seen:
                seen.add(u)
                usernames.append(u)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(usernames))

    print(f"Wrote {len(usernames)} usernames to {OUT}")


if __name__ == "__main__":
    main()




