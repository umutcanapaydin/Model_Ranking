#!/usr/bin/env python3
"""`make leak-scan`: what the tracked tree holds that looks like data. REPORT ONLY: it never fails, and no gate runs it.

WHY (v7.3; the 2026-10-27 field harvest, 6e). An adopted codebase can arrive with a database file, a dump, a
large blob or a CSV of people already committed. `make secrets` looks for credentials; nothing looked for data,
and committing personal data is an Escalate-NOW item (AGENTS.md §3). `/setup-project` runs this once on an
adopted codebase, and its lines go into `docs/adoption-audit.md`, where the owner decides each one. No list of
exceptions exists, for an agent to keep or for anyone: a line is the owner's to answer, never to silence.

What it reads: the files git tracks, as they stand in the working tree (what a push carries, as `make secrets`).
  name    a file named like data or a key: a database (`.db`, `.sqlite`, `.sqlite3`, `.mdb`), a dump (`.dump`),
          a key store (`.p12`, `.pfx`, `id_rsa`, `id_ed25519`), infrastructure state (`.tfvars`,
          `terraform.tfstate*`), a cloud service account (`service-account*.json`)
  size    a file over 256 KB
  header  a `.csv` or `.tsv` whose first line, or a `.json` whose first 4 KB, names a personal-data field
          (email, phone, birth date, address, a person's name, a national id, a card or bank number)
A file it cannot read is a line of its own. The history is not read: what it finds there is the owner's to ask.

Exit: always 0, findings or none -- the owner ruled it report only (2026-10-28). A tree git cannot list says
CANNOT RUN and never "0 finding(s)".
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

LIMIT = 256 * 1024
NAMES = [(re.compile(r"\.(db|sqlite|sqlite3|mdb)$", re.I), "a database file"),
         (re.compile(r"\.dump$", re.I), "a database dump"),
         (re.compile(r"(\.p12|\.pfx|(^|/)id_(rsa|dsa|ecdsa|ed25519))$", re.I), "a private key store"),
         (re.compile(r"(\.tfvars|(^|/)terraform\.tfstate[^/]*)$", re.I), "infrastructure state or variables"),
         (re.compile(r"(^|/)service-account[^/]*\.json$", re.I), "a cloud service-account key")]
PERSONAL = {"email", "e_mail", "email_address", "mail_address", "phone", "phone_number", "telephone", "mobile",
            "mobile_number", "msisdn", "dob", "date_of_birth", "birth_date", "birthdate", "birthday", "address",
            "street", "street_address", "home_address", "postcode", "postal_code", "zip", "zip_code", "first_name",
            "last_name", "full_name", "surname", "given_name", "family_name", "ssn", "social_security_number",
            "national_id", "passport", "passport_number", "tax_id", "iban", "card_number", "credit_card",
            "cc_number", "cvv", "account_number"}


def field(name: str) -> str:
    """A header or key as one comparable word: `E-mail` -> `e_mail`, `Phone Number` -> `phone_number`."""
    return re.sub(r"[^a-z0-9]+", "_", name.strip().strip("\"'").lower()).strip("_")


def personal(path: Path, rel: str) -> list[str]:
    with path.open("rb") as fh:
        head = fh.read(4096).decode("utf-8", errors="replace")
    if rel.lower().endswith((".csv", ".tsv")):
        first = head.splitlines()[0] if head else ""
        names = re.split(r"[,;\t|]", first)
    else:
        names = re.findall(r'"([^"\\]{1,64})"\s*:', head)
    return sorted({field(n) for n in names} & PERSONAL)


def scan(top: Path, files: list[str]) -> list[str]:
    out = []
    for rel in files:
        p = top / rel
        if p.is_symlink() or not p.is_file():
            continue
        out += [f"  name    {rel} ({why})" for pat, why in NAMES if pat.search(rel)][:1]
        try:
            size = p.stat().st_size
            if size > LIMIT:
                out.append(f"  size    {rel} ({size // 1024} KB, over {LIMIT // 1024} KB)")
            if rel.lower().endswith((".csv", ".tsv", ".json")):
                hits = personal(p, rel)
                if hits:
                    out.append(f"  header  {rel} ({', '.join(hits)})")
        except OSError as e:
            out.append(f"  unread  {rel} ({type(e).__name__}: it was not scanned)")
    return out


def main() -> int:
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, encoding="utf-8",
                             errors="replace").stdout.strip()
        r = subprocess.run(["git", "-C", top, "ls-files", "-z"], capture_output=True) if top else None
    except OSError:                                 # no git at all: the same answer, never a traceback
        r = None
    if r is None or r.returncode != 0:
        print(f"leak-scan CANNOT RUN: git cannot list the tracked files in {os.getcwd()} -- nothing was scanned. "
              "Report only: run it in the repository")
        return 0
    files = [f for f in r.stdout.decode("utf-8", "replace").split("\0") if f]
    lines = scan(Path(top), files)
    for ln in lines:
        print(ln)
    print(f"leak-scan: {len(lines)} finding(s) in {len(files)} tracked file(s) -- report only, no gate reads it. "
          "Each line goes in docs/adoption-audit.md, §7, for the owner to decide")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                          # report only: a crash says so, and still exits 0
        print(f"leak-scan CANNOT RUN: {type(e).__name__}: {e} -- the scan stopped there. Report only")
        sys.exit(0)
