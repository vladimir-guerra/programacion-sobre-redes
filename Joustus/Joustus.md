# Joustus
## Integrantes
* Eduardo Vásquez
* Ernesto Gallego
* Lautaro Fortuna
* Federico Coronado

# Secuencia

## Paso 1
El jugador se conecta y espera a un rival.

## Paso 2

Una vez emparejado el jugador, se le entregan a ambos una matriz de 5x5 y una mano de 3 cartas. Ejemplo:

| X | - | - | - | X |
| :--- | :--- | :--- | :--- | :--- |
| - | O |   | O | - |
| - |   | O |   | - |
| - |   |   |   | - |
| X | - | - | - | X |

* X: Celda inhabilitada para movimientos
* -: Celda de descarte. El jugador no puede poner una carta aquí directamente, pero sí mediante __empuje__
* O: Celdas especial que suma puntos al jugador que tenga una carta puesta en ella. El jugador no puede poner una carta aquí directamente, pero sí mediante __empuje__
* Celdas vacías: El jugador puede poner cartas libremente en ellas.

Además, se entregará a cada jugador una mano de tres cartas. Cada carta puede tener una dirección (izquierda, derecha, arriba, abajo). Ejemplo:

| ↑ → | ↑ | ← ↑ → |
| :--- | :--- | :--- |

## Paso 3

En cada turno, el jugador debe poner una carta de su mano (respetando las reglas de celda anteriormente establecidas). Por ejemplo:

| X | - | - | - | X |
| :--- | :--- | :--- | :--- | :--- |
| - | O |   | O | - |
| - |   | O |   | - |
| - |   | ← ↑ → |   | - |
| X | - | - | - | X |

El jugador no solo puede poner cartas en celdas libres, sino que también puede desplazar otras cartas a las celdas condicionadas mediante empuje. El empuje precisa de las siguientes condiciones:

* La carta a poner tenga entre sus direcciones la dirección a la que se prentende empujar (por ejemplo, | ← ↑ → | puede empujar a la izquierda, a la derecha y arriba)
* Todas las cartas que se encuentren en la trayectoria del empuje __no__ pueden tener la dirección opuesta al empuje (por ejemplo, si se quiere empujar hacia arriba pero en la columna hay una carta con dirección hacia abajo, no se efectuará el movimiento)
* La pila de la columna o fila de la trayectoría no puede estar saturada (es decir, mientras la celda de descarte al final de la columna o fila esté libre, los movimientos serán válidos)

## Paso 4

Luego de que se agoten los movimientos posibles, la partida termina. Se cuenta qué jugador tiene más cartas puestas en las celdas especiales y el que tenga más, gana. 
