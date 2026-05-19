from pathlib import Path


def summarize_generated_configs(config_dir=Path("output_builds/SPINELEAF")):
    configs = sorted(config_dir.glob("*.cfg"))
    return {
        "config_dir": str(config_dir),
        "device_count": len(configs),
        "spines": [path.stem for path in configs if path.stem.startswith("spine")],
        "leaves": [path.stem for path in configs if path.stem.startswith("leaf")],
    }


if __name__ == "__main__":
    print(summarize_generated_configs())
