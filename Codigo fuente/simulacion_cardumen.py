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
TIEMPO_TURNO = 0.15     
CANTIDAD_PECES = 160    # 10% de una grilla de 40x40 por defecto

# Colores (RGB)
COLOR_FONDO = (11, 19, 43)      # Azul océano oscuro
COLOR_PEZ = (0, 180, 216)       # Celeste brillante
COLOR_TEXTO = (255, 255, 255)
COLOR_INPUT_ACTIVO = (0, 180, 216)
COLOR_INPUT_INACTIVO = (70, 90, 120)
COLOR_BOTON = (40, 167, 69)     # Verde para Start

# Vectores de movimiento
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

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def inicializar_simulacion(tamano, total_peces):
    """Genera la grilla y posiciona la cantidad exacta de peces ingresada."""
    global grilla_actual
    grilla_actual = [[0 for _ in range(tamano)] for _ in range(tamano)]
    
    posiciones_libres = [(f, c) for f in range(tamano) for c in range(tamano)]
    
    # Fisher-Yates Shuffle para mezclar posiciones de manera aleatoria
    for i in range(len(posiciones_libres)):
        random_index = random.randint(i, len(posiciones_libres) - 1)
        posiciones_libres[i], posiciones_libres[random_index] = posiciones_libres[random_index], posiciones_libres[i]
        
    # Limitar la cantidad de peces al máximo de celdas disponibles para evitar bucles infinitos
    total_celdas = tamano * tamano
    peces_a_colocar = min(total_peces, total_celdas)
    
    for i in range(peces_a_colocar):
        f, c = posiciones_libres[i]
        dir_aleatoria = random.randint(1, 8)
        grilla_actual[f][c] = dir_aleatoria

def conseguir_moda(lista):
    if not lista: return None
    conteo = {}
    for item in lista:
        conteo[item] = conteo.get(item, 0) + 1
    moda = lista[0]
    max_conteo = 0
    for key, val in conteo.items():
        if val > max_conteo:
            max_conteo = val
            moda = key
    return moda

def dibujar_pez(pantalla, color, f, c, direccion_idx, factor_sep):
    centro_x = c * factor_sep + factor_sep // 2
    centro_y = f * factor_sep + factor_sep // 2
    radio = factor_sep // 2
    
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
        # Calcular dinámicamente la densidad resultante en tiempo real
        try:
            g_temp = int(input_grilla_texto) if input_grilla_texto else 0
            p_temp = int(input_peces_texto) if input_peces_texto else 0
            total_celdas = g_temp ** 2
            
            if total_celdas > 0:
                # Evitar que la densidad supere el 100% en el texto informativo
                p_temp = min(p_temp, total_celdas)
                densidad_calculada = (p_temp / total_celdas) * 100
            else:
                densidad_calculada = 0.0
        except ValueError:
            densidad_calculada = 0.0

        # Definición de Rectángulos para interacción (Inputs y Botón)
        rect_grilla = pygame.Rect(280, 150, 140, 40)
        rect_peces = pygame.Rect(280, 220, 140, 40)
        rect_boton_start = pygame.Rect(200, 370, 200, 50)

        # Manejo de Eventos en el Menú
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if evento.type == pygame.MOUSEBUTTONDOWN:
                # Detectar si se hace click en los inputs
                if rect_grilla.collidepoint(evento.pos):
                    activo_grilla = True
                    activo_peces = False
                elif rect_peces.collidepoint(evento.pos):
                    activo_peces = True
                    activo_grilla = False
                else:
                    activo_grilla = False
                    activo_peces = False
                
                # Detectar si se hace click en el botón START
                if rect_boton_start.collidepoint(evento.pos):
                    try:
                        TAMANO_GRILLA = max(5, int(input_grilla_texto)) # Grilla mínima de 5x5
                        CANTIDAD_PECES = max(0, int(input_peces_texto))
                    except ValueError:
                        # Si hay valores corruptos, usa los valores por defecto
                        TAMANO_GRILLA = 40
                        CANTIDAD_PECES = 160

                    # Inicializar datos y ajustar dinámicamente el tamaño de ventana a la grilla
                    inicializar_simulacion(TAMANO_GRILLA, CANTIDAD_PECES)
                    VENTANA_TAMANO = TAMANO_GRILLA * FACTOR_SEPARACION
                    pantalla = pygame.display.set_mode((VENTANA_TAMANO, VENTANA_TAMANO))
                    pygame.display.set_caption("Simulación de Cardumen Puro")
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
                    elif evento.unicode.isdigit() and len(input_peces_texto) < 5: # Permite números grandes
                        input_peces_texto += evento.unicode

        # Renderizado del Menú
        pantalla.fill(COLOR_FONDO)
        
        # Título
        txt_titulo = fuente.render("CONFIGURACIÓN DE PARÁMETROS", True, COLOR_TEXTO)
        pantalla.blit(txt_titulo, (110, 50))
        
        # Input 1: Tamaño de Grilla
        txt_g = fuente.render("Tamaño Grilla (NxN):", True, COLOR_TEXTO)
        pantalla.blit(txt_g, (50, 155))
        col_g = COLOR_INPUT_ACTIVO if activo_grilla else COLOR_INPUT_INACTIVO
        pygame.draw.rect(pantalla, col_g, rect_grilla, 2)
        txt_g_val = fuente.render(input_grilla_texto, True, COLOR_TEXTO)
        pantalla.blit(txt_g_val, (290, 155))
        
        # Input 2: Cantidad de Peces
        txt_p = fuente.render("Cantidad de Peces:", True, COLOR_TEXTO)
        pantalla.blit(txt_p, (50, 225))
        col_p = COLOR_INPUT_ACTIVO if activo_peces else COLOR_INPUT_INACTIVO
        pygame.draw.rect(pantalla, col_p, rect_peces, 2)
        txt_p_val = fuente.render(input_peces_texto, True, COLOR_TEXTO)
        pantalla.blit(txt_p_val, (290, 225))

        # Indicador informativo: Densidad calculada en base a lo que escribes
        txt_d = fuente.render(f"Densidad de la Grilla: {densidad_calculada:.1f}%", True, COLOR_PEZ)
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

        # Avance generacional por turnos discretos
        if tiempo_acumulado >= TIEMPO_TURNO:
            tiempo_acumulado = 0.0
            nueva_grilla = [[0 for _ in range(TAMANO_GRILLA)] for _ in range(TAMANO_GRILLA)]
            
            for f in range(TAMANO_GRILLA):
                for c in range(TAMANO_GRILLA):
                    dir_actual = grilla_actual[f][c]
                    if dir_actual == 0: 
                        continue

                    # Vecindad de Moore Toroidal
                    direcciones_vecinos = []
                    for df in range(-1, 2):
                        for dc in range(-1, 2):
                            if df == 0 and dc == 0: 
                                continue
                            vf = (f + df + TAMANO_GRILLA) % TAMANO_GRILLA
                            vc = (c + dc + TAMANO_GRILLA) % TAMANO_GRILLA
                            if grilla_actual[vf][vc] > 0:
                                direcciones_vecinos.append(grilla_actual[vf][vc])
                    
                    # Regla de Alineación
                    dir_deseada = dir_actual
                    if direcciones_vecinos and random.random() < 0.7:
                        dir_deseada = conseguir_moda(direcciones_vecinos)
                    
                    # Calcular destino
                    paso = DIRECCIONES[dir_deseada]
                    destino_f = (f + paso[0] + TAMANO_GRILLA) % TAMANO_GRILLA
                    destino_c = (c + paso[1] + TAMANO_GRILLA) % TAMANO_GRILLA
                    
                    # Regla de Separación / Movimiento
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
                    dibujar_pez(pantalla, COLOR_PEZ, f, c, valor, FACTOR_SEPARACION)
                    
        pygame.display.flip()