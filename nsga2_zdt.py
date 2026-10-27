import math
import os
import random
import matplotlib.pyplot as plt

from hypervolume import leb_measure


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


# Funciones de prueba ZDT (Zitzler, Deb y Thiele 1999)
# todas son f1(x1) y f2 = g(x2..xm) * h(f1, g)   (ecuacion 6)

def zdt1(x):
    # ecuacion 7: frente convexo
    f1 = x[0]
    g = 1 + 9 * sum(x[1:]) / (len(x) - 1)
    h = 1 - math.sqrt(f1 / g)
    return f1, g * h


def zdt2(x):
    # ecuacion 8: frente no convexo
    f1 = x[0]
    g = 1 + 9 * sum(x[1:]) / (len(x) - 1)
    h = 1 - (f1 / g) ** 2
    return f1, g * h


def zdt3(x):
    # ecuacion 9: frente discontinuo (en pedazos)
    f1 = x[0]
    g = 1 + 9 * sum(x[1:]) / (len(x) - 1)
    h = 1 - math.sqrt(f1 / g) - (f1 / g) * math.sin(10 * math.pi * f1)
    return f1, g * h


def zdt4(x):
    # ecuacion 10: multimodal, 21^9 frentes locales
    f1 = x[0]
    g = 1 + 10 * (len(x) - 1)
    for xi in x[1:]:
        g += xi ** 2 - 10 * math.cos(4 * math.pi * xi)
    h = 1 - math.sqrt(f1 / g)
    return f1, g * h


def zdt6(x):
    # ecuacion 12: frente no convexo y soluciones no uniformes
    f1 = 1 - math.exp(-4 * x[0]) * math.sin(6 * math.pi * x[0]) ** 6
    g = 1 + 9 * (sum(x[1:]) / (len(x) - 1)) ** 0.25
    h = 1 - (f1 / g) ** 2
    return f1, g * h


# nombre: (funcion, numero de variables m, limites de cada variable)
PROBLEMAS = {
    "ZDT1": (zdt1, 30, [(0, 1)] * 30),
    "ZDT2": (zdt2, 30, [(0, 1)] * 30),
    "ZDT3": (zdt3, 30, [(0, 1)] * 30),
    "ZDT4": (zdt4, 10, [(0, 1)] + [(-5, 5)] * 9),
    "ZDT6": (zdt6, 10, [(0, 1)] * 10),
}


def fast_nondominated_sort(poblacion):
    # poblacion: lista de soluciones [f1, f2, x1, ..., xm]
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


VALOR_GRANDE = 999999  # sustituye al infinito para los puntos frontera


def crowding_distance(frente, poblacion, num_objetivos=2):
    # frente: lista de indices de un mismo frente
    # devuelve un diccionario {indice: distancia}, sin normalizar
    l = len(frente)
    distancia = {idx: 0 for idx in frente}

    for m in range(num_objetivos):
        ordenado = sorted(frente, key=lambda idx: poblacion[idx][m])

        distancia[ordenado[0]] = VALOR_GRANDE   # puntos frontera siempre seleccionados
        distancia[ordenado[-1]] = VALOR_GRANDE

        for i in range(1, l - 1):
            distancia[ordenado[i]] += poblacion[ordenado[i + 1]][m] - poblacion[ordenado[i - 1]][m]

    return distancia


# NSGA-II

N = 100                # tamaño de la poblacion (como en el articulo)
GENERACIONES = 250
ALFA = 0.5             # que tanto se estira el rango de los padres en la cruza
M_REF = [1.1, 1.1]     # punto de referencia para el hypervolume
SEMILLA = 1            # misma semilla = mismos resultados en cada corrida


def evaluar(x, funcion):
    # arma la solucion [f1, f2, x1, ..., xm]
    f1, f2 = funcion(x)
    return [f1, f2] + x


def genera_poblacion(n, funcion, limites):
    poblacion = []
    for _ in range(n):
        x = [random.uniform(a, b) for (a, b) in limites]
        poblacion.append(evaluar(x, funcion))
    return poblacion


def comparacion_crowded(a, b, rango, distancia):
    # operador <n: ¿a es mejor que b?
    # gana el de menor frente; si estan en el mismo frente, gana el de mayor distancia
    if rango[a] < rango[b]:
        return True
    if rango[a] == rango[b] and distancia[a] > distancia[b]:
        return True
    return False


def torneo(P, rango, distancia):
    # torneo binario: se toman dos al azar y se queda el mejor segun <n
    a = random.randrange(len(P))
    b = random.randrange(len(P))
    if comparacion_crowded(a, b, rango, distancia):
        return P[a]
    else:
        return P[b]


def cruza_blx(p1, p2):
    # p1, p2: valor de UNA variable de cada padre (se llama una vez por variable)
    minimo = min(p1, p2)
    maximo = max(p1, p2)
    rango = maximo - minimo                          # range_i = max_i - min_i
    beta1 = minimo - rango * ALFA                    # B1 = min_i - range_i * alfa
    beta2 = maximo + rango * ALFA                    # B2 = max_i + range_i * alfa
    y1 = beta1 + random.random() * (beta2 - beta1)   # y1 = B1 + rand(B2 - B1)
    y2 = beta1 + random.random() * (beta2 - beta1)   # y2 = B1 + rand(B2 - B1), con otro rand
    return y1, y2


def mutacion(x, limites):
    # mutacion uniforme: cada variable se cambia con probabilidad 1/m por un valor al azar de su dominio
    prob = 1 / len(x)
    nuevo = []
    for i in range(len(x)):
        if random.random() < prob:
            nuevo.append(random.uniform(limites[i][0], limites[i][1]))
        else:
            nuevo.append(x[i])
    return nuevo


def recortar(x, limites):
    # si la cruza BLX saca a una variable de su dominio, aqui se regresa al limite
    return [max(limites[i][0], min(limites[i][1], x[i])) for i in range(len(x))]


def make_new_pop(P, rango, distancia, funcion, limites):
    # seleccion, cruza y mutacion para crear Q(t+1) a partir de P
    Q = []
    while len(Q) < N:
        padre1 = torneo(P, rango, distancia)
        padre2 = torneo(P, rango, distancia)
        hijo1 = []
        hijo2 = []
        for i in range(len(limites)):                        # BLX variable por variable
            y1, y2 = cruza_blx(padre1[2 + i], padre2[2 + i])
            hijo1.append(y1)
            hijo2.append(y2)
        Q.append(evaluar(recortar(mutacion(hijo1, limites), limites), funcion))
        if len(Q) < N:
            Q.append(evaluar(recortar(mutacion(hijo2, limites), limites), funcion))
    return Q


def siguiente_poblacion(P, Q):
    R = P + Q                                   # Rt = Pt U Qt
    frentes = fast_nondominated_sort(R)         # F = fast-non-dominated-sort(Rt)

    P_nueva = []                                # Pt+1 = vacio
    rango = []                                  # en que frente quedo cada uno (para el torneo)
    distancia_nueva = []                        # su crowding distance (para el torneo)
    i = 0                                       # i = 1 (aqui empieza en 0)
    while i < len(frentes) and len(P_nueva) + len(frentes[i]) <= N:   # until |Pt+1| + |Fi| <= N
        distancia = crowding_distance(frentes[i], R)                   # crowding-distance-assignment(Fi)
        for idx in frentes[i]:                                         # Pt+1 = Pt+1 U Fi
            P_nueva.append(R[idx])
            rango.append(i)
            distancia_nueva.append(distancia[idx])
        i += 1                                                         # i = i + 1

    if len(P_nueva) < N:
        distancia = crowding_distance(frentes[i], R)
        ordenado = sorted(frentes[i], key=lambda idx: distancia[idx], reverse=True)   # Sort(Fi, <n)
        faltan = N - len(P_nueva)
        for idx in ordenado[:faltan]:                                                 # Fi[1 : (N - |Pt+1|)]
            P_nueva.append(R[idx])
            rango.append(i)
            distancia_nueva.append(distancia[idx])

    return P_nueva, rango, distancia_nueva


def nsga2(funcion, limites):
    P = genera_poblacion(N, funcion, limites)          # P0 aleatoria
    P, rango, distancia = siguiente_poblacion(P, [])   # P0 tambien se separa en frentes para el primer torneo
    Q = make_new_pop(P, rango, distancia, funcion, limites)      # Q0 = make-new-pop(P0)

    for t in range(GENERACIONES):
        P, rango, distancia = siguiente_poblacion(P, Q)
        Q = make_new_pop(P, rango, distancia, funcion, limites)  # Qt+1 = make-new-pop(Pt+1)
    return P


def frente_optimo(nombre, puntos=500):
    # el frente verdadero sale con g = 1: f2 = h(f1, 1)
    frente = []
    for k in range(puntos):
        if nombre == "ZDT6":
            f1 = 0.2807753191 + (1 - 0.2807753191) * k / (puntos - 1)   # en ZDT6 f1 no baja de 0.28
        else:
            f1 = k / (puntos - 1)
        if nombre in ("ZDT1", "ZDT4"):
            f2 = 1 - math.sqrt(f1)
        elif nombre in ("ZDT2", "ZDT6"):
            f2 = 1 - f1 ** 2
        else:  # ZDT3
            f2 = 1 - math.sqrt(f1) - f1 * math.sin(10 * math.pi * f1)
        frente.append([f1, f2])

    # en ZDT3 no toda la curva es no dominada: se queda solo con los pedazos que si
    no_dominados = []
    mejor_f2 = float("inf")
    for p in sorted(frente):
        if p[1] < mejor_f2:
            no_dominados.append(p)
            mejor_f2 = p[1]
    return no_dominados


def guardar(nombre, frente):
    # FUN.txt (funciones objetivo) y VAR.txt (variables que las producen), una carpeta por problema
    # una solucion por renglon y en el mismo orden: el renglon 1 de FUN.txt sale del renglon 1 de VAR.txt
    carpeta = f"salidas/{nombre}"
    os.makedirs(carpeta, exist_ok=True)
    with open(f"{carpeta}/FUN.txt", "w") as f:
        for sol in frente:
            f.write(f"{sol[0]} {sol[1]}\n")   # precision completa, sin redondear
    with open(f"{carpeta}/VAR.txt", "w") as f:
        for sol in frente:
            f.write(" ".join(f"{v}" for v in sol[2:]) + "\n")   # sin redondear: en ZDT6 6 decimales ya cambian f2


if __name__ == "__main__":
    print(f"NSGA-II en ZDT  (N={N}, generaciones={GENERACIONES}, referencia={M_REF}, semilla={SEMILLA})")

    fig, ejes = plt.subplots(2, 3, figsize=(15, 9))
    ejes = ejes.flatten()
    resumen = []

    for k, (nombre, (funcion, m, limites)) in enumerate(PROBLEMAS.items()):
        random.seed(SEMILLA)   # se fija antes de cada funcion, asi cada una se puede repetir sola
        final = nsga2(funcion, limites)

        frentes = fast_nondominated_sort(final)
        F1 = [final[idx] for idx in frentes[0]]
        F1.sort(key=lambda sol: sol[0])
        guardar(nombre, F1)

        optimo = frente_optimo(nombre)
        hv = leb_measure([sol[:2] for sol in F1], M_REF)
        hv_optimo = leb_measure(optimo, M_REF)
        porcentaje = 100 * hv / hv_optimo
        resumen.append((nombre, len(F1), hv, hv_optimo, porcentaje))

        print(f"\n{nombre}: {len(F1)} soluciones en F1")
        print(f"  HV obtenido = {hv:.4f}   HV del frente optimo = {hv_optimo:.4f}   ({porcentaje:.1f}%)")

        ax = ejes[k]
        ax.scatter([p[0] for p in optimo], [p[1] for p in optimo],
                   s=3, color="#94a3b8", label="Frente optimo (g = 1)")
        ax.scatter([s[0] for s in F1], [s[1] for s in F1],
                   s=14, color="#2563eb", label="F1 de NSGA-II")
        ax.scatter([M_REF[0]], [M_REF[1]], marker="s", s=30, color="black", label=f"Referencia {M_REF}")
        ax.set_title(f"{nombre}  -  HV = {hv:.4f} ({porcentaje:.1f}% del optimo)")
        ax.set_xlabel("f1")
        ax.set_ylabel("f2")
        ax.grid(True, alpha=0.2)
        ax.legend(frameon=False, fontsize=8)

    # sexto panel: tabla con la calidad de cada funcion
    ejes[5].axis("off")
    tabla = ejes[5].table(
        cellText=[[n, c, f"{h:.4f}", f"{ho:.4f}", f"{p:.1f}%"] for (n, c, h, ho, p) in resumen],
        colLabels=["Funcion", "|F1|", "HV", "HV optimo", "% del optimo"],
        loc="center",
    )
    tabla.scale(1, 1.6)
    ejes[5].set_title("Calidad (hypervolume)")

    fig.suptitle(f"NSGA-II con BLX-alfa en ZDT  (N={N}, {GENERACIONES} generaciones)")
    fig.tight_layout()
    fig.savefig("nsga2_zdt.png", dpi=150)
    plt.show()
