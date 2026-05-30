"""
Script de preparación del dataset SoyaLens.

Operaciones:
  1. Fusiona las clases 'Skin Damaged' (3) y 'Spotted' (4) en una sola clase 'damaged'.
  2. Reasigna todos los índices de clase al nuevo mapa de 4 clases.
  3. Divide el dataset en train / val / test (70 / 15 / 15).
  4. Aparta 15 imágenes como 'smoke_test' (datos de prueba del modelo, no entran en ninguna split).
  5. Genera un data.yaml actualizado compatible con YOLO.

Clases finales (4):
  0: broken     ← antes Broken (0)
  1: immature   ← antes Immature (1)
  2: intact     ← antes Intact (2)
  3: damaged    ← antes Skin Damaged (3) + Spotted (4)

Uso:
  python ai/prepare_dataset.py

Requisitos: ninguno (solo stdlib de Python)
"""

import shutil
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
DATASET_SRC = Path(r"C:\Users\alfre\Documents\Tarts\Coding\proyectos\BWAI_project_soyaLens\Defect Soybean.yolov8")
DATASET_OUT = Path(r"C:\Users\alfre\Documents\Tarts\Coding\proyectos\BWAI_project_soyaLens\soyaLens\ai\dataset")

SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
SMOKE_TEST_N = 15
SEED = 42

# Mapeo de clases antiguas → nuevas
# Clases originales: 0=Broken, 1=Immature, 2=Intact, 3=Skin Damaged, 4=Spotted
# Clases nuevas:     0=broken, 1=immature, 2=intact, 3=damaged
CLASS_MAP = {0: 0, 1: 1, 2: 2, 3: 3, 4: 3}
NEW_CLASS_NAMES = ["broken", "immature", "intact", "damaged"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def remap_label_file(src: Path, dst: Path) -> None:
    """Lee un archivo .txt YOLO, reasigna los índices de clase y lo guarda."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for line in src.read_text().strip().splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        old_class = int(parts[0])
        new_class = CLASS_MAP[old_class]
        lines.append(f"{new_class} " + " ".join(parts[1:]))
    dst.write_text("\n".join(lines))


def copy_pair(img_src: Path, lbl_src: Path, split_dir: Path) -> None:
    """Copia un par imagen + label al directorio de split indicado."""
    (split_dir / "images").mkdir(parents=True, exist_ok=True)
    (split_dir / "labels").mkdir(parents=True, exist_ok=True)
    shutil.copy2(img_src, split_dir / "images" / img_src.name)
    remap_label_file(lbl_src, split_dir / "labels" / lbl_src.name)


def write_yaml(out_dir: Path, splits: list[str]) -> None:
    """Genera el data.yaml compatible con YOLO en el directorio de salida."""
    lines = [
        f"path: {out_dir.as_posix()}",
        "",
    ]
    for split in splits:
        lines.append(f"{split}: {split}/images")
    lines += [
        "",
        f"nc: {len(NEW_CLASS_NAMES)}",
        f"names: {NEW_CLASS_NAMES}",
    ]
    (out_dir / "data.yaml").write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    random.seed(SEED)

    src_images = sorted((DATASET_SRC / "train" / "images").glob("*"))
    src_labels_dir = DATASET_SRC / "train" / "labels"

    # Filtrar solo imágenes con su label correspondiente
    pairs: list[tuple[Path, Path]] = []
    for img in src_images:
        lbl = src_labels_dir / (img.stem + ".txt")
        if lbl.exists():
            pairs.append((img, lbl))

    print(f"Total de pares imagen-label encontrados: {len(pairs)}")

    random.shuffle(pairs)

    # Apartar smoke_test primero
    smoke_pairs = pairs[:SMOKE_TEST_N]
    remaining  = pairs[SMOKE_TEST_N:]

    total = len(remaining)
    n_train = int(total * SPLIT_RATIOS["train"])
    n_val   = int(total * SPLIT_RATIOS["val"])

    splits_data = {
        "train": remaining[:n_train],
        "val":   remaining[n_train : n_train + n_val],
        "test":  remaining[n_train + n_val:],
    }

    # Limpiar y reconstruir el directorio de salida
    if DATASET_OUT.exists():
        shutil.rmtree(DATASET_OUT)
    DATASET_OUT.mkdir(parents=True)

    # Copiar splits
    for split_name, split_pairs in splits_data.items():
        split_dir = DATASET_OUT / split_name
        for img, lbl in split_pairs:
            copy_pair(img, lbl, split_dir)
        print(f"  {split_name:6s}: {len(split_pairs)} imágenes")

    # Copiar smoke_test
    smoke_dir = DATASET_OUT / "smoke_test"
    for img, lbl in smoke_pairs:
        copy_pair(img, lbl, smoke_dir)
    print(f"  smoke_test: {len(smoke_pairs)} imágenes")

    # Generar data.yaml
    write_yaml(DATASET_OUT, ["train", "val", "test"])
    print(f"\nDataset preparado en: {DATASET_OUT}")
    print(f"data.yaml generado con {len(NEW_CLASS_NAMES)} clases: {NEW_CLASS_NAMES}")


if __name__ == "__main__":
    main()
