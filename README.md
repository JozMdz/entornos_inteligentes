# entornos_inteligentes

Aquí les cuento qué hace cada archivo y cómo funcionan las partes más densas del código, para que quede bien entendible aunque no hayan seguido toda la conversación donde lo armamos.

---

## `dominancia.py`

El primer intento, bien básico: generamos un montón de puntos 2D aleatorios y nos quedamos solo con los que "nadie les gana" en los dos objetivos a la vez — eso es la dominancia.

### `dominancia(a, b)`
Esta función responde: **¿el punto `a` domina al punto `b`?** (o sea, ¿`a` es mejor o igual en todo y mejor en al menos una cosa?). Como es minimización, "mejor" = "menor".

```python
def dominancia(a, b):
    bandera = 0
    i = 0
    while i < len(a) and a[i] <= b[i]:
        if a[i] < b[i]:
            bandera = 1
        i += 1
    if bandera == 1 and i >= len(a):
        return True
    else:
        return False
```
- El `while` va recorriendo cada objetivo (`i=0` sería `f1`, `i=1` sería `f2`, etc.) y **se detiene apenas encuentra un objetivo donde `a` es peor que `b`** (`a[i] <= b[i]` deja de cumplirse).
- Si en algún objetivo `a` fue estrictamente menor, prende la `bandera = 1` (o sea, "sí hubo mejora en algo").
- Al final, solo si el `while` llegó hasta el final SIN cortarse (`i >= len(a)`, es decir, `a` nunca fue peor en nada) Y además hubo al menos una mejora (`bandera==1`), decimos que `a` domina a `b`.
- Si `a` y `b` son idénticos, `bandera` se queda en 0 y devuelve `False` (nadie domina a nadie, son iguales).

### `agrega(a, arreglo)`
Esta es la que arma el "archivo" (la lista de soluciones no dominadas encontradas hasta el momento), agregando una solución nueva (`arreglo`) de una en una:

```python
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
```
1. Primero revisa: **¿alguien que ya está en el archivo domina a la solución nueva?** Si sí, la nueva ni entra (`dominado = True`, no se hace nada más).
2. Si nadie la domina, entonces la solución nueva es válida — pero antes de meterla, hay que **sacar del archivo a cualquiera que la nueva solución domine** (porque ya no pertenecen al frente). Por eso el `while` con `a.pop(x)`: recorre el archivo y va borrando a los que quedaron obsoletos (nota que solo avanza `x += 1` cuando NO borra, porque al hacer `pop` todo se recorre un lugar).
3. Al final, agrega la solución nueva al archivo.

En el `__main__` se generan 100,000 puntos aleatorios `[random.random(), random.random()]`, se van metiendo uno por uno con `agrega()`, y se grafica la nube completa (gris) contra el frente que sobrevivió (azul).

---

## `schaffer.py`

Mismo mecanismo de `dominancia.py`, pero ahora los puntos no son aleatorios "sueltos" — vienen de evaluar la **función de Schaffer**:

```python
def schaffer(x):
    f1 = x ** 2
    f2 = (x - 2) ** 2
    return f1, f2
```
Es decir, cada solución depende de un solo número `x`, y de ahí salen los dos objetivos: `f1` (qué tan cerca está `x` de 0) y `f2` (qué tan cerca está `x` de 2). El "tira y afloja" entre ambos es lo interesante del problema.

Aquí `agrega()` cambia un poco: cada solución guardada es `[f1, f2, x]` (le pegamos el valor de `x` de dónde salió, para poder saber después qué `x` generó cada punto del frente), y por eso al comparar con `dominancia()` se usa `[:2]` — o sea, solo se comparan los primeros dos valores (los objetivos), ignorando el `x` que viaja pegado.

Al final se generan 100,000 valores de `x` entre -1000 y 1000, y se grafican dos vistas: una completa y otra con **zoom** a la zona `x∈[0,2]` (que es donde realmente vive el frente óptimo — fuera de ahí, todo queda dominado).

---

## `frentes_schaffer.py`

Aquí subimos de nivel: ya no solo queremos "el mejor frente", queremos **separar TODAS las soluciones en capas** F1, F2, F3... Eso es el algoritmo **fast-non-dominated-sort** (el del pseudocódigo que dio el profe).

### `fast_nondominated_sort(poblacion)`
```python
def fast_nondominated_sort(poblacion):
    n = len(poblacion)
    dominados_por = [[] for _ in range(n)]  # Sp
    contador_dominacion = [0] * n           # np
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
    ...
```
- **Primera parte (doble `for`)**: para cada solución `p`, la comparamos contra TODAS las demás `q`. Si `p` domina a `q`, anotamos a `q` en la lista de "a quiénes domina `p`" (`dominados_por[p]`, esto es la `Sp` del pseudocódigo). Si en cambio `q` domina a `p`, le sumamos 1 al contador de `p` (`contador_dominacion[p]`, la `np` del pseudocódigo — cuántos le ganan a `p`).
- Al terminar de comparar a `p` contra todos, si nadie le ganó (`contador_dominacion[p] == 0`), entonces `p` es parte del primer frente, **F1**.

```python
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
    frentes.pop()
    return frentes
```
- **Segunda parte**: ya con F1 armado, hay que ir "pelando capas". Por cada solución `p` del frente actual, vamos a sus dominadas (`dominados_por[p]`) y les restamos 1 a su contador — es como decirles "ya no cuentes a `p` como alguien que te gana, porque `p` ya se fue a su frente". Si al restar el contador de alguna `q` llega a 0 (ya nadie que quede "activo" le gana), esa `q` pasa al siguiente frente.
- Esto se repite frente tras frente hasta que un frente sale vacío (ya no queda nadie), y ese último vacío se descarta con `frentes.pop()`.

En el `__main__` se generan 150 soluciones con `x ∈ [-10⁵, 10⁵]` (dominio pedido en clase) y se grafican todos los frentes con distintos colores (usando `plt.cm.viridis` para generar una escala de colores automática). **Dato importante**: con este dominio tan grande, casi todos los frentes terminan con **una sola solución** — no es error, es que con una sola variable `x`, fuera del tramo `[0,2]` (donde de verdad hay competencia entre `f1` y `f2`), las soluciones quedan ordenadas en una fila estricta (cada una le gana a la siguiente), así que no hay manera de que dos empaten en el mismo frente.

---

## `frentes_schaffer_2var.py`

Exactamente el mismo algoritmo de arriba (`dominancia` y `fast_nondominated_sort` calcados), pero le agregamos una segunda variable de decisión:

```python
def schaffer2(x1, x2):
    f1 = x1 ** 2 + x2 ** 2
    f2 = (x1 - 2) ** 2 + (x2 - 2) ** 2
    return f1, f2
```
Ahora `f1` es la distancia al punto `(0,0)` y `f2` la distancia al punto `(2,2)`. Al tener dos variables (`x1` y `x2`) en vez de una sola, hay muchísima más libertad geométrica para que varias soluciones queden empatadas (que ninguna le gane a la otra) — por eso aquí sí salen frentes con varios puntos cada uno, como el dibujo que enseñaron en clase. Usamos un dominio más chico (`x1, x2 ∈ [-4,4]`) porque si lo hacíamos igual de grande que el anterior (`10⁵`), pasaba lo mismo que con 1 variable: todo se dispersa tanto que los objetivos vuelven a comportarse casi como uno solo.

---

## `crowding_distance_schaffer.py`

El último paso: a cada solución, dentro de su propio frente, le calculamos qué tan "sola" está respecto a sus vecinas — eso es la **crowding distance**. Sirve para saber qué soluciones son más valiosas para mantener diversidad (las que están en zonas menos pobladas del frente).

### `crowding_distance(frente, poblacion, num_objetivos=2)`
```python
VALOR_GRANDE = 999999

def crowding_distance(frente, poblacion, num_objetivos=2):
    l = len(frente)
    distancia = {idx: 0 for idx in frente}

    for m in range(num_objetivos):
        ordenado = sorted(frente, key=lambda idx: poblacion[idx][m])
        distancia[ordenado[0]] = VALOR_GRANDE
        distancia[ordenado[-1]] = VALOR_GRANDE
        for i in range(1, l - 1):
            distancia[ordenado[i]] += poblacion[ordenado[i + 1]][m] - poblacion[ordenado[i - 1]][m]

    return distancia
```
- `distancia` es un diccionario `{índice_de_la_solución: su_distancia}`, y arranca todo en 0.
- El `for m in range(2)` repite el proceso una vez por cada objetivo (`m=0` es `f1`, `m=1` es `f2`).
- `ordenado = sorted(...)` reordena las soluciones del frente de menor a mayor **según ese objetivo**.
- `ordenado[0]` (la mejor en ese objetivo) y `ordenado[-1]` (la peor) son los **puntos frontera** — a esos siempre se les pone `VALOR_GRANDE` (en vez de `∞` como dice el pseudocódigo original, usamos un número grande porque así lo pidió el profe) para asegurarnos de que nunca se descarten, son los extremos del frente.
- Para el resto (`i` de 1 a `l-2`, o sea los que quedan "en medio"), la distancia se va sumando con `poblacion[ordenado[i+1]][m] - poblacion[ordenado[i-1]][m]` — es literalmente "qué tan separados están mis dos vecinos" en ese objetivo. Entre más separados, más "sola" está esa solución ahí. Esto se hace **sin normalizar** (o sea, sin dividir entre el rango del objetivo), porque el profe dijo que también se vale hacerlo así.
- Como el `for m` se repite para los 2 objetivos, cada solución termina con la **suma** de qué tan aislada está en `f1` más qué tan aislada está en `f2`.

**Por qué salen tantos `999999` al correrlo**: la mayoría de los frentes de Schaffer con 1 variable solo tienen 2 soluciones (ya explicado arriba). Cuando un frente tiene nada más 2 elementos, ambos son al mismo tiempo "el primero" y "el último" al ordenar — o sea, los dos siempre caen como punto frontera, y los dos terminan con `999999`. Nada más en frentes de 3+ soluciones (como el F1) se alcanzan a ver valores "normales" en los de en medio.

El `__main__` genera 100 soluciones (`x ∈ [-10,10]`), separa en frentes, y por cada frente imprime cada solución con sus valores (`f1`, `f2`, `x`) junto a su crowding distance.
