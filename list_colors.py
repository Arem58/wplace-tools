from PIL import Image
import numpy as np
import pandas as pd
from typing import Tuple
from functions.detect_colors.palette import (load_palette, palette_by_rgb)

def list_colors(image_path: str, palette_json: str, sort_desc: bool = True) -> pd.DataFrame:
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    flat = arr.reshape(-1, 3)

    colors, counts = np.unique(flat, axis=0, return_counts=True)
    df = pd.DataFrame(colors, columns=["r","g","b"])
    df["count"] = counts
    if sort_desc:
        df = df.sort_values("count", ascending=False).reset_index(drop=True)

    palette = load_palette(palette_json)
    idx = palette_by_rgb(palette)

    # Validación estricta: TODOS los colores deben existir en la paleta
    tuples = [tuple(x) for x in df[["r", "g", "b"]].to_numpy()]
    mask_in = [t in idx for t in tuples]
    if not all(mask_in):
        illegal = df.loc[[i for i, ok in enumerate(mask_in) if not ok], ["r","g","b","count"]]
        raise ValueError("Colores fuera de paleta:\n" + illegal.to_string(index=False))

    # Enriquecer con nombre y premium (ya que todos están en paleta)
    df["id"]      = [idx[t]["id"] for t in tuples]
    df["name"] = [idx[t]["name"] for t in tuples]
    df["premium"] = [bool(idx[t]["premium"]) for t in tuples]
    return df

if __name__ == "__main__":
    image_path = "assets/converted_Screenshot_20250831_140046_Spotify(1).png"
    palette_json = "assets/wplace-color.json"

    df = list_colors(image_path, palette_json)
    print(df.head(30))  # muestra los 20 colores más frecuentes

    csv_path = "output/list_color/colors_mi_imagen.csv"
    txt_path = "output/list_color/colors_mi_imagen.txt"

    df.to_csv(csv_path, index=False)  # Guardar CSV con todos los colores

    # anchos para alinear
    w_count = int(df["count"].astype(str).str.len().max())     # ancho de la columna "px"
    w_id    = int(df["id"].astype(str).str.len().max())        # ancho máximo de ID

    with open(txt_path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            r, g, b = int(row.r), int(row.g), int(row.b)
            count   = int(row["count"])
            _id     = int(row["id"])
            name    = str(row["name"])
            # estrella ocupa SIEMPRE 2 caracteres: "★ " (premium) o "  " (no premium)
            star2   = "★ " if bool(row["premium"]) else "   "

            # VS Code reconoce 'rgb(R, G, B)' con espacios
            rgb_str = f"rgb({r:>3}, {g:>3}, {b:>3})"
            # ejemplo: rgb( 51,  57,  65): 12035 px | #58 ★ Dark Slate
            line = f"{rgb_str}: {count:>{w_count}} px | id:{_id:>{w_id}} {star2}{name}"
            f.write(line + "\n")

    print(f"[OK] Guardados: colors_mi_imagen.csv y {txt_path}")
