with open("salida.out") as f, open("first_windows.dat", "w") as out:
    for i, line in enumerate(f, 1):
        if line.strip().endswith(")"):
            x = line.split()[-1][:-1]  # extrae número antes de ')'
            out.write(f"{i} {x}\n")

