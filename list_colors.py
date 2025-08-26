from PIL import Image
import numpy as np
import pandas as pd
import os

def list_colors(image_path: str, sort_desc=True) -> pd.DataFrame:
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    flat = arr.reshape(-1, 3)
    colors, counts = np.unique(flat, axis=0, return_counts=True)
    df = pd.DataFrame(colors, columns=["r","g","b"])
    df["count"] = counts
    if sort_desc:
        df = df.sort_values("count", ascending=False).reset_index(drop=True)
    return df

if __name__ == "__main__":
    df = list_colors("assets/converted_ChatGPT Image Aug 20, 2025, 09_15_42 PM.png")
    print(df.head(20))  # muestra los 20 colores más frecuentes
    df.to_csv("colors_mi_imagen.csv", index=False)  # Guardar CSV con todos los colores
    txt_path = "colors_mi_imagen.txt" # Guardar TXT con formato "rgb(R, G, B): N px"
    with open(txt_path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            r, g, b, count = int(row.r), int(row.g), int(row.b), int(row["count"])
            f.write(f"rgb({r}, {g}, {b}): {count} px\n")

    print(f"[OK] Guardados: colors_mi_imagen.csv y {txt_path}")
