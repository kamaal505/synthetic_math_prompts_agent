import os
import json
from pathlib import Path

def save_prompts(valid_list, discarded_list, save_path):
    save_dir = Path(save_path)
    os.makedirs(save_dir, exist_ok=True)

    # ✅ Save full JSON with full fidelity
    with open(save_dir / "valid.json", "w", encoding="utf-8") as f:
        json.dump(valid_list, f, indent=2, ensure_ascii=False)

    with open(save_dir / "discarded.json", "w", encoding="utf-8") as f:
        json.dump(discarded_list, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved to: {save_dir}")
    print(f"✅ valid.json ({len(valid_list)} entries)")
    print(f"❌ discarded.json ({len(discarded_list)} entries)")