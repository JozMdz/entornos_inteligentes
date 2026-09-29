import random


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


# ---------------- NSGA-II (avance) ----------------

N = 10  # tamaño de la poblacion


def genera_poblacion(n):
    poblacion = []
    for _ in range(n):
        x = random.uniform(-10, 10)
        f1, f2 = schaffer(x)
        poblacion.append([f1, f2, x])
    return poblacion


def make_new_pop(P):
    # PENDIENTE: aqui va seleccion, cruza y mutacion para crear Q(t+1) a partir de P
    # por ahora se generan hijos aleatorios solo para poder probar el resto del ciclo
    return genera_poblacion(len(P))


def siguiente_poblacion(P, Q):
    R = P + Q                                   # Rt = Pt U Qt
    frentes = fast_nondominated_sort(R)         # F = fast-non-dominated-sort(Rt)

    P_nueva = []                                # Pt+1 = vacio
    i = 0                                       # i = 1 (aqui empieza en 0)
    while i < len(frentes) and len(P_nueva) + len(frentes[i]) <= N:   # until |Pt+1| + |Fi| <= N
        distancia = crowding_distance(frentes[i], R)                   # crowding-distance-assignment(Fi)
        for idx in frentes[i]:                                         # Pt+1 = Pt+1 U Fi
            P_nueva.append(R[idx])
        print(f"  F{i + 1} entra completo ({len(frentes[i])} soluciones)")
        i += 1                                                         # i = i + 1

    if len(P_nueva) < N:
        distancia = crowding_distance(frentes[i], R)
        ordenado = sorted(frentes[i], key=lambda idx: distancia[idx], reverse=True)   # Sort(Fi, <n)
        faltan = N - len(P_nueva)
        for idx in ordenado[:faltan]:                                                 # Fi[1 : (N - |Pt+1|)]
            P_nueva.append(R[idx])
        print(f"  F{i + 1} no cabe completo: entran {faltan} de {len(frentes[i])} (por crowding distance)")

    return P_nueva


if __name__ == "__main__":
    print("NSGA-II (avance) - funcion de Schaffer")

    P = genera_poblacion(N)
    Q = make_new_pop(P)

    print(f"\nRt = Pt U Qt: {len(P) + len(Q)} soluciones")
    P = siguiente_poblacion(P, Q)
    Q = make_new_pop(P)   # Qt+1 = make-new-pop(Pt+1)

    print(f"\nPt+1: {len(P)} soluciones")
    for sol in P:
        print(f"  f1={sol[0]:.4f}  f2={sol[1]:.4f}  x={sol[2]:.4f}")

    # PENDIENTE: repetir el ciclo por varias generaciones (t = t + 1) y graficar el frente final
