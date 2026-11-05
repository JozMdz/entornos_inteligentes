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


def signo(v):
    # sign(): 1 si es positivo, -1 si es negativo, 0 si es 0 (Math.signum de jMetal)
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


# Problemas GLT (Gu, Liu y Tan 2012), tabla 1 del articulo como F1 ... F6
# todos son f_i = (1 + g) * alfa_i, y g = 0 en el frente optimo
# se sigue la implementacion de jMetal (glt/GLT1.java ... GLT6.java)

def g_glt(x, desde):
    # g = suma de (x_i - sin(2*pi*x1 + i*pi/n))^2, i empieza en 0 como en jMetal
    # desde = 1 en los de 2 objetivos (x2 ... x10) y 2 en los de 3 objetivos (x3 ... x10)
    n = len(x)
    g = 0
    for i in range(desde, n):
        valor = x[i] - math.sin(2 * math.pi * x[0] + i * math.pi / n)
        g += valor ** 2
    return g


def glt1(x):
    # F1: frente lineal y en pedazos
    g = g_glt(x, 1)
    f1 = (1 + g) * x[0]
    f2 = (1 + g) * (2 - x[0] - signo(math.cos(2 * math.pi * x[0])))
    return f1, f2


def glt2(x):
    # F2: frente convexo, f2 llega hasta 10
    g = g_glt(x, 1)
    f1 = (1 + g) * (1 - math.cos(math.pi * x[0] / 2))
    f2 = (1 + g) * (10 - 10 * math.sin(math.pi * x[0] / 2))
    return f1, f2


def glt3(x):
    # F3: frente convexo con un quiebre (jMetal decide el tramo con f1 < 0.05)
    g = g_glt(x, 1)
    f1 = (1 + g) * x[0]
    if f1 < 0.05:
        f2 = (1 + g) * (1 - 19 * x[0])
    else:
        f2 = (1 + g) * (1 / 19 - x[0] / 19)
    return f1, f2


def glt4(x):
    # F4: frente convexo y en pedazos, f2 llega hasta 2
    g = g_glt(x, 1)
    f1 = (1 + g) * x[0]
    f2 = (1 + g) * (2 - 2 * math.sqrt(x[0]) * math.cos(2 * math.sqrt(x[0]) * math.pi) ** 2)
    return f1, f2


def glt5(x):
    # F5: 3 objetivos, frente convexo
    g = g_glt(x, 2)
    f1 = (1 + g) * (1 - math.cos(x[0] * math.pi / 2)) * (1 - math.cos(x[1] * math.pi / 2))
    f2 = (1 + g) * (1 - math.cos(x[0] * math.pi / 2)) * (1 - math.sin(x[1] * math.pi / 2))
    f3 = (1 + g) * (1 - math.sin(x[0] * math.pi / 2))
    return f1, f2, f3


def glt6(x):
    # F6: 3 objetivos, frente convexo y en pedazos
    g = g_glt(x, 2)
    f1 = (1 + g) * (1 - math.cos(x[0] * math.pi / 2)) * (1 - math.cos(x[1] * math.pi / 2))
    f2 = (1 + g) * (1 - math.cos(x[0] * math.pi / 2)) * (1 - math.sin(x[1] * math.pi / 2))
    f3 = (1 + g) * (2 - math.sin(x[0] * math.pi / 2) - signo(math.cos(4 * x[0] * math.pi)))
    return f1, f2, f3


# nombre: (funcion, numero de objetivos k, limites de cada variable)   n = 10 variables
PROBLEMAS = {
    "GLT1": (glt1, 2, [(0, 1)] + [(-1, 1)] * 9),
    "GLT2": (glt2, 2, [(0, 1)] + [(-1, 1)] * 9),
    "GLT3": (glt3, 2, [(0, 1)] + [(-1, 1)] * 9),
    "GLT4": (glt4, 2, [(0, 1)] + [(-1, 1)] * 9),
    "GLT5": (glt5, 3, [(0, 1)] * 2 + [(-1, 1)] * 8),
    "GLT6": (glt6, 3, [(0, 1)] * 2 + [(-1, 1)] * 8),
}


def fast_nondominated_sort(poblacion, k):
    # poblacion: lista de soluciones [f1, ..., fk, x1, ..., xn]; k = numero de objetivos
    # devuelve una lista de frentes, cada frente es una lista de indices
    n = len(poblacion)
    dominados_por = [[] for _ in range(n)]  # Sp: a quienes domina p
    contador_dominacion = [0] * n           # np: cuantos dominan a p

    frentes = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominancia(poblacion[p][:k], poblacion[q][:k]):
                dominados_por[p].append(q)
            elif dominancia(poblacion[q][:k], poblacion[p][:k]):
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


def crowding_distance(frente, poblacion, num_objetivos):
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

N_POR_OBJETIVOS = {2: 100, 3: 300}   # tamaño de la poblacion (como en el articulo: 100 con 2 objetivos, 300 con 3)
GENERACIONES = 250
ALFA = 0.5             # que tanto se estira el rango de los padres en la cruza
SEMILLA = 1            # misma semilla = mismos resultados en cada corrida


def evaluar(x, funcion):
    # arma la solucion [f1, ..., fk, x1, ..., xn]
    return list(funcion(x)) + x


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
    # mutacion uniforme: cada variable se cambia con probabilidad 1/n por un valor al azar de su dominio
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


def make_new_pop(P, rango, distancia, funcion, limites, k, N):
    # seleccion, cruza y mutacion para crear Q(t+1) a partir de P
    Q = []
    while len(Q) < N:
        padre1 = torneo(P, rango, distancia)
        padre2 = torneo(P, rango, distancia)
        hijo1 = []
        hijo2 = []
        for i in range(len(limites)):                        # BLX variable por variable
            y1, y2 = cruza_blx(padre1[k + i], padre2[k + i])  # las variables empiezan despues de los k objetivos
            hijo1.append(y1)
            hijo2.append(y2)
        Q.append(evaluar(recortar(mutacion(hijo1, limites), limites), funcion))
        if len(Q) < N:
            Q.append(evaluar(recortar(mutacion(hijo2, limites), limites), funcion))
    return Q


def siguiente_poblacion(P, Q, k, N):
    R = P + Q                                   # Rt = Pt U Qt
    frentes = fast_nondominated_sort(R, k)      # F = fast-non-dominated-sort(Rt)

    P_nueva = []                                # Pt+1 = vacio
    rango = []                                  # en que frente quedo cada uno (para el torneo)
    distancia_nueva = []                        # su crowding distance (para el torneo)
    i = 0                                       # i = 1 (aqui empieza en 0)
    while i < len(frentes) and len(P_nueva) + len(frentes[i]) <= N:   # until |Pt+1| + |Fi| <= N
        distancia = crowding_distance(frentes[i], R, k)                # crowding-distance-assignment(Fi)
        for idx in frentes[i]:                                         # Pt+1 = Pt+1 U Fi
            P_nueva.append(R[idx])
            rango.append(i)
            distancia_nueva.append(distancia[idx])
        i += 1                                                         # i = i + 1

    if len(P_nueva) < N:
        distancia = crowding_distance(frentes[i], R, k)
        ordenado = sorted(frentes[i], key=lambda idx: distancia[idx], reverse=True)   # Sort(Fi, <n)
        faltan = N - len(P_nueva)
        for idx in ordenado[:faltan]:                                                 # Fi[1 : (N - |Pt+1|)]
            P_nueva.append(R[idx])
            rango.append(i)
            distancia_nueva.append(distancia[idx])

    return P_nueva, rango, distancia_nueva


def nsga2(funcion, limites, k):
    N = N_POR_OBJETIVOS[k]
    P = genera_poblacion(N, funcion, limites)             # P0 aleatoria
    P, rango, distancia = siguiente_poblacion(P, [], k, N)   # P0 tambien se separa en frentes para el primer torneo
    Q = make_new_pop(P, rango, distancia, funcion, limites, k, N)      # Q0 = make-new-pop(P0)

    for t in range(GENERACIONES):
        P, rango, distancia = siguiente_poblacion(P, Q, k, N)
        Q = make_new_pop(P, rango, distancia, funcion, limites, k, N)  # Qt+1 = make-new-pop(Pt+1)
    return P


def no_dominados(puntos):
    # se queda con los puntos que nadie domina (sirve para 2 o 3 objetivos)
    resultado = []
    for p in puntos:
        if not any(dominancia(q, p) for q in puntos):
            resultado.append(p)
    return resultado


def frente_optimo(funcion, k, limites, puntos_2obj=1000, lado_3obj=20):
    # con 3 objetivos se usa una rejilla de 20 x 20: con mas puntos LebMeasure en 3D tarda minutos
    # el frente verdadero sale con g = 0: cada x_i = sin(2*pi*x1 + i*pi/n)
    # se barre x1 (y x2 en los de 3 objetivos) y se evalua la funcion real
    n = len(limites)
    desde = 1 if k == 2 else 2

    def x_optimo(primeras):
        x = list(primeras)
        for i in range(desde, n):
            x.append(math.sin(2 * math.pi * x[0] + i * math.pi / n))
        return x

    frente = []
    if k == 2:
        for a in range(puntos_2obj):
            frente.append(list(funcion(x_optimo([a / (puntos_2obj - 1)]))))
    else:
        for a in range(lado_3obj):
            for b in range(lado_3obj):
                frente.append(list(funcion(x_optimo([a / (lado_3obj - 1), b / (lado_3obj - 1)]))))

    return no_dominados(frente)   # algunos tramos de la curva quedan dominados (GLT1, GLT4, GLT6)


def punto_referencia(optimo):
    # un poco peor que el peor punto del frente optimo en cada objetivo (10% mas), como el (6, 7) del ejemplo
    k = len(optimo[0])
    return [round(1.1 * max(p[i] for p in optimo), 2) for i in range(k)]


def igd(optimo, obtenido):
    # IGD del articulo: distancia promedio de cada punto del frente optimo al punto mas cercano del obtenido
    total = 0
    for v in optimo:
        total += min(math.dist(v, q) for q in obtenido)
    return total / len(optimo)


def guardar(nombre, frente, k):
    # FUN.txt (funciones objetivo) y VAR.txt (variables que las producen), una carpeta por problema
    # una solucion por renglon y en el mismo orden: el renglon 1 de FUN.txt sale del renglon 1 de VAR.txt
    carpeta = f"salidas/{nombre}"
    os.makedirs(carpeta, exist_ok=True)
    with open(f"{carpeta}/FUN.txt", "w") as f:
        for sol in frente:
            f.write(" ".join(f"{v}" for v in sol[:k]) + "\n")   # precision completa, sin redondear
    with open(f"{carpeta}/VAR.txt", "w") as f:
        for sol in frente:
            f.write(" ".join(f"{v}" for v in sol[k:]) + "\n")


if __name__ == "__main__":
    print(f"NSGA-II en GLT  (N={N_POR_OBJETIVOS}, generaciones={GENERACIONES}, semilla={SEMILLA})")

    fig = plt.figure(figsize=(16, 10))
    resumen = []

    for j, (nombre, (funcion, k, limites)) in enumerate(PROBLEMAS.items()):
        random.seed(SEMILLA)   # se fija antes de cada problema, asi cada uno se puede repetir solo
        final = nsga2(funcion, limites, k)

        frentes = fast_nondominated_sort(final, k)
        F1 = [final[idx] for idx in frentes[0]]
        F1.sort(key=lambda sol: sol[0])
        guardar(nombre, F1, k)

        optimo = frente_optimo(funcion, k, limites)
        M = punto_referencia(optimo)
        hv = leb_measure([sol[:k] for sol in F1], M)
        hv_optimo = leb_measure(optimo, M)
        porcentaje = 100 * hv / hv_optimo
        valor_igd = igd(optimo, [sol[:k] for sol in F1])
        resumen.append((nombre, k, len(F1), M, hv, hv_optimo, porcentaje, valor_igd))

        print(f"\n{nombre} ({k} objetivos): {len(F1)} soluciones en F1, referencia {M}")
        print(f"  HV obtenido = {hv:.4f}   HV del frente optimo = {hv_optimo:.4f}   ({porcentaje:.1f}%)   IGD = {valor_igd:.4f}")

        if k == 2:
            ax = fig.add_subplot(2, 3, j + 1)
            ax.scatter([p[0] for p in optimo], [p[1] for p in optimo],
                       s=3, color="#94a3b8", label="Frente optimo (g = 0)")
            ax.scatter([s[0] for s in F1], [s[1] for s in F1],
                       s=14, color="#2563eb", label="F1 de NSGA-II")
            ax.scatter([M[0]], [M[1]], marker="s", s=30, color="black", label=f"Referencia {M}")
            ax.set_xlabel("f1")
            ax.set_ylabel("f2")
            ax.grid(True, alpha=0.2)
        else:
            ax = fig.add_subplot(2, 3, j + 1, projection="3d")
            ax.scatter([p[0] for p in optimo], [p[1] for p in optimo], [p[2] for p in optimo],
                       s=2, color="#94a3b8", label="Frente optimo (g = 0)")
            ax.scatter([s[0] for s in F1], [s[1] for s in F1], [s[2] for s in F1],
                       s=8, color="#2563eb", label="F1 de NSGA-II")
            ax.set_xlabel("f1")
            ax.set_ylabel("f2")
            ax.set_zlabel("f3")
            ax.view_init(elev=25, azim=45)
        ax.set_title(f"{nombre}  -  HV = {hv:.4f} ({porcentaje:.1f}%)  IGD = {valor_igd:.4f}", fontsize=10)
        ax.legend(frameon=False, fontsize=7)

    fig.suptitle(f"NSGA-II con BLX-alfa en GLT  ({GENERACIONES} generaciones, poblacion 100 con 2 objetivos y 300 con 3)")
    fig.tight_layout()
    fig.savefig("nsga2_glt.png", dpi=150)

    print("\nResumen")
    print(f"  {'Problema':8} {'k':>2} {'|F1|':>5} {'Referencia':>20} {'HV':>8} {'HV opt':>8} {'%':>7} {'IGD':>8}")
    for (n, k, c, M, h, ho, p, d) in resumen:
        print(f"  {n:8} {k:>2} {c:>5} {str(M):>20} {h:>8.4f} {ho:>8.4f} {p:>6.1f}% {d:>8.4f}")

    plt.show()
