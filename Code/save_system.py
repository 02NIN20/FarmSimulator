from __future__ import annotations
import os, json, time
from typing import List, Dict, Any, Optional

def _now_str() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class SaveManager:
    def __init__(self, dir_path: str = "saves") -> None:
        self.dir = dir_path
        os.makedirs(self.dir, exist_ok=True)

    def _slot_path(self, slot_id: str) -> str:
        return os.path.join(self.dir, f"{slot_id}.json")

    def _next_free_id(self) -> str:
        i = 1
        while True:
            sid = f"slot_{i}"
            if not os.path.exists(self._slot_path(sid)):
                return sid
            i += 1

    def list_slots(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for fname in sorted(os.listdir(self.dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self.dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                out.append({
                    "id": data.get("id", fname[:-5]),
                    "name": data.get("name", "Partida"),
                    "created": data.get("created", ""),
                    "updated": data.get("updated", ""),
                    "scene_index": int(data.get("scene_index", 1)),
                    "clock_elapsed": float(data.get("clock_elapsed", 0.0)),
                    "seconds_per_day": float(data.get("seconds_per_day", 300.0)),
                })
            except Exception:
                out.append({
                    "id": fname[:-5], "name": "Corrupto",
                    "created": "?", "updated": "?", "scene_index": -1,
                    "clock_elapsed": 0.0, "seconds_per_day": 300.0
                })
        return out

    def load(self, slot_id: str) -> Optional[Dict[str, Any]]:
        path = self._slot_path(slot_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, slot_id: str, data: Dict[str, Any]) -> str:
        if not slot_id:
            slot_id = self._next_free_id()
        path = self._slot_path(slot_id)
        data["id"] = slot_id
        data["updated"] = _now_str()
        if not os.path.exists(path):
            data.setdefault("created", data["updated"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return slot_id

    def create(self, data: Dict[str, Any], name: Optional[str] = None) -> str:
        sid = self._next_free_id()
        data["id"] = sid
        data["name"] = name or f"Partida {sid.split('_')[-1]}"
        data["created"] = _now_str()
        data["updated"] = data["created"]
        with open(self._slot_path(sid), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return sid

    def delete(self, slot_id: str) -> None:
        path = self._slot_path(slot_id)
        if os.path.exists(path):
            os.remove(path)

    def rename(self, slot_id: str, new_name: str) -> None:
        data = self.load(slot_id)
        if not data:
            return
        data["name"] = new_name.strip() or data.get("name", "Partida")
        self.save(slot_id, data)
