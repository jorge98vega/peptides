#!/usr/bin/env python3
import sys
import re
import numpy as np
import matplotlib.pyplot as plt


def parse_expression(expr, data):
    """
    Evaluate a column expression such as '2', '3+5', '(3+4)/2'.
    Numbers are substituted by data[:, n-1].
    """
    expr_py = re.sub(r'\b(\d+)\b', r'data[:, \1 - 1]', expr)
    try:
        return eval(expr_py)
    except Exception as e:
        print(f"Error evaluating '{expr}': {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("Usage: plot_rst.py <file> <col|expr> [<col|expr> ...]")
        print("Examples:")
        print("  plot_rst.py data.txt 2")
        print("  plot_rst.py data.txt 2 3")
        print("  plot_rst.py data.txt 3+5 (3+4)/2")
        sys.exit(1)

    filepath    = sys.argv[1]
    expressions = sys.argv[2:]

    data = np.loadtxt(filepath)
    x    = np.arange(len(data))

    plt.figure(figsize=(8, 5))
    for expr in expressions:
        plt.plot(x, parse_expression(expr, data), label=expr)

    plt.xlabel("Index")
    plt.ylabel("Value")
    plt.title(f"{filepath}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
