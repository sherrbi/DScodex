"""Prepare own empty home/config only. Never copy the original home or invoke tools."""
import argparse,json
from pathlib import Path

def prepare(target, apply=False):
    root=Path(target).resolve()
    home=root/"state"/"home"
    config=home/"config.toml"
    source=Path(__file__).parent/"templates"/"config.example.toml"
    result={"mode":"apply" if apply else "preview", "home":str(home),"preserve_existing_config":True,"tools_installed":False,"full_dscodex_ready":False}
    if apply:
        home.mkdir(parents=True,exist_ok=True)
        if not config.exists():
            with config.open("x",encoding="utf-8") as f: f.write(source.read_text(encoding="utf-8"))
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--target",required=True);p.add_argument("--apply",action="store_true");a=p.parse_args()
    print(json.dumps(prepare(a.target,a.apply),ensure_ascii=False,indent=2))
