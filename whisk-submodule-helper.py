#! /usr/bin/env python3
#
# 2021 Garmin Ltd. or its subsidiaries
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Whisk Submodule Fetch Helper")
    parser.add_argument("parent", help="Submodule parent")
    parser.add_argument("path", help="Path to submodule (relative to parent)")
    parser.add_argument(
        "--depth", type=int, default=0, help="Attempt shallow clone with depth"
    )
    parser.add_argument(
        "--remote", action="store_true", help="Use remote HEAD instead of recorded SHA1"
    )
    parser.add_argument(
        "--patch",
        dest="patches",
        action="append",
        default=[],
        help="Apply patch after checkout",
    )

    args = parser.parse_args()

    submodule_path = os.path.join(args.parent, args.path)

    if args.remote:
        p = subprocess.run(
            [
                "git",
                "-C",
                args.parent,
                "submodule",
                "update",
                "--init",
                "--remote",
                submodule_path,
            ],
            check=True,
        )
    else:
        p = subprocess.run(
            [
                "git",
                "-C",
                args.parent,
                "config",
                "--get",
                "submodule.%s.url" % args.path,
            ],
            stdout=subprocess.PIPE,
            check=True,
        )
        submodule_url = p.stdout.decode("utf-8")

        os.makedirs(args.path, exist_ok=True)
        subprocess.run(["git", "init", submodule_path], check=True)
        p = subprocess.run(
            ["git", "-C", submodule_path, "remote"], stdout=subprocess.PIPE, check=True
        )

        if not "origin" in p.stdout.decode("utf-8").split():
            subprocess.run(
                ["git", "-C", submodule_path, "remote", "add", "origin", submodule_url],
                check=True,
            )

        p = subprocess.run(
            ["git", "-C", args.parent, "ls-tree", "-d", "HEAD", args.path],
            stdout=subprocess.PIPE,
            check=True,
        )
        sha1 = p.stdout.decode("utf-8").split()[2]

        full_fetch = False
        if args.depth:
            p = subprocess.run(
                [
                    "git",
                    "-C",
                    submodule_path,
                    "fetch",
                    "origin",
                    "--depth",
                    str(args.depth),
                    sha1,
                ]
            )
            if p.returncode != 0:
                print(
                    "WARNING: The repo '%s' failed a shallow clone. Performing a full clone"
                    % args.path
                )
                full_fetch = True
        else:
            full_fetch = True

        if full_fetch:
            subprocess.run(["git", "-C", submodule_path, "fetch", "origin"], check=True)

        subprocess.run(["git", "-C", submodule_path, "checkout", sha1], check=True)

    for patch in args.patches:
        subprocess.run(["git", "-C", submodule_path, "am", patch], check=True)


if __name__ == "__main__":
    sys.exit(main())
