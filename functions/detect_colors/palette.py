# palette_utils.py
import json
from typing import Dict, List, Tuple, Optional

RGB = Tuple[int, int, int]

def load_palette(json_path: str) -> List[Dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for d in data:
        d["rgb"] = tuple(d["rgb"])
    return data

def palette_by_rgb(palette: List[Dict]) -> Dict[RGB, Dict]:
    return {item["rgb"]: item for item in palette}

def find_by_name(palette: List[Dict], name: str) -> Optional[Dict]:
    name_lc = name.strip().lower()
    for item in palette:
        if item["name"].lower() == name_lc:
            return item
    return None

def find_exact_in_palette(rgb: RGB, palette: List[Dict]) -> Optional[Dict]:
    return palette_by_rgb(palette).get(rgb)

def resolve_target(target, palette: List[Dict]) -> Dict:
    """
    Acepta:
      - (r,g,b) que DEBE existir en paleta
      - "Nombre" (debe existir)
      - "id:NN" (debe existir)
    Retorna: {"rgb":(r,g,b), "name":str, "premium":bool, "source": "..."}
    """
    if isinstance(target, tuple) and len(target) == 3:
        item = find_exact_in_palette(target, palette)
        if not item:
            raise ValueError(f"RGB {target} no existe en la paleta.")
        return {"rgb": item["rgb"], "name": item["name"], "premium": item["premium"], "source": "exact_rgb"}

    if isinstance(target, str):
        t = target.strip()
        if t.lower().startswith("id:"):
            try:
                wanted = int(t.split(":", 1)[1])
            except ValueError:
                raise ValueError(f"ID inválido en target: {target}")
            for it in palette:
                if it["id"] == wanted:
                    return {"rgb": it["rgb"], "name": it["name"], "premium": it["premium"], "source": "by_id"}
            raise ValueError(f"No se encontró id {wanted} en la paleta.")
        item = find_by_name(palette, t)
        if item:
            return {"rgb": item["rgb"], "name": item["name"], "premium": item["premium"], "source": "by_name"}
        raise ValueError(f"No se encontró el nombre '{target}' en la paleta.")

    raise ValueError("target debe ser (r,g,b) o str (nombre o 'id:NN').")
