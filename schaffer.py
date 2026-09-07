import random
import matplotlib.pyplot as plt


def dominancia(a, b):
    bandera = 0
    i = 0
    while i < len(a) and a[i] <= b[i]:
        if a[i] < b[i]:  # minimizar
            bandera = 1  # mejor en algun objetivo
        i += 1

    if bandera == 1 and i >= len(a):  # aqui se cumple porque i termina en i=len(a)
        return True
    else:
        return False  # compare


def agrega(a, arreglo):
    # los dos primeros valores (f1, f2) son los objetivos que se comparan;
    # el resto (x) es informacion extra que solo viaja pegada
    dominado = False
    for x in range(len(a)):
        if dominancia(a[x][:2], arreglo[:2]):
            dominado = True

    if not dominado:
        x = 0
        while x < len(a):
            if dominancia(arreglo[:2], a[x][:2]):
                a.pop(x)
            else:
                x += 1
        a.append(list(arreglo))


def schaffer(x):
    f1 = x ** 2
    f2 = (x - 2) ** 2
    return f1, f2


if __name__ == "__main__":
    print("Prueba de dominancia - funcion de Schaffer")
    archivo = []
    todos = []
    for _ in range(100000):
        x = random.uniform(-1000, 1000)
        f1, f2 = schaffer(x)
        tempsol = [f1, f2, x]
        todos.append(tempsol)
        agrega(archivo, tempsol)

    for sol in archivo:
        print(f"f1={sol[0]:.4f}  f2={sol[1]:.4f}  x={sol[2]:.4f}")

    archivo.sort(key=lambda p: p[0])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

    for ax in (ax1, ax2):
        ax.scatter(
            [p[0] for p in todos], [p[1] for p in todos],
            s=4, alpha=0.15, color="#94a3b8", linewidths=0, label="Soluciones generadas",
        )
        ax.plot(
            [p[0] for p in archivo], [p[1] for p in archivo],
            color="#2563eb", linewidth=1.5, marker="o", markersize=5,
            label="Frente no dominado",
        )
        ax.set_xlabel("f1(x) = x^2")
        ax.set_ylabel("f2(x) = (x-2)^2")
        ax.grid(True, alpha=0.2)

    ax1.set_title("Vista completa (x entre -1000 y 1000)")
    ax1.legend(frameon=False)

    ax2.set_xlim(-0.3, 4.3)
    ax2.set_ylim(-0.3, 4.3)
    for sol in archivo[::max(1, len(archivo) // 8)]:
        ax2.annotate(f"x={sol[2]:.2f}", (sol[0], sol[1]),
                     textcoords="offset points", xytext=(6, 6), fontsize=8, color="#1e3a8a")
    ax2.set_title("Frente (donde vive x en [0, 2])")

    fig.suptitle("Prueba de dominancia - Schaffer")
    fig.tight_layout()
    fig.savefig("schaffer.png", dpi=150)
    plt.show()
