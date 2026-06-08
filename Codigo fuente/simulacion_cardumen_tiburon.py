import pygame
import random
import sys
import math

# Inicialización de Pygame
pygame.init()
pygame.font.init()

# =============================================================================
# CONFIGURACIÓN INICIAL (Valores por defecto)
# =============================================================================
TAMANO_GRILLA = 40
FACTOR_SEPARACION = 15  # Tamaño en píxeles de cada celda
TIEMPO_TURNO = 0.15      # Segundos por turno
CANTIDAD_PECES = 160    # 10% de la grilla por defecto

# Colores (RGB)
COLOR_FONDO = (10, 25, 47)      # Azul océano profundo
COLOR_PEZ = (64, 224, 208)       # Turquesa
COLOR_TIBURON = (255, 69, 0)     # Rojo/Naranja brillante
COLOR_TEXTO = (255, 255, 255)
COLOR_INPUT_ACTIVO = (64, 224, 208)
COLOR_INPUT_INACTIVO = (70, 90, 120)
COLOR_BOTON = (40, 167, 69)     

# Mapeo de direcciones
DIRECCIONES = [
    (0, 0),    # 0: Vacío
    (-1, 0),   # 1: Norte
    (-1, 1),   # 2: Noreste
    (0, 1),    # 3: Este
    (1, 1),    # 4: Sureste
    (1, 0),    # 5: Sur
    (1, -1),   # 6: Suroeste
    (0, -1),   # 7: Oeste
    (-1, -1)   # 8: Noroeste
]

# Configuración de la ventana inicial fija para el menú
VENTANA_ANCHO = 600
VENTANA_ALTO = 600
pantalla = pygame.display.set_mode((VENTANA_ANCHO, VENTANA_ALTO))
pygame.display.set_caption("Configuración de Simulación")
reloj = pygame.time.Clock()
fuente = pygame.font.SysFont("Arial", 24)

# Variables de control para los Inputs del Menú
input_grilla_texto = str(TAMANO_GRILLA)
input_peces_texto = str(CANTIDAD_PECES)
activo_grilla = False
activo_peces = False

# Estados del juego: 'MENU' o 'SIMULACION'
estado_actual = 'MENU'
grilla_actual = []
posicion_tiburon = (0, 0)
vieja_posicion_tiburon = (0, 0)
ultima_dir_tiburon = 3  # Inercia inicial (Este)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def inicializar_simulacion(tamano, total_peces):
    """Genera la grilla, posiciona al tiburón y la cantidad de peces."""
    global grilla_actual, posicion_tiburon, ultima_dir_tiburon, vieja_posicion_tiburon
    
    grilla_actual = [[0 for _ in range(tamano)] for _ in range(tamano)]
    posiciones_libres = [(f, c) for f in range(tamano) for c in range(tamano)]
    
    # Mezclado aleatorio
    for i in range(len(posiciones_libres)):
        random_index = random.randint(i, len(posiciones_libres) - 1)
        posiciones_libres[i], posiciones_libres[random_index] = posiciones_libres[random_index], posiciones_libres[i]
        
    # 1. Instanciar al TIBURÓN
    posicion_tiburon = posiciones_libres[0]
    vieja_posicion_tiburon = posicion_tiburon
    grilla_actual[posicion_tiburon[0]][posicion_tiburon[1]] = 9
    ultima_dir_tiburon = random.randint(1, 8)
    
    # 2. Instanciar los Peces
    total_celdas = tamano * tamano
    peces_a_colocar = min(total_peces, total_celdas - 1) # -1 dejando espacio al tiburón
    
    for i in range(1, peces_a_colocar + 1):
        f, c = posiciones_libres[i]
        dir_aleatoria = random.randint(1, 8)
        grilla_actual[f][c] = dir_aleatoria

def conseguir_moda(lista):
    if not lista: return None
    conteo = {}
    for item in lista: conteo[item] = conteo.get(item, 0) + 1
    moda = lista[0]
    max_conteo = 0
    for key, val in conteo.items():
        if val > max_conteo: max_conteo = val; moda = key
    return moda

def dibujar_triangulo(pantalla, color, f, c, direccion_idx, factor_sep):
    centro_x = c * factor_sep + factor_sep // 2
    centro_y = f * factor_sep + factor_sep // 2
    radio = factor_sep // 2
    
    if direccion_idx == 9:
        radio = int(factor_sep * 0.7)
        paso = DIRECCIONES[ultima_dir_tiburon]
    else:
        paso = DIRECCIONES[direccion_idx]
        
    angulo = math.atan2(-paso[0], paso[1])
    
    p1 = (centro_x + radio * math.cos(angulo), centro_y - radio * math.sin(angulo))
    p2 = (centro_x + radio * 0.5 * math.cos(angulo + 2.5), centro_y - radio * 0.5 * math.sin(angulo + 2.5))
    p3 = (centro_x + radio * 0.5 * math.cos(angulo - 2.5), centro_y - radio * 0.5 * math.sin(angulo - 2.5))
    
    pygame.draw.polygon(pantalla, color, [p1, p2, p3])

# =============================================================================
# BUCLE PRINCIPAL
# =============================================================================
tiempo_acumulado = 0.0

while True:
    dt = reloj.tick(60) / 1000.0
    
    # --- ESTADO: MENÚ DE CONFIGURACIÓN ---
    if estado_actual == 'MENU':
        try:
            g_temp = int(input_grilla_texto) if input_grilla_texto else 0
            p_temp = int(input_peces_texto) if input_peces_texto else 0
            total_celdas = g_temp ** 2
            densidad_calculada = (min(p_temp, total_celdas) / total_celdas * 100) if total_celdas > 0 else 0.0
        except ValueError:
            densidad_calculada = 0.0

        rect_grilla = pygame.Rect(280, 150, 140, 40)
        rect_peces = pygame.Rect(280, 220, 140, 40)
        rect_boton_start = pygame.Rect(200, 370, 200, 50)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if evento.type == pygame.MOUSEBUTTONDOWN:
                activo_grilla = rect_grilla.collidepoint(evento.pos)
                activo_peces = rect_peces.collidepoint(evento.pos)
                
                if rect_boton_start.collidepoint(evento.pos):
                    try:
                        TAMANO_GRILLA = max(5, int(input_grilla_texto))
                        CANTIDAD_PECES = max(0, int(input_peces_texto))
                    except ValueError:
                        TAMANO_GRILLA = 40
                        CANTIDAD_PECES = 160

                    inicializar_simulacion(TAMANO_GRILLA, CANTIDAD_PECES)
                    VENTANA_TAMANO = TAMANO_GRILLA * FACTOR_SEPARACION
                    pantalla = pygame.display.set_mode((VENTANA_TAMANO, VENTANA_TAMANO))
                    pygame.display.set_caption("Simulación de Cardumen y Depredador")
                    estado_actual = 'SIMULACION'

            if evento.type == pygame.KEYDOWN:
                if activo_grilla:
                    if evento.key == pygame.K_BACKSPACE:
                        input_grilla_texto = input_grilla_texto[:-1]
                    elif evento.unicode.isdigit() and len(input_grilla_texto) < 3:
                        input_grilla_texto += evento.unicode
                elif activo_peces:
                    if evento.key == pygame.K_BACKSPACE:
                        input_peces_texto = input_peces_texto[:-1]
                    elif evento.unicode.isdigit() and len(input_peces_texto) < 5:
                        input_peces_texto += evento.unicode

        pantalla.fill(COLOR_FONDO)
        txt_titulo = fuente.render("CONFIGURACIÓN DE PARÁMETROS", True, COLOR_TEXTO)
        pantalla.blit(txt_titulo, (110, 50))
        
        # UI Grilla
        txt_g = fuente.render("Tamaño Grilla (NxN):", True, COLOR_TEXTO)
        pantalla.blit(txt_g, (50, 155))
        pygame.draw.rect(pantalla, COLOR_INPUT_ACTIVO if activo_grilla else COLOR_INPUT_INACTIVO, rect_grilla, 2)
        pantalla.blit(fuente.render(input_grilla_texto, True, COLOR_TEXTO), (290, 155))
        
        # UI Peces
        txt_p = fuente.render("Cantidad de Peces:", True, COLOR_TEXTO)
        pantalla.blit(txt_p, (50, 225))
        pygame.draw.rect(pantalla, COLOR_INPUT_ACTIVO if activo_peces else COLOR_INPUT_INACTIVO, rect_peces, 2)
        pantalla.blit(fuente.render(input_peces_texto, True, COLOR_TEXTO), (290, 225))

        # UI Densidad Informativa
        txt_d = fuente.render(f"Densidad de la Grilla: {densidad_calculada:.1f}%", True, COLOR_INPUT_ACTIVO)
        pantalla.blit(txt_d, (50, 295))
        
        # Botón Start
        pygame.draw.rect(pantalla, COLOR_BOTON, rect_boton_start, border_radius=5)
        txt_btn = fuente.render("START", True, COLOR_TEXTO)
        pantalla.blit(txt_btn, (265, 380))
        pygame.display.flip()

    # --- ESTADO: EJECUCIÓN DE LA SIMULACIÓN ---
    elif estado_actual == 'SIMULACION':
        tiempo_acumulado += dt

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if tiempo_acumulado >= TIEMPO_TURNO:
            tiempo_acumulado = 0.0
            nueva_grilla = [[0 for _ in range(TAMANO_GRILLA)] for _ in range(TAMANO_GRILLA)]
            
            # ----------------------------------------------------
            # 1. LÓGICA DEL DEPREDADOR (CON INERCIA)
            # ----------------------------------------------------
            dir_tiburon = ultima_dir_tiburon
            if random.random() < 0.2:
                giro = 1 if random.random() < 0.5 else -1
                dir_tiburon = ultima_dir_tiburon + giro
                if dir_tiburon > 8: dir_tiburon = 1
                if dir_tiburon < 1: dir_tiburon = 8
                
            ultima_dir_tiburon = dir_tiburon
            paso_tiburon = DIRECCIONES[dir_tiburon]
            
            n_tiburon_f = (posicion_tiburon[0] + paso_tiburon[0] + TAMANO_GRILLA) % TAMANO_GRILLA
            n_tiburon_c = (posicion_tiburon[1] + paso_tiburon[1] + TAMANO_GRILLA) % TAMANO_GRILLA
            
            nueva_grilla[n_tiburon_f][n_tiburon_c] = 9
            vieja_posicion_tiburon = posicion_tiburon
            posicion_tiburon = (n_tiburon_f, n_tiburon_c)
            
            # ----------------------------------------------------
            # 2. LÓGICA DE LOS PECES
            # ----------------------------------------------------
            for f in range(TAMANO_GRILLA):
                for c in range(TAMANO_GRILLA):
                    dir_actual = grilla_actual[f][c]
                    if dir_actual == 0 or dir_actual == 9:
                        continue
                    
                    amenaza_detectada = False
                    pos_amenaza = (0, 0)
                    direcciones_vecinos = []
                    
                    # Escaneo Toroidal
                    for df in range(-1, 2):
                        for dc in range(-1, 2):
                            if df == 0 and dc == 0: continue
                            
                            vf = (f + df + TAMANO_GRILLA) % TAMANO_GRILLA
                            vc = (c + dc + TAMANO_GRILLA) % TAMANO_GRILLA
                            
                            if grilla_actual[vf][vc] == 9 or (vf == vieja_posicion_tiburon[0] and vc == vieja_posicion_tiburon[1]):
                                amenaza_detectada = True
                                pos_amenaza = (vf, vc)
                            elif 1 <= grilla_actual[vf][vc] <= 8:
                                direcciones_vecinos.append(grilla_actual[vf][vc])
                    
                    dir_deseada = dir_actual
                    
                    if amenaza_detectada:
                        # Vector de huida opuesto corregido toroidalmente
                        diff_f = f - pos_amenaza[0]
                        diff_c = c - pos_amenaza[1]
                        
                        if diff_f > TAMANO_GRILLA // 2: diff_f -= TAMANO_GRILLA
                        elif diff_f < -TAMANO_GRILLA // 2: diff_f += TAMANO_GRILLA
                        if diff_c > TAMANO_GRILLA // 2: diff_c -= TAMANO_GRILLA
                        elif diff_c < -TAMANO_GRILLA // 2: diff_c += TAMANO_GRILLA
                        
                        h_f = 1 if diff_f > 0 else (-1 if diff_f < 0 else 0)
                        h_c = 1 if diff_c > 0 else (-1 if diff_c < 0 else 0)
                        
                        for i in range(1, 9):
                            if DIRECCIONES[i][0] == h_f and DIRECCIONES[i][1] == h_c:
                                dir_deseada = i
                                break
                    elif direcciones_vecinos and random.random() < 0.7:
                        dir_deseada = conseguir_moda(direcciones_vecinos)
                    
                    paso = DIRECCIONES[dir_deseada]
                    destino_f = (f + paso[0] + TAMANO_GRILLA) % TAMANO_GRILLA
                    destino_c = (c + paso[1] + TAMANO_GRILLA) % TAMANO_GRILLA
                    
                    if nueva_grilla[destino_f][destino_c] == 0:
                        nueva_grilla[destino_f][destino_c] = dir_deseada
                    else:
                        dir_azar = random.randint(1, 8)
                        if nueva_grilla[f][c] == 0:
                            nueva_grilla[f][c] = dir_azar
                        else:
                            pass
                            
            grilla_actual = nueva_grilla

        # Renderizado de la simulación
        pantalla.fill(COLOR_FONDO)
        for f in range(TAMANO_GRILLA):
            for c in range(TAMANO_GRILLA):
                valor = grilla_actual[f][c]
                if 1 <= valor <= 8:
                    dibujar_triangulo(pantalla, COLOR_PEZ, f, c, valor, FACTOR_SEPARACION)
                elif valor == 9:
                    dibujar_triangulo(pantalla, COLOR_TIBURON, f, c, 9, FACTOR_SEPARACION)
                    
        pygame.display.flip()