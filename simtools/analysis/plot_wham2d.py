#!/usr/bin/env python3
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import argparse

def main():
    parser = argparse.ArgumentParser(description="Pinta el mapa 2D de energía libre obtenido de WHAM2D")
    parser.add_argument("--path", type=str, required=True,
                        help="Directorio que contiene el archivo de salida de WHAM2D (por defecto 'wham2d.out')")
    parser.add_argument("--file", type=str, default="wham2d.out",
                        help="Nombre del archivo de salida de WHAM2D (default: wham2d.out)")
    parser.add_argument("--zlim", type=float, nargs=2, default=None,
                        help="Rango opcional para la escala de energía libre (por ejemplo --zlim 0 10)")
    parser.add_argument("--save", type=str, default=None,
                        help="Ruta opcional para guardar el gráfico (por ejemplo --save fe_map.png). "
                             "Si se usa con --meansfile, el gráfico 1D se guarda con sufijo _1d.")
    parser.add_argument("--meansfile", type=str, nargs="+", default=None,
                        help="Archivo con los valores medios (window mean_c1 std_c1 mean_c2 std_c2) para dibujar la trayectoria 1D sobre el mapa 2D")
    args = parser.parse_args()

    filepath = os.path.join(args.path, args.file)

    if not os.path.isfile(filepath):
        print(f"❌ No se encontró el archivo: {filepath}")
        sys.exit(1)

    data = np.loadtxt(filepath)

    if data.shape[1] < 3:
        print("❌ El archivo WHAM2D debe tener al menos tres columnas (x, y, F).")
        sys.exit(1)

    x = data[:, 0]
    y = data[:, 1]
    F = data[:, 2]

    x_unique = np.unique(x)
    y_unique = np.unique(y)
    nx, ny = len(x_unique), len(y_unique)

    if nx * ny != len(F):
        print("⚠️ Advertencia: los datos no parecen formar una grilla regular.")
        print("   Se intentará una interpolación simple.")
        return

    X, Y = np.meshgrid(x_unique, y_unique)
    Z = F.reshape((nx, ny)).T

    Z[Z > 1e6] = np.nan
    Z -= np.nanmin(Z)

    cmap = plt.get_cmap("turbo").copy()
    cmap.set_bad(alpha=0)

    plt.figure(1, figsize=(6, 12))
    c = plt.pcolormesh(X, Y, Z, shading='auto', cmap=cmap)
    cbar = plt.colorbar(c)
    cbar.set_label(label="Free energy (kcal/mol)", size=18)
    cbar.ax.tick_params(labelsize=15)

    if args.zlim:
        plt.clim(args.zlim)

    plt.xlabel("Reaction coordinate x$_1$ (Å)", fontsize=18)
    plt.ylabel("Reaction coordinate x$_2$ (Å)", fontsize=18)
    plt.title("Free energy surface", fontsize=21)
    plt.tick_params(axis='both', labelsize=15)
    plt.tight_layout()

    if args.meansfile:
        from scipy.spatial import cKDTree

        colors = ["skyblue", "orange", "lime", "magenta"]
        valid_mask = np.isfinite(Z.ravel()) & (Z.ravel() < 1e6)
        coords_valid = np.column_stack([X.ravel()[valid_mask], Y.ravel()[valid_mask]])
        F_valid = Z.ravel()[valid_mask]
        tree = cKDTree(coords_valid) if len(coords_valid) > 0 else None

        for idx, means_file in enumerate(args.meansfile):
            if not os.path.isfile(means_file):
                print(f"⚠️ No se encontró el archivo {means_file}")
                continue

            means = np.loadtxt(means_file)
            if means.shape[1] < 5:
                print(f"⚠️ El archivo {means_file} no tiene 5 columnas.")
                continue

            color = colors[idx % len(colors)]
            mean_c1, mean_c2 = means[:, 1], means[:, 3]

            plt.figure(1)
            plt.plot(mean_c1, mean_c2, color=color, lw=1.5, label=f"Trajectory {idx+1}")
            plt.scatter(mean_c1, mean_c2, color=color, s=20, zorder=3)

            if tree is not None:
                F_path = []
                for x_val, y_val in zip(mean_c1, mean_c2):
                    dist, i_near = tree.query([x_val, y_val])
                    F_path.append(F_valid[i_near] if dist <= 0.15 else np.nan)

                F_path = np.array(F_path)
                valid_idx = np.isfinite(F_path)
                if np.any(valid_idx):
                    plt.figure(2)
                    plt.plot(mean_c1[valid_idx], F_path[valid_idx], '-o',
                             color=color, label=f"Trajectory {idx+1}")

            print(f"📈 Añadida trayectoria {idx+1} desde {means_file}")

        if plt.fignum_exists(2):
            plt.figure(2)
            plt.xlabel("Reaction coordinate x$_1$ (Å)")
            plt.ylabel("Free energy (kcal/mol)")
            plt.title("1D curve from 2D surface")
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()

    if args.save:
        plt.figure(1)
        plt.savefig(args.save, dpi=300)
        print(f"✅ Gráfico guardado en: {args.save}")
        if plt.fignum_exists(2):
            base, ext = os.path.splitext(args.save)
            save2 = f"{base}_1d{ext}"
            plt.figure(2)
            plt.savefig(save2, dpi=300)
            print(f"✅ Gráfico 1D guardado en: {save2}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
