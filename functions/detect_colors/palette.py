# functions/detect_colors/palette.py
import json
from typing import Tuple, Dict, Optional, List
import pandas as pd
import math

RGB = Tuple[int, int, int]

# ---------- Utilidades básicas ----------
def hex_to_rgb(hexstr: str) -> RGB:
    h = hexstr.strip().lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def rgb_to_hex(rgb: RGB) -> str:
    r,g,b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"

# ---------- Carga única y construcción de índice ----------
def _load_palette(palette_json_path: str) -> List[dict]:
    with open(palette_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for d in data:
        d["rgb"] = hex_to_rgb(d["color"])
    return data

def _build_rgb_index(palette: List[dict]) -> Dict[RGB, dict]:
    idx: Dict[RGB, dict] = {}
    for item in palette:
        idx[tuple(item["rgb"])] = item  # último gana si hay duplicados
    return idx

# ---------- Búsqueda ----------
def _nearest_in_palette(rgb: RGB, palette: List[dict]) -> dict:
    r,g,b = rgb
    best, best_d2 = None, float("inf")
    for p in palette:
        pr,pg,pb = p["rgb"]
        d2 = (r-pr)**2 + (g-pg)**2 + (b-pb)**2
        if d2 < best_d2:
            best, best_d2 = p, d2
    return best

def get_color_info(
    rgb: RGB,
    palette_json_path: str,
    use_nearest: bool = True,
    _cache: dict = {}
) -> Dict[str, Optional[str]]:
    """
    Devuelve dict:
      name, hex, id, isPremium, match ('exact'|'nearest'|'none'), palette_rgb (tupla)
    """
    if palette_json_path not in _cache:
        pal = _load_palette(palette_json_path)
        _cache[palette_json_path] = {
            "palette": pal,
            "index": _build_rgb_index(pal),
        }
    palette = _cache[palette_json_path]["palette"]
    index = _cache[palette_json_path]["index"]

    p = index.get(tuple(rgb))
    if p:
        return {
            "name": p["name"],
            "hex": p["color"],
            "id": p.get("id"),
            "isPremium": p.get("isPremium", False),
            "match": "exact",
            "palette_rgb": tuple(p["rgb"])
        }

    if not use_nearest:
        return {
            "name": None, "hex": None, "id": None, "isPremium": None,
            "match": "none", "palette_rgb": None
        }

    p = _nearest_in_palette(rgb, palette)
    return {
        "name": p["name"],
        "hex": p["color"],
        "id": p.get("id"),
        "isPremium": p.get("isPremium", False),
        "match": "nearest",
        "palette_rgb": tuple(p["rgb"])
    }

def map_df_colors(
    df: pd.DataFrame,
    palette_json_path: str,
    use_nearest: bool = True
) -> pd.DataFrame:
    """
    Añade name, hex, id, match a un DF con r,g,b.
    Usa la paleta indexada en cache para acelerar (no recarga por fila).
    """
    rows = []
    for _, row in df.iterrows():
        rgb = (int(row["r"]), int(row["g"]), int(row["b"]))
        info = get_color_info(rgb, palette_json_path, use_nearest=use_nearest)
        rows.append({
            "name": info["name"],
            "hex": info["hex"],
            "id": info["id"],
            "isPremium": info["isPremium"],   # <---
            "match": info["match"],
        })
    info_df = pd.DataFrame(rows, index=df.index)
    return pd.concat([df.reset_index(drop=True), info_df.reset_index(drop=True)], axis=1)

# ---------- Extras útiles para tu flujo ----------
def require_color_exact(rgb: RGB, palette_json_path: str):
    """Lanza ValueError si el RGB no existe en la paleta (modo estricto)."""
    info = get_color_info(rgb, palette_json_path, use_nearest=False)
    if info["match"] != "exact":
        raise ValueError(
            f"RGB {rgb} no existe en la paleta permitida ({palette_json_path}). "
            f"Sugerencia: verifica la exportación de la web. HEX esperado: {rgb_to_hex(rgb)}."
        )
    return info

def verify_image_palette(image_path: str, palette_json_path: str) -> List[RGB]:
    """
    Devuelve lista de RGB que aparecen en la imagen pero NO están en la paleta.
    Lista vacía => todo OK.
    """
    from PIL import Image
    import numpy as np

    # cache: no recargar paleta
    pal = _load_palette(palette_json_path)
    idx = _build_rgb_index(pal)

    arr = np.array(Image.open(image_path).convert("RGB")).reshape(-1, 3)
    uniq = {tuple(x) for x in arr}
    unknown = [rgb for rgb in uniq if rgb not in idx]
    return sorted(unknown)
