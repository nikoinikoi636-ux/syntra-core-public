from pathlib import Path
from .utils import save_json, load_json
import json, shutil

def pull_rules(local_repo_dir: Path, dest_rules_dir: Path):
    # Copies any *.json from local_repo_dir/heart_rules into dest_rules_dir
    src = local_repo_dir / "heart_rules"
    dest_rules_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    if src.exists():
        for f in src.glob("*.json"):
            shutil.copy2(str(f), str(dest_rules_dir / f.name))
            copied.append(f.name)
    return copied

def apply_policy_config(config_json_path: Path, active_policy_symlink: Path):
    # config_json contains {"policy":"heart_rules_balanced.json"}
    cfg = load_json(config_json_path, {})
    pol = cfg.get("policy")
    if not pol:
        raise ValueError("Missing 'policy' in config json")
    target = active_policy_symlink.parent / pol
    if not target.exists():
        raise FileNotFoundError(f"Policy not found: {target}")
    # create/update symlink-like marker (write a small file pointing to active policy)
    active_policy_symlink.write_text(target.name, encoding="utf-8")
    return target
