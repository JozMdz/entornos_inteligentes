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


def get_bound_value(lista, i, M):
    # u_i(p1): el menor valor mayor que f_i(x1) entre los vectores 2 a Size
    # si no hay ninguno, la cota es M_i (el punto de referencia)
    p1 = lista[0]
    b = M[i]
    for q in lista[1:]:
        if p1[i] < q[i] < b:
            b = q[i]
    return b


def spawn_vector(p1, i, b):
    # p1i = p1 con el objetivo i cambiado por su cota b_i
    nuevo = list(p1)
    nuevo[i] = b
    return nuevo


def nd_filter(lista, spawn_data, M):
    # borra de SpawnData los vectores dominados por alguno de List
    # o que tengan un M_i (su hipercubo tendria un lado de longitud cero)
    filtrados = []
    for s in spawn_data:
        dominado = False
        for q in lista:
            if dominancia(q, s):
                dominado = True
        tiene_M = False
        for i in range(len(M)):
            if s[i] == M[i]:
                tiene_M = True
        if not dominado and not tiene_M:
            filtrados.append(s)

    lista[0:0] = filtrados   # SpawnData se inserta en List en lugar de p1
    return len(lista)


def leb_measure(frente, M):
    # frente: soluciones no dominadas [f1, f2, ...], M: punto de referencia (minimizar)
    lista = [list(p) for p in frente]
    n = len(M)

    leb = 0.0                                          # LebMeasure = 0.0
    new_size = len(lista)                              # newSize = Size
    while new_size > 1:                                # while (newSize > 1)
        lop_off_vol = 1.0                              # lopOffVol = 1.0
        p1 = lista[0]                                  # get first vector p1 in List
        spawn_data = []
        for i in range(n):                             # for (i = 0; i < n; i++)
            b = get_bound_value(lista, i, M)           # bi = getBoundValue(fi(x1))
            spawn_data.append(spawn_vector(p1, i, b))  # spawnVector(p1, i, bi)
            lop_off_vol *= abs(p1[i] - b)              # lopOffVol *= |fi(x1) - bi|
        leb += lop_off_vol                             # LebMeasure += lopOffVol
        lista.pop(0)                                   # delete p1 from List
        new_size = nd_filter(lista, spawn_data, M)     # newSize = ndFilter(List, SpawnData)
                                                       # clear SpawnData (se crea vacia en cada vuelta)

    last_vol = 1.0                                     # lastVol = 1.0
    for i in range(n):
        last_vol *= abs(lista[0][i] - M[i])            # lastVol *= |fi(x1) - Mi|
    leb += last_vol   # el pseudocodigo calcula lastVol pero no lo suma; sin esto falta el ultimo cubo

    return leb                                         # return (LebMeasure)


if __name__ == "__main__":
    print("Hypervolume (LebMeasure) - frente de ejemplo")

    frente = [[1.0, 6.0], [2.0, 4.0], [3.0, 3.0], [5.0, 1.0]]
    M = [6.0, 7.0]   # punto de referencia

    for p in frente:
        print(f"  f1={p[0]}  f2={p[1]}")
    print(f"  referencia = {M}")
    print(f"  HV = {leb_measure(frente, M)}")
