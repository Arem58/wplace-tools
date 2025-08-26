
from PIL import Image, ImageDraw
import numpy as np
import pandas as pd
import os
from typing import Tuple

def find_and_export_color(
    image_path: str,
    target_rgb: Tuple[int, int, int],
    tol: int = 0,
    canvas_origin: Tuple[int, int] = (0, 0),
    out_prefix: str = ""
):
    """
    - image_path: ruta de la imagen de referencia (PNG/JPG).
    - target_rgb: color a localizar, por ejemplo (15, 183, 154).
    - tol: tolerancia por canal (0 = exacto; usa 1-3 si tu herramienta redondea colores).
    - canvas_origin: desplazamiento (x0,y0) donde vas a colocar la ESQUINA SUPERIOR IZQUIERDA de la imagen en el lienzo.
                     Así obtienes coordenadas absolutas listas para pintar.
    - out_prefix: texto opcional para prefijar los archivos de salida.

    Salidas:
    - coords_...csv : tabla con x,y (imagen) y X,Y (coordenadas en el lienzo) y el color.
    - mask_...png   : máscara RGBA que deja visibles solo los píxeles del color.
    - preview_...png: vista previa: imagen atenuada + píxeles del color resaltados.
    """
    base = os.path.splitext(os.path.basename(image_path))[0]
    safe_rgb = f"{target_rgb[0]}_{target_rgb[1]}_{target_rgb[2]}"
    tag = f"{out_prefix}_rgb_{safe_rgb}_tol_{tol}".strip("_")
    csv_path = f"coords_{base}_{tag}.csv"
    mask_path = f"mask_{base}_{tag}.png"
    preview_path = f"preview_{base}_{tag}.png"

    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)

    R, G, B = target_rgb
    mask = (
        (np.abs(arr[:,:,0] - R) <= tol) &
        (np.abs(arr[:,:,1] - G) <= tol) &
        (np.abs(arr[:,:,2] - B) <= tol)
    )

    ys, xs = np.where(mask)
    count = len(xs)

    # CSV con coordenadas
    if count > 0:
        sub = arr[mask]
        df = pd.DataFrame({
            "x": xs, "y": ys,
            "X": xs + canvas_origin[0],  # coords en lienzo
            "Y": ys + canvas_origin[1],
            "r": sub[:,0], "g": sub[:,1], "b": sub[:,2],
        })
    else:
        df = pd.DataFrame(columns=["x","y","X","Y","r","g","b"])
    df.to_csv(csv_path, index=False)

    # Máscara RGBA (solo ese color visible)
    h, w = arr.shape[:2]
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[:,:,:3] = arr
    out[:,:,3] = (mask * 255).astype(np.uint8)
    Image.fromarray(out, mode="RGBA").save(mask_path)

    # Preview: fondo atenuado + píxeles destino fuertes
    preview = Image.fromarray(arr).convert("RGBA")
    # Atenuar todo
    over = Image.new("RGBA", preview.size, (0,0,0,180))
    preview = Image.alpha_composite(preview, over)
    # Colocar solo los píxeles del color por encima
    only = Image.fromarray(out, mode="RGBA")
    preview = Image.alpha_composite(preview, only)
    preview.save(preview_path)

    print(f"[OK] {target_rgb} -> {count} px")
    print(f"CSV: {csv_path}")
    print(f"MASK: {mask_path}")
    print(f"PREVIEW: {preview_path}")
    return csv_path, mask_path, preview_path

if __name__ == "__main__":
    # --- EJEMPLO DE USO ---
    # Cambia estos valores por los tuyos:
    image_path = "assets/converted_ChatGPT Image Aug 20, 2025, 09_15_42 PM.png"
    target_rgb = (15, 183, 154)
    tol = 0
    canvas_origin = (0, 0)  # mueve esto si tu plantilla empieza más a la derecha/abajo
    find_and_export_color(image_path, target_rgb, tol, canvas_origin, out_prefix="demo")
