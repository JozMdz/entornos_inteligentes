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


def schaffer(x):
    f1 = x ** 2
    f2 = (x - 2) ** 2
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

N = 50                 # tamaño de la poblacion
GENERACIONES = 100
LIM_INF = -10 ** 5     # dominio de x 
LIM_SUP = 10 ** 5
ALFA = 0.5             # que tanto se estira el rango de los padres en la cruza
PROB_MUTACION = 0.1    # probabilidad de mutar a cada hijo


def evaluar(x):
    # arma la solucion [f1, f2, x]
    f1, f2 = schaffer(x)
    return [f1, f2, x]


def genera_poblacion(n):
    poblacion = []
    for _ in range(n):
        poblacion.append(evaluar(random.uniform(LIM_INF, LIM_SUP)))
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
    # p1, p2: valor de x de cada padre
    minimo = min(p1, p2)
    maximo = max(p1, p2)
    rango = maximo - minimo                          # range_i = max_i - min_i
    beta1 = minimo - rango * ALFA                    # B1 = min_i - range_i * alfa
    beta2 = maximo + rango * ALFA                    # B2 = max_i + range_i * alfa
    y1 = beta1 + random.random() * (beta2 - beta1)   # y1 = B1 + rand(B2 - B1)
    y2 = beta1 + random.random() * (beta2 - beta1)   # y2 = B1 + rand(B2 - B1), con otro rand
    return y1, y2


def mutacion(x):
    # mutacion uniforme: con cierta probabilidad, x se cambia por un valor al azar del dominio
    if random.random() < PROB_MUTACION:
        return random.uniform(LIM_INF, LIM_SUP)
    return x


def recortar(x):
    # si la cruza BLX puede sacar a x del dominio, aqui se regresa al limite
    return max(LIM_INF, min(LIM_SUP, x))


def make_new_pop(P, rango, distancia):
    # seleccion, cruza y mutacion para crear Q(t+1) a partir de P
    Q = []
    while len(Q) < N:
        padre1 = torneo(P, rango, distancia)
        padre2 = torneo(P, rango, distancia)
        y1, y2 = cruza_blx(padre1[2], padre2[2])
        Q.append(evaluar(recortar(mutacion(y1))))
        if len(Q) < N:
            Q.append(evaluar(recortar(mutacion(y2))))
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


def nsga2():
    P = genera_poblacion(N)                    # P0 aleatoria
    inicial = [list(sol) for sol in P]
    # P0 tambien se separa en frentes para que el primer torneo use <n
    # (con Q vacio, R = P0 cabe completo y nadie se descarta)
    P, rango, distancia = siguiente_poblacion(P, [])
    Q = make_new_pop(P, rango, distancia)      # Q0 = make-new-pop(P0)

    for t in range(GENERACIONES):
        P, rango, distancia = siguiente_poblacion(P, Q)
        Q = make_new_pop(P, rango, distancia)   # Qt+1 = make-new-pop(Pt+1)
                                                # t = t + 1 (lo hace el for)
    return inicial, P


if __name__ == "__main__":
    print("NSGA-II funcion de Schaffer")

    inicial, final = nsga2()
    final.sort(key=lambda p: p[2])

    frentes = fast_nondominated_sort(final)
    print(f"\nPoblacion final (generacion {GENERACIONES}): {len(frentes[0])} de {len(final)} soluciones en F1")
    for sol in final:
        print(f"  f1={sol[0]:.4f}  f2={sol[1]:.4f}  x={sol[2]:.4f}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

    ax1.scatter(
        [p[0] for p in inicial], [p[1] for p in inicial],
        s=12, alpha=0.5, color="#94a3b8", linewidths=0, label="Poblacion inicial",
    )
    ax1.scatter(
        [p[0] for p in final], [p[1] for p in final],
        s=12, color="#2563eb", label=f"Poblacion final (gen {GENERACIONES})",
    )
    ax1.set_title(f"Vista completa (x entre {LIM_INF} y {LIM_SUP})")
    ax1.legend(frameon=False)

    ax2.plot(
        [p[0] for p in final], [p[1] for p in final],
        color="#2563eb", linewidth=1.2, marker="o", markersize=4,
        label="Poblacion final",
    )
    ax2.set_xlim(-0.3, 4.3)
    ax2.set_ylim(-0.3, 4.3)
    ax2.set_title("Zoom al frente (x en [0, 2])")
    ax2.legend(frameon=False)

    for ax in (ax1, ax2):
        ax.set_xlabel("f1(x) = x^2")
        ax.set_ylabel("f2(x) = (x-2)^2")
        ax.grid(True, alpha=0.2)

    fig.suptitle("NSGA-II con BLX-alfa - Schaffer")
    fig.tight_layout()
    fig.savefig("nsga2_schaffer.png", dpi=150)
    plt.show()
