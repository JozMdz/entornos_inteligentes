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


def schaffer2(x1, x2):
    f1 = x1 ** 2 + x2 ** 2
    f2 = (x1 - 2) ** 2 + (x2 - 2) ** 2
    return f1, f2


def fast_nondominated_sort(poblacion):
    # poblacion: lista de soluciones [f1, f2, ...extra]
    # devuelve una lista de frentes, cada frente es una lista de indices
    n = len(poblacion)
    dominados_por = [[] for _ in range(n)]  # Sp: a quienes domina p
    contador_dominacion = [0] * n           # np: cuantos dominan a p

    frentes = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominancia(poblacion[p][:2], poblacion[q][:2]):
                dominados_por[p].append(q)
            elif dominancia(poblacion[q][:2], poblacion[p][:2]):
                contador_dominacion[p] += 1

        if contador_dominacion[p] == 0:
            frentes[0].append(p)

    i = 0
    while len(frentes[i]) > 0:
        siguiente_frente = []
        for p in frentes[i]:
            for q in dominados_por[p]:
                contador_dominacion[q] -= 1
                if contador_dominacion[q] == 0:
                    siguiente_frente.append(q)
        i += 1
        frentes.append(siguiente_frente)

    frentes.pop()  # el ultimo frente queda vacio
    return frentes


if __name__ == "__main__":
    print("Fast non-dominated sort - funcion de Schaffer (2 variables)")

    poblacion = []
    for _ in range(150):
        x1 = random.uniform(-4, 4)
        x2 = random.uniform(-4, 4)
        f1, f2 = schaffer2(x1, x2)
        poblacion.append([f1, f2, x1, x2])

    frentes = fast_nondominated_sort(poblacion)

    for i in range(len(frentes)):
        print(f"F{i + 1}: {len(frentes[i])} soluciones")
        for idx in frentes[i]:
            sol = poblacion[idx]
            print(f"  f1={sol[0]:.4f}  f2={sol[1]:.4f}  x1={sol[2]:.4f}  x2={sol[3]:.4f}")

    colores = plt.cm.viridis([i / max(1, len(frentes) - 1) for i in range(len(frentes))])
    max_leyenda = 8  # solo se etiquetan los primeros frentes para no saturar la leyenda

    fig, ax = plt.subplots(figsize=(8.5, 7))

    for i in range(len(frentes)):
        puntos = [poblacion[idx] for idx in frentes[i]]
        puntos.sort(key=lambda p: p[0])
        etiqueta = f"F{i + 1}" if i < max_leyenda else None
        ax.plot(
            [p[0] for p in puntos], [p[1] for p in puntos],
            color=colores[i], linewidth=1.2, marker="o", markersize=4,
            label=etiqueta,
        )

    ax.set_xlabel("f1(x1,x2) = x1^2 + x2^2")
    ax.set_ylabel("f2(x1,x2) = (x1-2)^2 + (x2-2)^2")
    ax.set_title(f"Frentes de no dominancia - Schaffer 2 variables ({len(frentes)} frentes)")
    ax.grid(True, alpha=0.2)
    ax.legend(frameon=False, ncol=2, fontsize=7, title=f"Primeros {max_leyenda} frentes")
    fig.tight_layout()
    fig.savefig("frentes_schaffer_2var.png", dpi=150)
    plt.show()
