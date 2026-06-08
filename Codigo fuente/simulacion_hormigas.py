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
FILAS = 40
COLUMNAS = 70
FACTOR_SEPARACION = 12   # Tamaño de cada celda en píxeles
TIEMPO_TURNO = 0.08      
TIEMPO_APARICION = 0.5   
MAX_HORMIGAS = 50

# Colores (RGB)
COLOR_VACIO = (25, 20, 15)        
COLOR_PARED = (75, 70, 65)        
COLOR_NIDO = (139, 90, 43)        
COLOR_COMIDA = (34, 197, 94)      
COLOR_BUSCANDO = (200, 200, 200)  
COLOR_CARGADA = (234, 179, 8)     
COLOR_TEXTO = (255, 255, 255)
COLOR_INPUT_ACTIVO = (234, 179, 8)  # Amarillo hormiga cargada para foco
COLOR_INPUT_INACTIVO = (70, 90, 120)
COLOR_BOTON = (34, 197, 94)

# Vecindad de Moore
VECINDAD_MOORE = [
    (-1, 0), (1, 0), (0, 1), (0, -1),
    (-1, 1), (1, 1), (-1, -1), (1, -1)
]

# Configuración de la ventana del menú inicial
VENTANA_ANCHO_MENU = 650
VENTANA_ALTO_MENU = 500
pantalla = pygame.display.set_mode((VENTANA_ANCHO_MENU, VENTANA_ALTO_MENU))
pygame.display.set_caption("Configuración de Colonia de Hormigas")
reloj = pygame.time.Clock()
fuente_menu = pygame.font.SysFont("Arial", 24)

# Variables de control para los Inputs del Menú
input_filas_texto = str(FILAS)
input_columnas_texto = str(COLUMNAS)
input_hormigas_texto = str(MAX_HORMIGAS)

activo_filas = False
activo_columnas = False
activo_hormigas = False

estado_actual = 'MENU'

# Variables globales de la simulación que se construirán al dar START
grilla_actual = []
grilla_feromonas = []
campo_potencial_nido = []
pasos_sin_comida = []
grilla_direcciones = []
lista_comidas = []
posicion_nido = (0, 0)
posicion_nacimiento = (0, 0)
hormigas_actuales_en_el_mapa = 0

# =============================================================================
# FASE 1: CONSTRUIR ESCENARIO DINÁMICO
# =============================================================================
def inicializar_escenario(f_totales, c_totales):
    global grilla_actual, grilla_feromonas, campo_potencial_nido, pasos_sin_comida, \
           grilla_direcciones, lista_comidas, posicion_nido, posicion_nacimiento, \
           hormigas_actuales_en_el_mapa
           
    grilla_actual = [[0 for _ in range(c_totales)] for _ in range(f_totales)]
    grilla_feromonas = [[0.0 for _ in range(c_totales)] for _ in range(f_totales)]
    campo_potencial_nido = [[9999 for _ in range(c_totales)] for _ in range(f_totales)]
    pasos_sin_comida = [[0 for _ in range(c_totales)] for _ in range(f_totales)]
    grilla_direcciones = [[(1.0, 0.0) for _ in range(c_totales)] for _ in range(f_totales)]
    
    lista_comidas = []
    hormigas_actuales_en_el_mapa = 0
    
    # Redefinir posiciones clave basadas en el nuevo tamaño
    posicion_nido = (f_totales // 2, 4)
    posicion_nacimiento = (posicion_nido[0], posicion_nido[1] + 1)

    # 1. Crear bordes exteriores (Paredes)
    for f in range(f_totales):
        for c in range(c_totales):
            if f == 0 or f == f_totales - 1 or c == 0 or c == c_totales - 1:
                grilla_actual[f][c] = 5

    # 2. Registrar el Nido estático
    grilla_actual[posicion_nido[0]][posicion_nido[1]] = 3

    # 3. Colocar exactamente 6 fuentes de comida desalineadas hacia el este
    while len(lista_comidas) < 6:
        fila_comida = random.randint(4, f_totales - 5)
        col_comida = random.randint(c_totales // 2 - 2, c_totales - 6)
        
        if grilla_actual[fila_comida][col_comida] == 0:
            grilla_actual[fila_comida][col_comida] = 4
            lista_comidas.append((fila_comida, col_comida))

    # 4. Generar formaciones de muros / Rocas dispersas proporcionales al tamaño
    cantidad_rocas = int((f_totales * c_totales) * 0.0125)
    for _ in range(cantidad_rocas):
        rf = random.randint(4, f_totales - 5)
        rc = random.randint(c_totales // 4, (c_totales // 4) * 3)
        
        if grilla_actual[rf][rc] == 0:
            grilla_actual[rf][rc] = 5
            if random.random() < 0.5 and rf + 1 < f_totales - 1:
                grilla_actual[rf + 1][rc] = 5
            if random.random() < 0.5 and rc + 1 < c_totales - 1:
                grilla_actual[rf][rc + 1] = 5

# =============================================================================
# FASE 2: MAPA POTENCIAL BFS AL NIDO
# =============================================================================
def calcular_campo_potencial_nido(f_totales, c_totales):
    cola = deque()
    campo_potencial_nido[posicion_nido[0]][posicion_nido[1]] = 0
    cola.append(posicion_nido)
    
    while cola:
        act_f, act_c = cola.popleft()
        for df, dc in VECINDAD_MOORE:
            vf = act_f + df
            vc = act_c + dc
            if 0 <= vf < f_totales and 0 <= vc < c_totales and grilla_actual[vf][vc] != 5:
                if campo_potencial_nido[vf][vc] > campo_potencial_nido[act_f][act_c] + 1:
                    campo_potencial_nido[vf][vc] = campo_potencial_nido[act_f][act_c] + 1
                    cola.append((vf, vc))

# =============================================================================
# RENDERIZADO VECTORIAL ROTADO
# =============================================================================
def dibujar_hormiga(pantalla, color, f, c, direccion):
    centro_x = c * FACTOR_SEPARACION + FACTOR_SEPARACION // 2
    centro_y = f * FACTOR_SEPARACION + FACTOR_SEPARACION // 2
    radio = FACTOR_SEPARACION // 2
    
    dir_x, dir_y = direccion
    angulo = math.atan2(-dir_y, dir_x)
    
    p1 = (centro_x + radio * math.cos(angulo), centro_y - radio * math.sin(angulo))
    p2 = (centro_x + radio * 0.4 * math.cos(angulo + 2.4), centro_y - radio * 0.4 * math.sin(angulo + 2.4))
    p3 = (centro_x + radio * 0.4 * math.cos(angulo - 2.4), centro_y - radio * 0.4 * math.sin(angulo - 2.4))
    
    pygame.draw.polygon(pantalla, color, [p1, p2, p3])

# =============================================================================
# BUCLE PRINCIPAL
# =============================================================================
tiempo_acumulado_turno = 0.0
tiempo_acumulado_goteo = 0.0

while True:
    dt = reloj.tick(60) / 1000.0  
    
    # --- ESTADO: MENÚ ---
    if estado_actual == 'MENU':
        try:
            f_temp = int(input_filas_texto) if input_filas_texto else 0
            c_temp = int(input_columnas_texto) if input_columnas_texto else 0
            h_temp = int(input_hormigas_texto) if input_hormigas_texto else 0
            celdas_totales = f_temp * c_temp
            densidad_calculada = (h_temp / celdas_totales * 100) if celdas_totales > 0 else 0.0
        except ValueError:
            densidad_calculada = 0.0

        rect_filas = pygame.Rect(320, 120, 140, 40)
        rect_columnas = pygame.Rect(320, 180, 140, 40)
        rect_hormigas = pygame.Rect(320, 240, 140, 40)
        rect_boton_start = pygame.Rect(225, 370, 200, 50)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if evento.type == pygame.MOUSEBUTTONDOWN:
                activo_filas = rect_filas.collidepoint(evento.pos)
                activo_columnas = rect_columnas.collidepoint(evento.pos)
                activo_hormigas = rect_hormigas.collidepoint(evento.pos)
                
                if rect_boton_start.collidepoint(evento.pos):
                    try:
                        FILAS = max(10, int(input_filas_texto))
                        COLUMNAS = max(20, int(input_columnas_texto))
                        MAX_HORMIGAS = max(1, int(input_hormigas_texto))
                    except ValueError:
                        FILAS, COLUMNAS, MAX_HORMIGAS = 40, 70, 50

                    inicializar_escenario(FILAS, COLUMNAS)
                    calcular_campo_potencial_nido(FILAS, COLUMNAS)
                    
                    # Forzar rediseño de ventana adaptada a la grilla móvil
                    VENTANA_ANCHO = COLUMNAS * FACTOR_SEPARACION
                    VENTANA_ALTO = FILAS * FACTOR_SEPARACION
                    pantalla = pygame.display.set_mode((VENTANA_ANCHO, VENTANA_ALTO))
                    pygame.display.set_caption("Simulación de Colonia de Hormigas")
                    estado_actual = 'SIMULACION'

            if evento.type == pygame.KEYDOWN:
                if activo_filas:
                    if evento.key == pygame.K_BACKSPACE: input_filas_texto = input_filas_texto[:-1]
                    elif evento.unicode.isdigit() and len(input_filas_texto) < 3: input_filas_texto += evento.unicode
                elif activo_columnas:
                    if evento.key == pygame.K_BACKSPACE: input_columnas_texto = input_columnas_texto[:-1]
                    elif evento.unicode.isdigit() and len(input_columnas_texto) < 3: input_columnas_texto += evento.unicode
                elif activo_hormigas:
                    if evento.key == pygame.K_BACKSPACE: input_hormigas_texto = input_hormigas_texto[:-1]
                    elif evento.unicode.isdigit() and len(input_hormigas_texto) < 4: input_hormigas_texto += evento.unicode

        pantalla.fill((20, 18, 24))
        txt_titulo = fuente_menu.render("COLONIA DE HORMIGAS: CONFIGURACIÓN", True, COLOR_TEXTO)
        pantalla.blit(txt_titulo, (90, 40))
        
        # UI Inputs
        pantalla.blit(fuente_menu.render("Filas de la Grilla:", True, COLOR_TEXTO), (60, 125))
        pygame.draw.rect(pantalla, COLOR_INPUT_ACTIVO if activo_filas else COLOR_INPUT_INACTIVO, rect_filas, 2)
        pantalla.blit(fuente_menu.render(input_filas_texto, True, COLOR_TEXTO), (330, 125))
        
        pantalla.blit(fuente_menu.render("Columnas de la Grilla:", True, COLOR_TEXTO), (60, 185))
        pygame.draw.rect(pantalla, COLOR_INPUT_ACTIVO if activo_columnas else COLOR_INPUT_INACTIVO, rect_columnas, 2)
        pantalla.blit(fuente_menu.render(input_columnas_texto, True, COLOR_TEXTO), (330, 185))
        
        pantalla.blit(fuente_menu.render("Máximo de Hormigas:", True, COLOR_TEXTO), (60, 245))
        pygame.draw.rect(pantalla, COLOR_INPUT_ACTIVO if activo_hormigas else COLOR_INPUT_INACTIVO, rect_hormigas, 2)
        pantalla.blit(fuente_menu.render(input_hormigas_texto, True, COLOR_TEXTO), (330, 245))

        txt_dens = fuente_menu.render(f"Densidad de Población: {densidad_calculada:.1f}%", True, COLOR_INPUT_ACTIVO)
        pantalla.blit(txt_dens, (60, 310))
        
        pygame.draw.rect(pantalla, COLOR_BOTON, rect_boton_start, border_radius=5)
        pantalla.blit(fuente_menu.render("START", True, COLOR_VACIO), (295, 380))
        pygame.display.flip()

    # --- ESTADO: SIMULACIÓN ---
    elif estado_actual == 'SIMULACION':
        tiempo_acumulado_turno += dt
        tiempo_acumulado_goteo += dt

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # 1. GENERACIÓN POR GOTEO ESTRICTO
        if hormigas_actuales_en_el_mapa < MAX_HORMIGAS and tiempo_acumulado_goteo >= TIEMPO_APARICION:
            tiempo_acumulado_goteo = 0.0
            if grilla_actual[posicion_nacimiento[0]][posicion_nacimiento[1]] == 0:
                grilla_actual[posicion_nacimiento[0]][posicion_nacimiento[1]] = 1 
                pasos_sin_comida[posicion_nacimiento[0]][posicion_nacimiento[1]] = 0
                grilla_direcciones[posicion_nacimiento[0]][posicion_nacimiento[1]] = (1.0, 0.0) 
                hormigas_actuales_en_el_mapa += 1

        # 2. AVANCE GENERACIONAL DEL AUTÓMATA
        if tiempo_acumulado_turno >= TIEMPO_TURNO:
            tiempo_acumulado_turno = 0.0
            
            nueva_grilla = [fila[:] for fila in grilla_actual]
            nuevos_pasos = [[0 for _ in range(COLUMNAS)] for _ in range(FILAS)]
            nuevas_direcciones = [[(0.0, 0.0) for _ in range(COLUMNAS)] for _ in range(FILAS)]
            
            for f in range(FILAS):
                for c in range(COLUMNAS):
                    if nueva_grilla[f][c] == 1 or nueva_grilla[f][c] == 2:
                        nueva_grilla[f][c] = 0

            mapa_deseos = {}
            mapa_memorias = {}

            # FASE A: Evaluación de intenciones
            for f in range(1, FILAS - 1):
                for c in range(1, COLUMNAS - 1):
                    estado_ant = grilla_actual[f][c]
                    if estado_ant != 1 and estado_ant != 2:
                        continue
                    
                    pos_act = (f, c)
                    destino = pos_act
                    memoria_actual = pasos_sin_comida[f][c]

                    # --- EXPLORADORA ---
                    if estado_ant == 1:
                        memoria_actual += 1
                        comida_cerca = False
                        pos_comida_detectada = (0, 0)
                        
                        for df, dc in VECINDAD_MOORE:
                            if grilla_actual[f + df][c + dc] == 4:
                                pos_comida_detectada = (f + df, c + dc)
                                comida_cerca = True
                                break
                                
                        if comida_cerca:
                            destino = pos_comida_detectada
                            memoria_actual = 0
                        else:
                            max_feromona = 0.05
                            max_distancia_nido = -1
                            opciones_rastro_validas = []
                            
                            for df, dc in VECINDAD_MOORE:
                                vf = f + df
                                vc = c + dc
                                if grilla_actual[vf][vc] == 0 or grilla_actual[vf][vc] == 3:
                                    feno = grilla_feromonas[vf][vc]
                                    if feno > max_feromona:
                                        dist_nido = campo_potencial_nido[vf][vc]
                                        if dist_nido > max_distancia_nido:
                                            max_distancia_nido = dist_nido
                                            opciones_rastro_validas = [(vf, vc)]
                                        elif dist_nido == max_distancia_nido:
                                            opciones_rastro_validas.append((vf, vc))
                                            
                            if opciones_rastro_validas:
                                destino = random.choice(opciones_rastro_validas)
                                memoria_actual = 0
                            else:
                                paso_hacia_adelante = []
                                paso_regreso_opcional = []
                                
                                for df, dc in VECINDAD_MOORE:
                                    vf = f + df
                                    vc = c + dc
                                    if grilla_actual[vf][vc] == 0:
                                        if dc >= 0:
                                            paso_hacia_adelante.append((vf, vc))
                                        else:
                                            paso_regreso_opcional.append((vf, vc))
                                            
                                if (c >= COLUMNAS - 3 or memoria_actual > 12) and paso_regreso_opcional:
                                    destino = random.choice(paso_regreso_opcional)
                                    if random.random() < 0.2:
                                        memoria_actual = 0
                                elif paso_hacia_adelante:
                                    destino = random.choice(paso_hacia_adelante)
                                elif paso_regreso_opcional:
                                    destino = random.choice(paso_regreso_opcional)

                    # --- DE RETORNO (CARGADA) ---
                    elif estado_ant == 2:
                        memoria_actual = 0
                        grilla_feromonas[f][c] = min(grilla_feromonas[f][c] + 0.6, 1.0)
                        
                        min_costo = campo_potencial_nido[f][c]
                        for df, dc in VECINDAD_MOORE:
                            vf = f + df
                            vc = c + dc
                            if grilla_actual[vf][vc] in (0, 3, 4):
                                if campo_potencial_nido[vf][vc] < min_costo:
                                    min_costo = campo_potencial_nido[vf][vc]
                                    destino = (vf, vc)

                    if destino not in mapa_deseos:
                        mapa_deseos[destino] = []
                        mapa_memorias[destino] = []
                    mapa_deseos[destino].append(pos_act)
                    mapa_memorias[destino].append(memoria_actual)

            # FASE B: Resolución de conflictos (Exclusión Mutua)
            for destino, hormigas in mapa_deseos.items():
                memorias_asociadas = mapa_memorias[destino]
                ganador_idx = random.randint(0, len(hormigas) - 1)
                pos_ganador = hormigas[ganador_idx]
                memoria_ganador = memorias_asociadas[ganador_idx]
                estado_hormiga = grilla_actual[pos_ganador[0]][pos_ganador[1]]
                
                es_destino_comida = (grilla_actual[destino[0]][destino[1]] == 4)
                dir_movimiento = (float(destino[1] - pos_ganador[1]), float(-(destino[0] - pos_ganador[0])))
                if dir_movimiento == (0.0, 0.0):
                    dir_movimiento = grilla_direcciones[pos_ganador[0]][pos_ganador[1]]

                if destino == posicion_nido and estado_hormiga == 2:
                    nueva_grilla[pos_ganador[0]][pos_ganador[1]] = 1  
                    nuevos_pasos[pos_ganador[0]][pos_ganador[1]] = 0
                    nuevas_direcciones[pos_ganador[0]][pos_ganador[1]] = (1.0, 0.0)
                    
                elif es_destino_comida and estado_hormiga == 1:
                    nueva_grilla[pos_ganador[0]][pos_ganador[1]] = 2  
                    nuevos_pasos[pos_ganador[0]][pos_ganador[1]] = 0
                    nuevas_direcciones[pos_ganador[0]][pos_ganador[1]] = (-1.0, 0.0)
                    
                elif grilla_actual[destino[0]][destino[1]] == 0:
                    nueva_grilla[destino[0]][destino[1]] = estado_hormiga
                    nuevos_pasos[destino[0]][destino[1]] = memoria_ganador
                    nuevas_direcciones[destino[0]][destino[1]] = dir_movimiento
                else:
                    nueva_grilla[pos_ganador[0]][pos_ganador[1]] = estado_hormiga
                    nuevos_pasos[pos_ganador[0]][pos_ganador[1]] = memoria_ganador
                    nuevas_direcciones[pos_ganador[0]][pos_ganador[1]] = grilla_direcciones[pos_ganador[0]][pos_ganador[1]]

                for i, pos_perdedor in enumerate(hormigas):
                    if i == ganador_idx: continue
                    nueva_grilla[pos_perdedor[0]][pos_perdedor[1]] = grilla_actual[pos_perdedor[0]][pos_perdedor[1]]
                    nuevos_pasos[pos_perdedor[0]][pos_perdedor[1]] = memorias_asociadas[i]
                    nuevas_direcciones[pos_perdedor[0]][pos_perdedor[1]] = grilla_direcciones[pos_perdedor[0]][pos_perdedor[1]]

            grilla_actual = nueva_grilla
            pasos_sin_comida = nuevos_pasos
            grilla_direcciones = nuevas_direcciones

            # 3. EVAPORACIÓN DINÁMICA DE FEROMONAS
            for f in range(FILAS):
                for c in range(COLUMNAS):
                    if grilla_feromonas[f][c] > 0.0:
                        grilla_feromonas[f][c] -= 0.012  
                        if grilla_feromonas[f][c] < 0.0:
                            grilla_feromonas[f][c] = 0.0

        # Renderizado Simulación
        pantalla.fill(COLOR_VACIO)
        for f in range(FILAS):
            for c in range(COLUMNAS):
                x = c * FACTOR_SEPARACION
                y = f * FACTOR_SEPARACION
                rect = pygame.Rect(x, y, FACTOR_SEPARACION, FACTOR_SEPARACION)
                
                valor = grilla_actual[f][c]
                if valor == 5:
                    pygame.draw.rect(pantalla, COLOR_PARED, rect)
                elif valor == 3:
                    pygame.draw.rect(pantalla, COLOR_NIDO, rect)
                elif valor == 4:
                    pygame.draw.rect(pantalla, COLOR_COMIDA, rect)
                else:
                    feno = grilla_feromonas[f][c]
                    if feno > 0.0:
                        alfa_color = (int(20 * feno), int(50 * feno), int(160 * feno))
                        pygame.draw.rect(pantalla, alfa_color, rect)
                    
                    if valor == 1:
                        dibujar_hormiga(pantalla, COLOR_BUSCANDO, f, c, grilla_direcciones[f][c])
                    elif valor == 2:
                        dibujar_hormiga(pantalla, COLOR_CARGADA, f, c, grilla_direcciones[f][c])
                        
        pygame.display.flip()