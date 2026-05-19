from pathlib import Path


def summarize_generated_configs(config_dir=Path("output_builds/SPINELEAF")):
    configs = sorted(config_dir.rglob("*.cfg"))
    names = [path.stem for path in configs]
    return {
        "config_dir": str(config_dir),
        "device_count": len(configs),
        "super_spines": [name for name in names if "-SS" in name],
        "spines": [name for name in names if "-SP" in name],
        "leaves": [name for name in names if "-LF" in name],
        "border_leaves": [
            name for name in names if name.endswith("-LF07") or name.endswith("-LF08")
        ],
        "sites": {
            site_dir.name: len(list(site_dir.glob("*.cfg")))
            for site_dir in sorted(config_dir.iterdir())
            if site_dir.is_dir()
        },
    }


if __name__ == "__main__":
    print(summarize_generated_configs())
