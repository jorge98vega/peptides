#!/usr/bin/env python3
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import argparse


def read_wham2d(filepath):
    data = np.loadtxt(filepath)
    if data.shape[1] < 3:
        print("Error: WHAM2D file must have at least 3 columns (x, y, F).")
        sys.exit(1)
    x = data[:, 0]
    y = data[:, 1]
    F = data[:, 2]
    x_unique = np.unique(x)
    y_unique = np.unique(y)
    nx, ny = len(x_unique), len(y_unique)
    if nx * ny != len(F):
        print("Warning: data does not form a regular grid.")
        sys.exit(1)
    Z = F.reshape((nx, ny)).T   # Z[iy, ix]
    Z[Z > 1e6] = np.nan
    Z -= np.nanmin(Z)
    return x_unique, y_unique, Z


def read_meta(meta_file):
    """Parse meta.dat → list of (i, j, cx, cy)."""
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


def make_map_figure(x_unique, y_unique, fig_width):
    """Create figure + axes for the 2D map.

    Figure height is computed so the axes region has the same physical aspect
    ratio as the data (equal Angstrom per inch on both axes). make_axes_locatable
    keeps the colorbar flush with the axes regardless of aspect ratio.
    """
    x_range = x_unique[-1] - x_unique[0]
    y_range = y_unique[-1] - y_unique[0]
    data_aspect = y_range / x_range if x_range > 0 else 1.0

    # Map panel width is ~72% of total figure width (rest: colorbar + margins)
    map_panel_w = fig_width * 0.72
    map_panel_h = map_panel_w * data_aspect
    # Add fixed vertical space for title + x-label + ticks
    fig_height = map_panel_h + 1.1

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    return fig, ax


def main():
    parser = argparse.ArgumentParser(
        description="Plot 2D free energy surface from WHAM2D output")
    parser.add_argument("--path", type=str, required=True,
                        help="Directory containing the WHAM2D output file")
    parser.add_argument("--file", type=str, default="wham2d.out",
                        help="WHAM2D output filename (default: wham2d.out)")
    parser.add_argument("--zlim", type=float, nargs=2, default=None,
                        help="Free energy color scale limits (e.g. --zlim 0 10)")
    parser.add_argument("--save", type=str, default=None,
                        help="Save 2D map to this path; 1D profile gets _1d suffix")
    parser.add_argument("--meansfile", type=str, nargs="+", default=None,
                        help="Window means files (w mean1 std1 mean2 std2) to overlay")
    parser.add_argument("--mfep", action="store_true",
                        help="Compute and overlay the minimum free energy path")
    parser.add_argument("--mfep-criterion", default="minsum",
                        choices=["minsum", "minimax"],
                        help="MFEP criterion: minsum (default) or minimax")
    parser.add_argument("--save-path", default=None,
                        help="Save MFEP path to text file (x1 x2 F; "
                             "prepends i j if --meta is given)")
    parser.add_argument("--meta", default=None,
                        help="meta.dat (w1_i_j.out cx cy rk1 rk2) "
                             "to map MFEP coordinates to window indices")
    # --- Presentation figure controls ---
    parser.add_argument("--fig-width", type=float, default=7.0,
                        help="Total figure width in inches (default: 7). "
                             "Height is computed from the data aspect ratio.")
    parser.add_argument("--dpi", type=int, default=300,
                        help="Resolution when saving (default: 300)")
    parser.add_argument("--fontsize", type=int, default=14,
                        help="Base font size; labels and title scale from this (default: 14)")
    parser.add_argument("--xlabel", type=str,
                        default="Reaction coordinate x$_1$ (Å)",
                        help="X-axis label")
    parser.add_argument("--ylabel", type=str,
                        default="Reaction coordinate x$_2$ (Å)",
                        help="Y-axis label")
    parser.add_argument("--title", type=str, default="Free energy surface",
                        help="Figure title; pass empty string '' to suppress")
    parser.add_argument("--title-1d", type=str, default="Free energy 1D profile",
                        help="Title for the 1D profile figure; pass empty string '' to suppress")
    parser.add_argument("--labels", type=str, nargs="+", default=None,
                        help="Legend labels for --meansfile curves, one per file "
                             "(default: 'Trajectory N')")
    parser.add_argument("--no-legend", action="store_false", dest="legend",
                        help="Hide the legend on all figures")
    # --- Contours ---
    parser.add_argument("--contours", type=int, default=0,
                        help="Number of isoenergy contour lines (default: 0 = off)")
    parser.add_argument("--contour-smooth", type=float, default=1.0,
                        help="Gaussian smoothing sigma for contours (default: 1.0; 0 = none)")
    parser.add_argument("--contour-color", type=str, default="white",
                        help="Contour line color (default: white)")
    parser.add_argument("--contour-lw", type=float, default=0.9,
                        help="Contour line width (default: 0.9)")
    parser.add_argument("--contour-alpha", type=float, default=0.7,
                        help="Contour line opacity (default: 0.7)")
    args = parser.parse_args()

    fs   = args.fontsize
    fs_l = int(round(fs * 1.15))   # axis labels
    fs_t = int(round(fs * 1.30))   # title
    fs_c = int(round(fs * 0.90))   # colorbar / tick labels

    filepath = os.path.join(args.path, args.file)
    if not os.path.isfile(filepath):
        print(f"Error: file not found: {filepath}")
        sys.exit(1)

    x_unique, y_unique, Z = read_wham2d(filepath)
    X, Y = np.meshgrid(x_unique, y_unique)

    cmap = plt.get_cmap("turbo").copy()
    cmap.set_bad(alpha=0)

    # --- Figure 1: 2D map ---
    fig1, ax1 = make_map_figure(x_unique, y_unique, args.fig_width)

    pm = ax1.pcolormesh(X, Y, Z, shading='auto', cmap=cmap)
    ax1.set_aspect('equal')

    # Colorbar flush with axes height (make_axes_locatable handles equal-aspect correctly)
    divider = make_axes_locatable(ax1)
    cax = divider.append_axes("right", size="5%", pad=0.18)
    cbar = fig1.colorbar(pm, cax=cax)
    cbar.set_label("Free energy (kcal/mol)", size=fs_l)

    if args.zlim:
        pm.set_clim(args.zlim)

    ax1.set_xlabel(args.xlabel, fontsize=fs_l)
    ax1.set_ylabel(args.ylabel, fontsize=fs_l)
    if args.title:
        ax1.set_title(args.title, fontsize=fs_t, pad=10)

    # Ticks on all four sides; labels only on left/bottom
    ax1.tick_params(axis='both', which='both',
                    top=True, right=True,
                    labeltop=False, labelright=False,
                    width=1.5, length=5, labelsize=fs_c)
    # Thicker frame
    for spine in ax1.spines.values():
        spine.set_linewidth(1.5)

    cbar.outline.set_linewidth(1.5)
    cbar.ax.tick_params(width=1.5, length=4, labelsize=fs_c)

    # --- Isoenergy contours ---
    if args.contours > 0:
        Z_draw = Z.copy()
        if args.contour_smooth > 0:
            from scipy.ndimage import gaussian_filter
            mask   = np.isfinite(Z_draw)
            vsum   = gaussian_filter(np.where(mask, Z_draw, 0.0), args.contour_smooth)
            wsum   = gaussian_filter(mask.astype(float), args.contour_smooth)
            Z_draw = np.where(mask, vsum / np.where(wsum > 0, wsum, 1.0), np.nan)
        # Extend grid by half a cell on each side so contours reach the plot edge
        # (pcolormesh already extends that far; contour stops at the last data point)
        dx = np.mean(np.diff(x_unique))
        dy = np.mean(np.diff(y_unique))
        x_ext = np.r_[x_unique[0] - dx/2, x_unique, x_unique[-1] + dx/2]
        y_ext = np.r_[y_unique[0] - dy/2, y_unique, y_unique[-1] + dy/2]
        X_ext, Y_ext = np.meshgrid(x_ext, y_ext)
        # Linear extrapolation at each edge so isolines continue in the same direction
        ny_d, nx_d = Z_draw.shape
        Z_ext = np.empty((ny_d + 2, nx_d + 2))
        Z_ext[1:-1, 1:-1] = Z_draw
        Z_ext[1:-1,  0]   = 2*Z_draw[:,  0] - Z_draw[:,  1]
        Z_ext[1:-1, -1]   = 2*Z_draw[:, -1] - Z_draw[:, -2]
        Z_ext[0,  1:-1]   = 2*Z_draw[ 0, :] - Z_draw[ 1, :]
        Z_ext[-1, 1:-1]   = 2*Z_draw[-1, :] - Z_draw[-2, :]
        Z_ext[ 0,  0]     = (Z_ext[ 0, 1] + Z_ext[ 1,  0]) / 2
        Z_ext[ 0, -1]     = (Z_ext[ 0,-2] + Z_ext[ 1, -1]) / 2
        Z_ext[-1,  0]     = (Z_ext[-2, 0] + Z_ext[-1,  1]) / 2
        Z_ext[-1, -1]     = (Z_ext[-2,-1] + Z_ext[-1, -2]) / 2
        ax1.contour(X_ext, Y_ext, Z_ext, levels=args.contours,
                    colors=args.contour_color, linewidths=args.contour_lw,
                    alpha=args.contour_alpha)

    # --- MFEP: compute path data ---
    path_x = path_y = path_F = None
    if args.mfep:
        path_iy = find_mfep(Z, criterion=args.mfep_criterion)
        path_x  = x_unique
        path_y  = np.array([y_unique[iy] for iy in path_iy])
        path_F  = np.array([Z[iy, ix] for ix, iy in enumerate(path_iy)])

        if args.save_path:
            if args.meta:
                meta_rows = read_meta(args.meta)
                ij = np.array([nearest_window(x, y, meta_rows)
                               for x, y in zip(path_x, path_y)], dtype=int)
                data_out = np.column_stack([ij, path_x, path_y, path_F])
                header   = "i  j  x1  x2  F_kcal_mol"
                fmt      = ["%d", "%d", "%.6f", "%.6f", "%.6f"]
            else:
                data_out = np.column_stack([path_x, path_y, path_F])
                header   = "x1  x2  F_kcal_mol"
                fmt      = "%.6f"
            np.savetxt(args.save_path, data_out, header=header, fmt=fmt)
            print(f"Path saved: {args.save_path}")

        ax1.plot(path_x, path_y, 'w-', lw=2, label="MFEP")
        ax1.scatter(path_x, path_y, c='white', s=20, zorder=5)

    # --- Figure 2: 1D profile (created lazily when needed) ---
    fig2, ax2 = None, None

    def get_ax2():
        nonlocal fig2, ax2
        if ax2 is None:
            fig2, ax2 = plt.subplots(figsize=(7, 5))
        return ax2

    if args.mfep:
        get_ax2().plot(path_x, path_F, 'o-', color='gray', lw=2, label="MFEP")

    # --- meansfile trajectories ---
    if args.meansfile:
        from scipy.spatial import cKDTree

        colors     = ["skyblue", "orange", "lightgreen", "violet"]
        valid_mask = np.isfinite(Z.ravel()) & (Z.ravel() < 1e6)
        coords_valid = np.column_stack([X.ravel()[valid_mask], Y.ravel()[valid_mask]])
        F_valid    = Z.ravel()[valid_mask]
        tree       = cKDTree(coords_valid) if len(coords_valid) > 0 else None

        for idx, means_file in enumerate(args.meansfile):
            if not os.path.isfile(means_file):
                print(f"Warning: file not found: {means_file}")
                continue

            means = np.loadtxt(means_file)
            if means.shape[1] < 5:
                print(f"Warning: {means_file} needs 5 columns.")
                continue

            color   = colors[idx % len(colors)]
            mean_c1 = means[:, 1]
            mean_c2 = means[:, 3]

            label = (args.labels[idx] if args.labels and idx < len(args.labels)
                     else f"Trajectory {idx+1}")
            ax1.plot(mean_c1, mean_c2, color=color, lw=1.5, label=label)
            ax1.scatter(mean_c1, mean_c2, color=color, s=20, zorder=3)

            if tree is not None:
                F_path = []
                for x_val, y_val in zip(mean_c1, mean_c2):
                    dist, i_near = tree.query([x_val, y_val])
                    F_path.append(F_valid[i_near] if dist <= 0.15 else np.nan)

                F_path    = np.array(F_path)
                valid_idx = np.isfinite(F_path)
                if np.any(valid_idx):
                    get_ax2().plot(mean_c1[valid_idx], F_path[valid_idx], '-o',
                                   color=color, label=label)

            print(f"Added trajectory {idx+1} from {means_file}")

    # --- Legend for 2D map ---
    if args.legend and (args.mfep or args.meansfile):
        ax1.legend(fontsize=fs_c)

    # --- Finish 1D profile figure ---
    if ax2 is not None:
        ax2.set_xlabel(args.xlabel, fontsize=fs_l)
        ax2.set_ylabel("Free energy (kcal/mol)", fontsize=fs_l)
        if args.title_1d:
            ax2.set_title(args.title_1d, fontsize=fs_t, pad=10)
        ax2.tick_params(axis='both', which='both',
                        top=True, right=True,
                        labeltop=False, labelright=False,
                        width=1.5, length=5, labelsize=fs_c)
        for spine in ax2.spines.values():
            spine.set_linewidth(1.5)
        ax2.grid(True, alpha=0.3)
        if args.legend:
            ax2.legend(fontsize=fs_c)
        fig2.tight_layout(pad=1.5)

    fig1.tight_layout(pad=1.5)

    if args.save:
        fig1.savefig(args.save, dpi=args.dpi, bbox_inches='tight')
        print(f"Saved: {args.save}")
        if fig2 is not None:
            base, ext = os.path.splitext(args.save)
            save2 = f"{base}_1d{ext}"
            fig2.savefig(save2, dpi=args.dpi, bbox_inches='tight')
            print(f"Saved: {save2}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
