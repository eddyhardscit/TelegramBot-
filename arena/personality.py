import json, random
from pathlib import Path
class ArenaPersonality:
    def __init__(self,path="personality.json"): self.data=json.loads(Path(path).read_text(encoding="utf-8"))
    def random_line(self,category):
        lines=self.data.get("responses",{}).get(category) or self.data.get("responses",{}).get("standard",[])
        return random.choice(lines) if lines else "The Arena is open."
    def greeting(self,name,returning):
        key="returning_greetings" if returning else "first_greetings"; lines=self.data.get(key,[])
        return random.choice(lines).format(name=name) if lines else f"Welcome to the Arena, {name}."
