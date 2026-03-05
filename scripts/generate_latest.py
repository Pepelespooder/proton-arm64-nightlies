#!/usr/bin/env python3
"""
Generate latest.json for the nightly build index.
Usage: generate_latest.py <out> <versionName> <date> <gitHash>
                          <wcpFile> <wcpSha> <wcpxzFile> <wcpxzSha> <releaseTag>
"""
import json
import sys

if len(sys.argv) < 10:
    print("Usage: generate_latest.py <out> <versionName> <date> <gitHash> "
          "<wcpFile> <wcpSha> <wcpxzFile> <wcpxzSha> <releaseTag>")
    sys.exit(1)

_, out_path, version_name, date, git_hash, \
    wcp_file, wcp_sha, wcpxz_file, wcpxz_sha, release_tag = sys.argv

data = {
    "versionName": version_name,
    "date": date,
    "gitHash": git_hash,
    "wcp": {
        "fileName": wcp_file,
        "sha256": wcp_sha,
    },
    "wcpxz": {
        "fileName": wcpxz_file,
        "sha256": wcpxz_sha,
    },
    "releaseTag": release_tag,
}

with open(out_path, "w") as f:
    json.dump(data, f, indent=2)

print(json.dumps(data, indent=2))
