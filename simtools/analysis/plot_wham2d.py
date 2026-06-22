#!/usr/bin/env python3
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import argparse


def read_wham2d(filepath):
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
        sys.exit(1)
    Z = F.reshape((nx, ny)).T   # Z[iy, ix]
    Z[Z > 1e6] = np.nan
    Z -= np.nanmin(Z)
    return x_unique, y_unique, Z


def read_meta(meta_file):
    """Parse meta.dat and return arrays: i, j (int), cx, cy (float).
    Expected format per line: w1_I_J.out cx cy rk1 rk2
    """
    import re
    rows = []
    with open(meta_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            m = re.search(r'_(\d+)_(\d+)\.', parts[0])
            if not m:
                continue
            i, j = int(m.group(1)), int(m.group(2))
            cx, cy = float(parts[1]), float(parts[2])
            rows.append((i, j, cx, cy))
    return rows


def nearest_window(cx, cy, meta_rows):
    """Return (i, j) of the meta.dat entry closest to (cx, cy)."""
    best_dist = np.inf
    best_ij = (0, 0)
    for i, j, mcx, mcy in meta_rows:
        d = (cx - mcx) ** 2 + (cy - mcy) ** 2
        if d < best_dist:
            best_dist = d
            best_ij = (i, j)
    return best_ij


def find_mfep(Z, criterion="minsum"):
    """DP path monotonic in x1 that optimises F along the path.

    criterion='minsum'  — minimise sum of F (follows valley floors and minima)
    criterion='minimax' — minimise the maximum F crossed (lowest saddle)

    Returns list of iy-indices (one per x1 column).
    """
    ny, nx = Z.shape
    INF = np.inf

    best = np.where(np.isfinite(Z[:, 0]), Z[:, 0], INF)
    back = np.full((nx, ny), -1, dtype=int)

    for ix in range(1, nx):
        new_best = np.full(ny, INF)
        for iy in range(ny):
            if not np.isfinite(Z[iy, ix]):
                continue
            f_here = Z[iy, ix]
            for diy in (-1, 0, 1):
                iy_prev = iy + diy
                if 0 <= iy_prev < ny and best[iy_prev] < INF:
                    cost = max(best[iy_prev], f_here) if criterion == "minimax" \
                           else best[iy_prev] + f_here
                    if cost < new_best[iy]:
                        new_best[iy] = cost
                        back[ix, iy] = iy_prev
        best = new_best

    iy_end = int(np.argmin(best))
    if best[iy_end] == INF:
        raise ValueError("No valid path found across the free energy surface.")

    path_iy = [iy_end]
    for ix in range(nx - 1, 0, -1):
        iy_end = back[ix, iy_end]
        path_iy.append(iy_end)
    path_iy.reverse()
    return path_iy


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
                        help="Archivo con los valores medios (window mean_c1 std_c1 mean_c2 std_c2) "
                             "para dibujar la trayectoria 1D sobre el mapa 2D")
    parser.add_argument("--mfep", action="store_true",
                        help="Compute and overlay the minimum free energy path on the 2D map")
    parser.add_argument("--mfep-criterion", default="minsum", choices=["minsum", "minimax"],
                        help="MFEP optimisation criterion: minsum (default) follows valley floors; "
                             "minimax finds the lowest saddle crossing")
    parser.add_argument("--save-path", default=None,
                        help="Save MFEP path to a text file. "
                             "Columns: x1 x2 F. If --meta is given, prepends i j window indices.")
    parser.add_argument("--meta", default=None,
                        help="meta.dat file (wham2d format: w1_i_j.out cx cy rk1 rk2). "
                             "Used to map MFEP coordinates to the nearest window (i, j).")
    args = parser.parse_args()

    filepath = os.path.join(args.path, args.file)
    if not os.path.isfile(filepath):
        print(f"❌ No se encontró el archivo: {filepath}")
        sys.exit(1)

    x_unique, y_unique, Z = read_wham2d(filepath)
    X, Y = np.meshgrid(x_unique, y_unique)

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

    # --- MFEP overlay ---
    if args.mfep:
        path_iy = find_mfep(Z, criterion=args.mfep_criterion)
        path_x = x_unique
        path_y = np.array([y_unique[iy] for iy in path_iy])
        path_F = np.array([Z[iy, ix] for ix, iy in enumerate(path_iy)])

        if args.save_path:
            if args.meta:
                meta_rows = read_meta(args.meta)
                ij = np.array([nearest_window(x, y, meta_rows)
                               for x, y in zip(path_x, path_y)], dtype=int)
                data_out = np.column_stack([ij, path_x, path_y, path_F])
                header = "i  j  x1  x2  F_kcal_mol"
                fmt = ["%d", "%d", "%.6f", "%.6f", "%.6f"]
            else:
                data_out = np.column_stack([path_x, path_y, path_F])
                header = "x1  x2  F_kcal_mol"
                fmt = "%.6f"
            np.savetxt(args.save_path, data_out, header=header, fmt=fmt)
            print(f"Path saved: {args.save_path}")

        plt.figure(1)
        plt.plot(path_x, path_y, 'w-', lw=2, label="MFEP")
        plt.scatter(path_x, path_y, c='white', s=20, zorder=5)

        plt.figure(2)
        plt.plot(path_x, path_F, 'o-', color='gray', lw=2, label="MFEP")

    # --- meansfile trajectories ---
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

    if plt.fignum_exists(1) and (args.mfep or args.meansfile):
        plt.figure(1)
        plt.legend(fontsize=13)

    if plt.fignum_exists(2):
        plt.figure(2)
        plt.xlabel("Reaction coordinate x$_1$ (Å)")
        plt.ylabel("Free energy (kcal/mol)")
        plt.title("1D free energy profile")
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
