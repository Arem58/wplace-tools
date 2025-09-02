
from PIL import Image
import numpy as np
import pandas as pd
import os
from typing import Tuple, Union

from functions.detect_colors.palette import load_palette, resolve_target

TargetType = Union[Tuple[int, int, int], str]

def find_and_export_color(
    image_path: str,
    target: TargetType,
    palette_json: str,
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

    palette = load_palette(palette_json)
    resolved = resolve_target(target, palette)
    R, G, B = resolved["rgb"]
    target_name = resolved["name"]
    target_premium = resolved["premium"]

    base = os.path.splitext(os.path.basename(image_path))[0]
    safe_rgb = f"{R}_{G}_{B}"
    safe_name = (target_name or "unknown").replace(" ", "_")
    tag = f"{out_prefix}_{safe_name}_rgb_{safe_rgb}".strip("_")
    csv_path = f"output/find_color/coords_{base}_{tag}.csv"
    mask_path = f"output/find_color/mask_{base}_{tag}.png"
    preview_path = f"output/find_color/preview_{base}_{tag}.png"

    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)

    # TOLERANCIA 0 – coincidencia exacta
    mask = ((arr[:,:,0] == R) & (arr[:,:,1] == G) & (arr[:,:,2] == B))
    ys, xs = np.where(mask)
    count = len(xs)

    # CSV con coordenadas
    if count > 0:
        sub = arr[mask]
        df = pd.DataFrame({
            "x": xs, "y": ys,
            "X": xs + canvas_origin[0],
            "Y": ys + canvas_origin[1],
            "r": sub[:,0], "g": sub[:,1], "b": sub[:,2],
            "name": target_name,
            "premium": target_premium
        })
    else:
        df = pd.DataFrame(columns=["x","y","X","Y","r","g","b","name","premium"])
    df.to_csv(csv_path, index=False)

    # Máscara RGBA (solo ese color visible)
    h, w = arr.shape[:2]
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[:,:,:3] = arr
    out[:,:,3] = (mask * 255).astype(np.uint8)
    from PIL import Image as _Image
    _Image.fromarray(out, mode="RGBA").save(mask_path)

    # Preview: fondo atenuado + píxeles destino fuertes
    preview = _Image.fromarray(arr).convert("RGBA")
    # Atenuar todo
    over = _Image.new("RGBA", preview.size, (0,0,0,180))
    preview = _Image.alpha_composite(preview, over)
    # Colocar solo los píxeles del color por encima
    only = _Image.fromarray(out, mode="RGBA")
    preview = _Image.alpha_composite(preview, only)
    preview.save(preview_path)

    print(f"[TARGET] {target} -> RGB {(R,G,B)} | name={target_name} premium={target_premium}")
    print(f"[OK] {(R,G,B)} -> {count} px")
    print(f"CSV: {csv_path}")
    print(f"MASK: {mask_path}")
    print(f"PREVIEW: {preview_path}")
    return csv_path, mask_path, preview_path

if __name__ == "__main__":
    # --- EJEMPLO DE USO ---
    # Cambia estos valores por los tuyos:
    image_path = "assets/converted_WhatsApp Image 2025-08-22 at 1.22.53 AM.jpeg.jpg"
    palette_json = "assets/wplace-color.json"

    target="Black"
    # target_rgb = (15, 183, 154)
    # tol = 0
    # canvas_origin = (0, 0)  # mueve esto si tu plantilla empieza más a la derecha/abajo
    find_and_export_color(image_path, target, palette_json)
