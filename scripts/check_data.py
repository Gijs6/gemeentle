#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data.gemeente_info as gemeente_info

FIELDS = ["vlag", "wapen", "kaart", "inwoners", "oppervlakte", "provincie", "burgemeester"]

names = sorted(gemeente_info.names())
missing = {field: [] for field in FIELDS}

col_w = max(len(n) for n in names) + 2
header = f"{'Gemeente':<{col_w}}" + "  ".join(f"{f:<12}" for f in FIELDS)
print(header)
print("-" * len(header))

for name in names:
    info = gemeente_info.get(name)
    for field in FIELDS:
        if not info.get(field):
            missing[field].append(name)
    row = f"{name:<{col_w}}" + "  ".join(
        f"{'ja':<12}" if info.get(f) else f"{'ONTBREEKT':<12}" for f in FIELDS
    )
    print(row)

print("\nSamenvatting:")
for field in FIELDS:
    count = len(missing[field])
    print(f"  {field}: {count} ontbrekend")
