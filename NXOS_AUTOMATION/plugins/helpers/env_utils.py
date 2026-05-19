import argparse
import os
import sys

from nornir.core.filter import F


def parse_env_argument(default="spineleaf"):
    parser = argparse.ArgumentParser(description="Select target environment")
    parser.add_argument("--env", default=default, help="Environment name")
    args, _ = parser.parse_known_args(sys.argv[1:])
    env = args.env.lower()
    os.environ["TARGET_ENV"] = env
    print(f"Target environment set to: {env.upper()}")
    return env


def get_active_env(default="spineleaf"):
    return os.getenv("TARGET_ENV", default).lower()


def filter_nornir_by_env(nr, env):
    nr_filtered = nr.filter(F(data__env=env.lower()))
    print(f"Filtered {len(nr_filtered.inventory.hosts)} hosts for environment '{env}'.")
    return nr_filtered
