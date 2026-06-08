import pygame
import random
import sys
import math
from collections import deque

# Inicialización de Pygame y fuentes
pygame.init()
pygame.font.init()

# =============================================================================
# CONFIGURACIÓN Y PARÁMETROS INICIALES (Valores por defecto)
# =============================================================================
FILAS = 20
COLUMNAS = 30
FACTOR_SEPARACION = 25  
TIEMPO_TURNO = 0.4       
CANTIDAD_PERSONAS = 135  # ~25% de las celdas utilizables por defecto

# Colores (RGB)
COLOR_VACIO = (20, 20, 20)
COLOR_PARED = (80, 90, 100)      
COLOR_SALIDA = (52, 211, 153)    
COLOR_PERSONA = (244, 63, 94)    
COLOR_TEXTO = (255, 255, 255)
COLOR_INPUT_ACTIVO = (244, 63, 94)
COLOR_INPUT_INACTIVO = (70, 90, 120)
COLOR_BOTON = (52, 211, 153)

# Vecindad de Moore
VECINDAD_MOORE = [
    (-1, 0), (1, 0), (0, 1), (0, -1),
    (-1, 1), (1, 1), (-1, -1), (1, -1)
]

# Configuración de la ventana del menú inicial
VENTANA_ANCHO_MENU = 650
VENTANA_ALTO_MENU = 500
pantalla = pygame.display.set_mode((VENTANA_ANCHO_MENU, VENTANA_ALTO_MENU))
pygame.display.set_caption("Configuración de Evacuación")
reloj = pygame.time.Clock()
fuente_menu = pygame.font.SysFont("Arial", 24)
fuente_sim = pygame.font.SysFont(None, 14)

# Variables de control para los Inputs del Menú
input_filas_texto = str(FILAS)
input_columnas_texto = str(COLUMNAS)
input_personas_texto = str(CANTIDAD_PERSONAS)

activo_filas = False
activo_columnas = False
activo_personas = False

estado_actual = 'MENU'

# Variables globales de la simulación que se construirán al dar START
grilla_actual = []
campo_potencial = []
grilla_direcciones = []
lista_salidas = []

# =============================================================================
# FASE 1: CONSTRUIR ESCENARIO DINÁMICO
# =============================================================================
def inicializar_escenario(f_totales, c_totales, total_personas):
    global grilla_actual, campo_potencial, grilla_direcciones, lista_salidas
    
    grilla_actual = [[0 for _ in range(c_totales)] for _ in range(f_totales)]
    campo_potencial = [[99999 for _ in range(c_totales)] for _ in range(f_totales)]
    grilla_direcciones = [[(0.0, 1.0) for _ in range(c_totales)] for _ in range(f_totales)]
    lista_salidas = []

    # 1. Bordes del mapa
    for f in range(f_totales):
        for c in range(c_totales):
            if f == 0 or f == f_totales - 1 or c == 0 or c == c_totales - 1:
                grilla_actual[f][c] = 2

    # 2. Posicionar salida en el centro del muro derecho
    fila_salida = f_totales // 2
    grilla_actual[fila_salida][c_totales - 1] = 3
    lista_salidas.append((fila_salida, c_totales - 1))

    # 3. Diseño de paredes internas (Laberinto adaptativo)
    columna_muro1 = c_totales // 3
    for f in range(1, f_totales - 1):
        if f > 4:
            grilla_actual[f][columna_muro1] = 2

    columna_muro2 = (c_totales // 3) * 2
    for f in range(1, f_totales - 1):
        if f < f_totales - 5:
            grilla_actual[f][columna_muro2] = 2

    fila_muro_h = f_totales // 2
    for c in range(columna_muro1 + 1, columna_muro2):
        if c < columna_muro1 + 6:
            grilla_actual[fila_muro_h][c] = 2

    # 4. Reunir celdas realmente caminables para spawnear personas
    posiciones_validas = []
    for f in range(1, f_totales - 1):
        for c in range(1, c_totales - 1):
            if grilla_actual[f][c] == 0:
                posiciones_validas.append((f, c))
                
    # Fisher-Yates shuffle manual
    for i in range(len(posiciones_validas)):
        r_idx = random.randint(i, len(posiciones_validas) - 1)
        posiciones_validas[i], posiciones_validas[r_idx] = posiciones_validas[r_idx], posiciones_validas[i]

    # Spawnear la cantidad exacta solicitada respetando el espacio máximo libre
    personas_a_colocar = min(total_personas, len(posiciones_validas))
    for i in range(personas_a_colocar):
        f, c = posiciones_validas[i]
        grilla_actual[f][c] = 1
        grilla_direcciones[f][c] = (1.0, 0.0)

# =============================================================================
# FASE 2: CÁLCULO DEL CAMPO POTENCIAL BFS
# =============================================================================
def calcular_campo_potencial(f_totales, c_totales):
    cola_planificacion = deque()
    
    for salida in lista_salidas:
        campo_potencial[salida[0]][salida[1]] = 0
        cola_planificacion.append(salida)
        
    while cola_planificacion:
        actual_f, actual_c = cola_planificacion.popleft()
        costo_actual = campo_potencial[actual_f][actual_c]
        
        for df, dc in VECINDAD_MOORE:
            vf = actual_f + df
            vc = actual_c + dc
            
            if 0 <= vf < f_totales and 0 <= vc < c_totales and grilla_actual[vf][vc] != 2:
                costo_paso = 14 if (df != 0 and dc != 0) else 10
                if campo_potencial[vf][vc] > costo_actual + costo_paso:
                    campo_potencial[vf][vc] = costo_actual + costo_paso
                    cola_planificacion.append((vf, vc))

def dibujar_agente(pantalla, color, f, c, direccion):
    centro_x = c * FACTOR_SEPARACION + FACTOR_SEPARACION // 2
    centro_y = f * FACTOR_SEPARACION + FACTOR_SEPARACION // 2
    radio = int(FACTOR_SEPARACION * 0.35)
    
    pygame.draw.circle(pantalla, color, (centro_x, centro_y), radio)
    dir_x, dir_y = direccion
    mag = math.hypot(dir_x, dir_y)
    if mag > 0:
        dir_x, dir_y = dir_x / mag, dir_y / mag
        fin_x = centro_x + dir_x * radio
        fin_y = centro_y + dir_y * radio
        pygame.draw.line(pantalla, (255, 255, 255), (centro_x, centro_y), (fin_x, fin_y), 2)

# =============================================================================
# BUCLE PRINCIPAL
# =============================================================================
tiempo_acumulado = 0.0

while True:
    dt = reloj.tick(60) / 1000.0
    
    # --- ESTADO: MENÚ ---
    if estado_actual == 'MENU':
        # Calcular densidad informativa basada en el espacio transitable estimado
        try:
            f_temp = int(input_filas_texto) if input_filas_texto else 0
            c_temp = int(input_columnas_texto) if input_columnas_texto else 0
            p_temp = int(input_personas_texto) if input_personas_texto else 0
            
            # Estimación aproximada de celdas libres considerando muros perimetrales e internos
            celdas_totales = f_temp * c_temp
            if celdas_totales > 0:
                densidad_calculada = (p_temp / celdas_totales) * 100
            else:
                densidad_calculada = 0.0
        except ValueError:
            densidad_calculada = 0.0

        rect_filas = pygame.Rect(320, 120, 140, 40)
        rect_columnas = pygame.Rect(320, 180, 140, 40)
        rect_personas = pygame.Rect(320, 240, 140, 40)
        rect_boton_start = pygame.Rect(225, 370, 200, 50)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if evento.type == pygame.MOUSEBUTTONDOWN:
                activo_filas = rect_filas.collidepoint(evento.pos)
                activo_columnas = rect_columnas.collidepoint(evento.pos)
                activo_personas = rect_personas.collidepoint(evento.pos)
                
                if rect_boton_start.collidepoint(evento.pos):
                    try:
                        FILAS = max(10, int(input_filas_texto)) # Mínimo de seguridad para laberinto
                        COLUMNAS = max(15, int(input_columnas_texto))
                        CANTIDAD_PERSONAS = max(0, int(input_personas_texto))
                    except ValueError:
                        FILAS, COLUMNAS, CANTIDAD_PERSONAS = 20, 30, 135

                    inicializar_escenario(FILAS, COLUMNAS, CANTIDAD_PERSONAS)
                    calcular_campo_potencial(FILAS, COLUMNAS)
                    
                    # Ajustar ventana a la grilla dinámica
                    VENTANA_ANCHO = COLUMNAS * FACTOR_SEPARACION
                    VENTANA_ALTO = FILAS * FACTOR_SEPARACION
                    pantalla = pygame.display.set_mode((VENTANA_ANCHO, VENTANA_ALTO))
                    pygame.display.set_caption("Simulación de Evacuación")
                    estado_actual = 'SIMULACION'

            if evento.type == pygame.KEYDOWN:
                if activo_filas:
                    if evento.key == pygame.K_BACKSPACE: input_filas_texto = input_filas_texto[:-1]
                    elif evento.unicode.isdigit() and len(input_filas_texto) < 3: input_filas_texto += evento.unicode
                elif activo_columnas:
                    if evento.key == pygame.K_BACKSPACE: input_columnas_texto = input_columnas_texto[:-1]
                    elif evento.unicode.isdigit() and len(input_columnas_texto) < 3: input_columnas_texto += evento.unicode
                elif activo_personas:
                    if evento.key == pygame.K_BACKSPACE: input_personas_texto = input_personas_texto[:-1]
                    elif evento.unicode.isdigit() and len(input_personas_texto) < 5: input_personas_texto += evento.unicode

        # Renderizado Menú
        pantalla.fill((15, 23, 42)) # Azul medianoche elegante
        txt_titulo = fuente_menu.render("EVACUACIÓN: CONFIGURACIÓN DE AGENTES", True, COLOR_TEXTO)
        pantalla.blit(txt_titulo, (80, 40))
        
        # Inputs
        pantalla.blit(fuente_menu.render("Filas de la Grilla:", True, COLOR_TEXTO), (60, 125))
        pygame.draw.rect(pantalla, COLOR_INPUT_ACTIVO if activo_filas else COLOR_INPUT_INACTIVO, rect_filas, 2)
        pantalla.blit(fuente_menu.render(input_filas_texto, True, COLOR_TEXTO), (330, 125))
        
        pantalla.blit(fuente_menu.render("Columnas de la Grilla:", True, COLOR_TEXTO), (60, 185))
        pygame.draw.rect(pantalla, COLOR_INPUT_ACTIVO if activo_columnas else COLOR_INPUT_INACTIVO, rect_columnas, 2)
        pantalla.blit(fuente_menu.render(input_columnas_texto, True, COLOR_TEXTO), (330, 185))
        
        pantalla.blit(fuente_menu.render("Cantidad de Personas:", True, COLOR_TEXTO), (60, 245))
        pygame.draw.rect(pantalla, COLOR_INPUT_ACTIVO if activo_personas else COLOR_INPUT_INACTIVO, rect_personas, 2)
        pantalla.blit(fuente_menu.render(input_personas_texto, True, COLOR_TEXTO), (330, 245))

        # Densidad Informativa global
        txt_dens = fuente_menu.render(f"Densidad Total Estimada: {densidad_calculada:.1f}%", True, COLOR_INPUT_ACTIVO)
        pantalla.blit(txt_dens, (60, 310))
        
        # Botón Start
        pygame.draw.rect(pantalla, COLOR_BOTON, rect_boton_start, border_radius=5)
        pantalla.blit(fuente_menu.render("START", True, (15, 23, 42)), (295, 380))
        pygame.display.flip()

    # --- ESTADO: SIMULACIÓN ---
    elif estado_actual == 'SIMULACION':
        tiempo_acumulado += dt

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if tiempo_acumulado >= TIEMPO_TURNO:
            tiempo_acumulado = 0.0
            
            nueva_grilla = [[0 for _ in range(COLUMNAS)] for _ in range(FILAS)]
            nuevas_direcciones = [[(0.0, 0.0) for _ in range(COLUMNAS)] for _ in range(FILAS)]
            
            for f in range(FILAS):
                for c in range(COLUMNAS):
                    if grilla_actual[f][c] == 2 or grilla_actual[f][c] == 3:
                        nueva_grilla[f][c] = grilla_actual[f][c]

            mapa_de_deseos = {}

            # Inteligencia de Navegación Local
            for f in range(1, FILAS - 1):
                for c in range(1, COLUMNAS - 1):
                    if grilla_actual[f][c] != 1:
                        continue
                    
                    posicion_actual = (f, c)
                    celda_destino = posicion_actual
                    costo_actual = campo_potencial[f][c]
                    
                    opciones_ideales = []
                    opciones_rodeo = []
                    
                    for df, dc in VECINDAD_MOORE:
                        vf = f + df
                        vc = c + dc
                        
                        if 0 <= vf < FILAS and 0 <= vc < COLUMNAS:
                            if grilla_actual[vf][vc] == 0 or grilla_actual[vf][vc] == 3:
                                costo_vecino = campo_potencial[vf][vc]
                                if costo_vecino < costo_actual:
                                    opciones_ideales.append((vf, vc))
                                elif costo_vecino <= costo_actual + 14:
                                    opciones_rodeo.append((vf, vc))
                    
                    if opciones_ideales:
                        mejor_ideal = opciones_ideales[0]
                        for opc in opciones_ideales:
                            if campo_potencial[opc[0]][opc[1]] < campo_potencial[mejor_ideal[0]][mejor_ideal[1]]:
                                mejor_ideal = opc
                        celda_destino = mejor_ideal
                    elif opciones_rodeo:
                        mejor_rodeo = opciones_rodeo[0]
                        for opc in opciones_rodeo:
                            if campo_potencial[opc[0]][opc[1]] < campo_potencial[mejor_rodeo[0]][mejor_rodeo[1]]:
                                mejor_rodeo = opc
                        celda_destino = mejor_rodeo
                        
                    if celda_destino not in mapa_de_deseos:
                        mapa_de_deseos[celda_destino] = []
                    mapa_de_deseos[celda_destino].append(posicion_actual)

            # Resolución de Conflictos
            for destino, pretendientes in mapa_de_deseos.items():
                dfest, dcest = destino
                indice_ganador = random.randint(0, len(pretendientes) - 1)
                pos_ganador = pretendientes[indice_ganador]
                
                if grilla_actual[dfest][dcest] == 3:
                    for i, pos_perdedor in enumerate(pretendientes):
                        if i == indice_ganador: continue
                        pf, pc = pos_perdedor
                        nueva_grilla[pf][pc] = 1
                        nuevas_direcciones[pf][pc] = grilla_direcciones[pf][pc]
                elif destino != pos_ganador:
                    nueva_grilla[dfest][dcest] = 1
                    direccion_movimiento = (float(dcest - pos_ganador[1]), float(dfest - pos_ganador[0]))
                    nuevas_direcciones[dfest][dcest] = direccion_movimiento
                    
                    for i, pos_perdedor in enumerate(pretendientes):
                        if i == indice_ganador: continue
                        pf, pc = pos_perdedor
                        nueva_grilla[pf][pc] = 1
                        nuevas_direcciones[pf][pc] = grilla_direcciones[pf][pc]
                else:
                    nueva_grilla[dfest][dcest] = 1
                    nuevas_direcciones[dfest][dcest] = grilla_direcciones[pos_ganador[0]][pos_ganador[1]]

            grilla_actual = nueva_grilla
            grilla_direcciones = nuevas_direcciones

        # Renderizado Simulación
        pantalla.fill(COLOR_VACIO)
        for f in range(FILAS):
            for c in range(COLUMNAS):
                x = c * FACTOR_SEPARACION
                y = f * FACTOR_SEPARACION
                rect = pygame.Rect(x, y, FACTOR_SEPARACION, FACTOR_SEPARACION)
                
                valor = grilla_actual[f][c]
                if valor == 2:
                    pygame.draw.rect(pantalla, COLOR_PARED, rect)
                    pygame.draw.rect(pantalla, (50, 55, 60), rect, 1)
                elif valor == 3:
                    pygame.draw.rect(pantalla, COLOR_SALIDA, rect)
                elif valor == 1:
                    dibujar_agente(pantalla, COLOR_PERSONA, f, c, grilla_direcciones[f][c])
                    
        pygame.display.flip()