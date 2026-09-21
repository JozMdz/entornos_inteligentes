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


if __name__ == "__main__":
    print("Crowding distance - funcion de Schaffer")

    poblacion = []
    for _ in range(100):
        x = random.uniform(-10, 10)
        f1, f2 = schaffer(x)
        poblacion.append([f1, f2, x])

    frentes = fast_nondominated_sort(poblacion)

    for i in range(len(frentes)):
        distancias = crowding_distance(frentes[i], poblacion)
        print(f"\nF{i + 1}: {len(frentes[i])} soluciones")
        for idx in frentes[i]:
            sol = poblacion[idx]
            print(f"  f1={sol[0]:.4f}  f2={sol[1]:.4f}  x={sol[2]:.4f}  crowding_distance={distancias[idx]:.4f}")
