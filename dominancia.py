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
    dominado = False
    for x in range(len(a)):
        if dominancia(a[x], arreglo):
            dominado = True

    if not dominado:
        x = 0
        while x < len(a):
            if dominancia(arreglo, a[x]):
                a.pop(x)
            else:
                x += 1
        a.append(list(arreglo))



if __name__ == "__main__":
    print("Prueba de dominancia")
    archivo = []
    todos = []
    for x in range(100000):
        tempsol = [random.random(), random.random()]
        todos.append(tempsol)
        agrega(archivo, tempsol)

    for x in range(len(archivo)):
        print(archivo[x][0], archivo[x][1])

    archivo.sort(key=lambda p: p[0])

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(
        [p[0] for p in todos], [p[1] for p in todos],
        s=4, alpha=0.15, color="#94a3b8", linewidths=0, label="Soluciones generadas",
    )
    ax.plot(
        [p[0] for p in archivo], [p[1] for p in archivo],
        color="#2563eb", linewidth=1.5, marker="o", markersize=5,
        label="Frente no dominado",
    )
    ax.set_xlabel("Objetivo 1")
    ax.set_ylabel("Objetivo 2")
    ax.set_title("Prueba de dominancia")
    ax.grid(True, alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig("dominancia.png", dpi=150)
    plt.show()