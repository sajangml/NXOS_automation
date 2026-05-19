from pathlib import Path


def summarize_generated_configs(config_dir=Path("output_builds/SPINELEAF")):
    configs = sorted(config_dir.rglob("*.cfg"))
    return {
        "config_dir": str(config_dir),
        "device_count": len(configs),
        "spines": [path.stem for path in configs if "spine" in path.stem],
        "leaves": [path.stem for path in configs if "leaf" in path.stem],
        "sites": {
            site_dir.name: len(list(site_dir.glob("*.cfg")))
            for site_dir in sorted(config_dir.iterdir())
            if site_dir.is_dir()
        },
    }


if __name__ == "__main__":
    print(summarize_generated_configs())
