import pygame
import sys
import os
import math
import random

# Inicializar Pygame
pygame.init()

# Configuración de colores (RGB)
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    CYAN = (0, 255, 255)
    RED = (255, 107, 107)
    DARK_BLUE = (15, 15, 35)
    BLUE_GRAY = (26, 26, 62)
    GRAY = (170, 170, 170)
    GREEN = (50, 205, 50)
    ORANGE = (255, 165, 0)

class PongGame:
    def __init__(self):
        # Configuración de pantalla
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 400
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Pong Arcade - Pong Kenny")
        
        # Reloj para controlar FPS
        self.clock = pygame.time.Clock()
        self.FPS = 60
        
        # Configuración de fuentes - Compatible con PyInstaller
        try:
            # Determinar la ruta base (funciona tanto en desarrollo como en ejecutable)
            if hasattr(sys, '_MEIPASS'):
                # Ruta cuando está empaquetado con PyInstaller
                base_path = sys._MEIPASS
            else:
                # Ruta cuando se ejecuta como script normal
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            # Intentar cargar una fuente personalizada (opcional)
            font_path = os.path.join(base_path, 'assets', 'font.ttf')
            if os.path.exists(font_path):
                self.font_large = pygame.font.Font(font_path, 36)
                self.font_medium = pygame.font.Font(font_path, 24)
                self.font_small = pygame.font.Font(font_path, 18)
            else:
                # Usar fuente por defecto del sistema
                self.font_large = pygame.font.Font(None, 36)
                self.font_medium = pygame.font.Font(None, 24)
                self.font_small = pygame.font.Font(None, 18)
        except Exception:
            # Si hay algún error, usar fuente por defecto
            self.font_large = pygame.font.Font(None, 36)
            self.font_medium = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
        
        # Estado del juego
        self.game_state = "difficulty_menu"  # difficulty_menu, waiting, playing, paused, game_over
        self.player_score = 0
        self.cpu_score = 0
        self.max_score = 5
        
        # Dificultad
        self.difficulty = None  # 'easy', 'medium', 'hard'
        self.selected_difficulty = 0  # 0: Fácil, 1: Medio, 2: Difícil
        
        # Controles
        self.keys = pygame.key.get_pressed()
        
        # Inicializar objetos del juego
        self.init_game_objects()
        
        # Sonidos (placeholder)
        self.sounds = {
            'paddle': None,
            'wall': None,
            'score': None
        }
        
        # Power-ups
        self.powerups = []
        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = 600  # MODIFICAR AQUÍ: Cada cuántos frames aparece un power-up (600 = 10 segundos a 60 FPS)
        
        # Estados de power-ups activos
        self.player_frozen = False
        self.player_frozen_timer = 0
        self.player_frozen_duration = 180  # MODIFICAR AQUÍ: Duración del congelamiento en frames (180 = 3 segundos a 60 FPS)
        
        self.cpu_frozen = False
        self.cpu_frozen_timer = 0
        self.cpu_frozen_duration = 180  # MODIFICAR AQUÍ: Duración del congelamiento en frames (180 = 3 segundos a 60 FPS)
        
        self.multi_ball_active = False
        self.multi_ball_timer = 0
        self.multi_ball_duration = 600  # MODIFICAR AQUÍ: Duración de pelotas múltiples en frames (600 = 10 segundos a 60 FPS)
        self.extra_balls = []  # Lista de pelotas adicionales
        self.multi_ball_count = 2  # MODIFICAR AQUÍ: Número de pelotas adicionales (2 o 3)
        
    def set_difficulty(self, difficulty):
        """Configura la dificultad del juego"""
        self.difficulty = difficulty
        
        if difficulty == 'easy':
            self.cpu['speed'] = 6
            self.cpu['reaction_delay'] = 10
            self.cpu['prediction'] = 1
        elif difficulty == 'medium':
            self.cpu['speed'] = 9
            self.cpu['reaction_delay'] = 5
            self.cpu['prediction'] = 2
        elif difficulty == 'hard':
            self.cpu['speed'] = 12
            self.cpu['reaction_delay'] = 1
            self.cpu['prediction'] = 4
        
    def init_game_objects(self):
        # Paleta del jugador
        self.player = {
            'x': 20,
            'y': self.SCREEN_HEIGHT // 2 - 50,
            'width': 10,
            'height': 100,
            'speed': 5,
            'color': Colors.CYAN
        }
        
        # Paleta de la CPU
        self.cpu = {
            'x': self.SCREEN_WIDTH - 30,
            'y': self.SCREEN_HEIGHT // 2 - 50,
            'width': 10,
            'height': 100,
            'speed': 3,
            'color': Colors.RED,
            'reaction_delay': 10,
            'prediction': 0.5
        }
        
        # Pelota
        self.ball = {
            'x': self.SCREEN_WIDTH // 2,
            'y': self.SCREEN_HEIGHT // 2,
            'radius': 8,
            'speed_x': 5,
            'speed_y': 4,
            'color': Colors.WHITE,
            'trail': [],
            'max_speed': 12
        }
        
        self.reset_ball()
        
    def reset_ball(self):
        self.ball['x'] = self.SCREEN_WIDTH // 2
        self.ball['y'] = self.SCREEN_HEIGHT // 2
        self.ball['speed_x'] = random.choice([5, -5])
        self.ball['speed_y'] = random.uniform(-4, 4)
        self.ball['trail'] = []
    
    def spawn_powerup(self):
        """Activa un power-up aleatorio automáticamente"""
        powerup_types = ['freeze_player', 'freeze_cpu', 'multi_ball']
        
        # Seleccionar y activar un power-up aleatorio
        selected_powerup = random.choice(powerup_types)
        self.activate_powerup(selected_powerup)
    
    def activate_powerup(self, powerup_type):
        """Activa un power-up específico"""
        if powerup_type == 'freeze_player':
            self.player_frozen = True
            self.player_frozen_timer = self.player_frozen_duration
        elif powerup_type == 'freeze_cpu':
            self.cpu_frozen = True
            self.cpu_frozen_timer = self.cpu_frozen_duration
        elif powerup_type == 'multi_ball':
            if not self.multi_ball_active:
                self.multi_ball_active = True
                self.multi_ball_timer = self.multi_ball_duration
                # Crear pelotas adicionales
                self.extra_balls = []
                for i in range(self.multi_ball_count):
                    new_ball = self.ball.copy()
                    new_ball['speed_x'] = random.choice([5, -5]) * random.uniform(0.8, 1.2)
                    new_ball['speed_y'] = random.uniform(-5, 5)
                    new_ball['trail'] = []
                    self.extra_balls.append(new_ball)
    
    def check_powerup_collision(self):
        """Verifica si la pelota toca un power-up"""
        for powerup in self.powerups[:]:
            distance = math.sqrt((self.ball['x'] - powerup['x'])**2 + (self.ball['y'] - powerup['y'])**2)
            if distance < self.ball['radius'] + powerup['radius']:
                self.activate_powerup(powerup['type'])
                self.powerups.remove(powerup)
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                # Menú de dificultad
                if self.game_state == "difficulty_menu":
                    if event.key == pygame.K_UP:
                        self.selected_difficulty = (self.selected_difficulty - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        self.selected_difficulty = (self.selected_difficulty + 1) % 3
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        difficulties = ['easy', 'medium', 'hard']
                        self.set_difficulty(difficulties[self.selected_difficulty])
                        self.game_state = "waiting"
                
                # Juego normal
                elif event.key == pygame.K_SPACE:
                    self.toggle_pause()
                elif event.key == pygame.K_r:
                    self.reset_game()
                    
        return True
        
    def update(self):
        if self.game_state != "playing":
            return
            
        # Actualizar controles
        self.keys = pygame.key.get_pressed()
        
        # Actualizar timers de power-ups
        if self.player_frozen:
            self.player_frozen_timer -= 1
            if self.player_frozen_timer <= 0:
                self.player_frozen = False
        
        if self.cpu_frozen:
            self.cpu_frozen_timer -= 1
            if self.cpu_frozen_timer <= 0:
                self.cpu_frozen = False
        
        if self.multi_ball_active:
            self.multi_ball_timer -= 1
            if self.multi_ball_timer <= 0:
                self.multi_ball_active = False
                self.extra_balls = []
        
        # Spawn de power-ups automático cada 10 segundos
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer >= self.powerup_spawn_interval:
            self.spawn_powerup()
            self.powerup_spawn_timer = 0
        
        # Movimiento del jugador (solo si no está congelado)
        if not self.player_frozen:
            if self.keys[pygame.K_UP] and self.player['y'] > 0:
                self.player['y'] -= self.player['speed']
            if self.keys[pygame.K_DOWN] and self.player['y'] < self.SCREEN_HEIGHT - self.player['height']:
                self.player['y'] += self.player['speed']
            
        # IA de la CPU mejorada con predicción (solo si no está congelado)
        if not self.cpu_frozen:
            cpu_center = self.cpu['y'] + self.cpu['height'] // 2
            
            # Predecir posición futura de la pelota
            if self.ball['speed_x'] > 0:  # Pelota viene hacia CPU
                frames_to_reach = (self.cpu['x'] - self.ball['x']) / self.ball['speed_x']
                predicted_y = self.ball['y'] + (self.ball['speed_y'] * frames_to_reach * self.cpu['prediction'])
                
                # Ajustar predicción por rebotes en bordes
                while predicted_y < 0 or predicted_y > self.SCREEN_HEIGHT:
                    if predicted_y < 0:
                        predicted_y = abs(predicted_y)
                    elif predicted_y > self.SCREEN_HEIGHT:
                        predicted_y = self.SCREEN_HEIGHT - (predicted_y - self.SCREEN_HEIGHT)
                
                target_y = predicted_y
            else:
                target_y = self.SCREEN_HEIGHT // 2  # Volver al centro
            
            # Mover CPU hacia la posición objetivo
            reaction_distance = self.cpu['reaction_delay'] * 15
            if abs(self.ball['x'] - self.cpu['x']) < reaction_distance or self.ball['speed_x'] > 0:
                tolerance = 15
                if cpu_center < target_y - tolerance:
                    self.cpu['y'] += self.cpu['speed']
                elif cpu_center > target_y + tolerance:
                    self.cpu['y'] -= self.cpu['speed']
            
        # Mantener CPU en pantalla
        if self.cpu['y'] < 0:
            self.cpu['y'] = 0
        if self.cpu['y'] > self.SCREEN_HEIGHT - self.cpu['height']:
            self.cpu['y'] = self.SCREEN_HEIGHT - self.cpu['height']
            
        # Movimiento de la pelota principal
        self.ball['x'] += self.ball['speed_x']
        self.ball['y'] += self.ball['speed_y']
        
        # Agregar trail a la pelota
        self.ball['trail'].append((self.ball['x'], self.ball['y']))
        if len(self.ball['trail']) > 10:
            self.ball['trail'].pop(0)
            
        # Colisiones con bordes superior e inferior
        if (self.ball['y'] - self.ball['radius'] <= 0 or 
            self.ball['y'] + self.ball['radius'] >= self.SCREEN_HEIGHT):
            self.ball['speed_y'] = -self.ball['speed_y']
            
        # Colisiones con paletas
        self.check_paddle_collisions()
        
        # Actualizar pelotas adicionales
        for extra_ball in self.extra_balls[:]:
            extra_ball['x'] += extra_ball['speed_x']
            extra_ball['y'] += extra_ball['speed_y']
            
            # Trail de pelotas extras
            extra_ball['trail'].append((extra_ball['x'], extra_ball['y']))
            if len(extra_ball['trail']) > 10:
                extra_ball['trail'].pop(0)
            
            # Colisiones con bordes
            if (extra_ball['y'] - extra_ball['radius'] <= 0 or 
                extra_ball['y'] + extra_ball['radius'] >= extra_ball['radius']):
                extra_ball['speed_y'] = -extra_ball['speed_y']
            
            # Colisiones con paletas para pelotas extras
            self.check_paddle_collisions_extra(extra_ball)
            
            # Verificar puntos con pelotas extras
            if extra_ball['x'] < 0:
                self.cpu_score += 1
                self.extra_balls.remove(extra_ball)
            elif extra_ball['x'] > self.SCREEN_WIDTH:
                self.player_score += 1
                self.extra_balls.remove(extra_ball)
        
        # Verificar puntos
        if self.ball['x'] < 0:
            self.cpu_score += 1
            self.reset_ball()
            
        if self.ball['x'] > self.SCREEN_WIDTH:
            self.player_score += 1
            self.reset_ball()
            
        # Verificar fin de juego
        if self.player_score >= self.max_score or self.cpu_score >= self.max_score:
            self.game_state = "game_over"
            
    def check_paddle_collisions(self):
        ball_rect = pygame.Rect(
            self.ball['x'] - self.ball['radius'],
            self.ball['y'] - self.ball['radius'],
            self.ball['radius'] * 2,
            self.ball['radius'] * 2
        )
        
        player_rect = pygame.Rect(
            self.player['x'],
            self.player['y'],
            self.player['width'],
            self.player['height']
        )
        
        cpu_rect = pygame.Rect(
            self.cpu['x'],
            self.cpu['y'],
            self.cpu['width'],
            self.cpu['height']
        )
        
        # Colisión con paleta del jugador
        if ball_rect.colliderect(player_rect) and self.ball['speed_x'] < 0:
            self.ball['speed_x'] = abs(self.ball['speed_x']) * 1.05  # Acelerar ligeramente
            
            # Calcular ángulo basado en dónde golpeó
            hit_pos = (self.ball['y'] - self.player['y']) / self.player['height']
            self.ball['speed_y'] = (hit_pos - 0.5) * 10
            
            # Limitar velocidad máxima
            if abs(self.ball['speed_x']) > self.ball['max_speed']:
                self.ball['speed_x'] = self.ball['max_speed'] if self.ball['speed_x'] > 0 else -self.ball['max_speed']
            
        # Colisión con paleta de la CPU
        if ball_rect.colliderect(cpu_rect) and self.ball['speed_x'] > 0:
            self.ball['speed_x'] = -abs(self.ball['speed_x']) * 1.05  # Acelerar ligeramente
            
            # Calcular ángulo basado en dónde golpeó
            hit_pos = (self.ball['y'] - self.cpu['y']) / self.cpu['height']
            self.ball['speed_y'] = (hit_pos - 0.5) * 10
            
            # Limitar velocidad máxima
            if abs(self.ball['speed_x']) > self.ball['max_speed']:
                self.ball['speed_x'] = self.ball['max_speed'] if self.ball['speed_x'] > 0 else -self.ball['max_speed']
    
    def check_paddle_collisions_extra(self, ball):
        """Verifica colisiones para pelotas adicionales"""
        ball_rect = pygame.Rect(
            ball['x'] - ball['radius'],
            ball['y'] - ball['radius'],
            ball['radius'] * 2,
            ball['radius'] * 2
        )
        
        player_rect = pygame.Rect(
            self.player['x'],
            self.player['y'],
            self.player['width'],
            self.player['height']
        )
        
        cpu_rect = pygame.Rect(
            self.cpu['x'],
            self.cpu['y'],
            self.cpu['width'],
            self.cpu['height']
        )
        
        if ball_rect.colliderect(player_rect) and ball['speed_x'] < 0:
            ball['speed_x'] = abs(ball['speed_x']) * 1.05
            hit_pos = (ball['y'] - self.player['y']) / self.player['height']
            ball['speed_y'] = (hit_pos - 0.5) * 10
            
        if ball_rect.colliderect(cpu_rect) and ball['speed_x'] > 0:
            ball['speed_x'] = -abs(ball['speed_x']) * 1.05
            hit_pos = (ball['y'] - self.cpu['y']) / self.cpu['height']
            ball['speed_y'] = (hit_pos - 0.5) * 10
            
    def draw_glow_rect(self, surface, color, rect, glow_size=5):
        """Dibuja un rectángulo con efecto de resplandor"""
        # Crear superficie para el resplandor
        glow_surf = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2))
        glow_surf.set_alpha(50)
        glow_surf.fill(color)
        
        # Dibujar el resplandor
        surface.blit(glow_surf, (rect.x - glow_size, rect.y - glow_size))
        
        # Dibujar el rectángulo principal
        pygame.draw.rect(surface, color, rect)
        
    def draw_glow_circle(self, surface, color, center, radius, glow_size=10):
        """Dibuja un círculo con efecto de resplandor"""
        # Dibujar círculos concéntricos para el efecto de resplandor
        for i in range(glow_size, 0, -1):
            alpha = 20 - (i * 2)
            if alpha > 0:
                glow_surf = pygame.Surface((radius * 2 + i * 2, radius * 2 + i * 2))
                glow_surf.set_alpha(alpha)
                pygame.draw.circle(glow_surf, color, (radius + i, radius + i), radius + i)
                surface.blit(glow_surf, (center[0] - radius - i, center[1] - radius - i))
        
        # Dibujar el círculo principal
        pygame.draw.circle(surface, color, center, radius)
    
    def render_difficulty_menu(self):
        """Renderiza el menú de selección de dificultad"""
        # Fondo con gradiente
        for y in range(self.SCREEN_HEIGHT):
            color_ratio = y / self.SCREEN_HEIGHT
            r = int(Colors.DARK_BLUE[0] * (1 - color_ratio) + Colors.BLUE_GRAY[0] * color_ratio)
            g = int(Colors.DARK_BLUE[1] * (1 - color_ratio) + Colors.BLUE_GRAY[1] * color_ratio)
            b = int(Colors.DARK_BLUE[2] * (1 - color_ratio) + Colors.BLUE_GRAY[2] * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.SCREEN_WIDTH, y))
        
        # Título
        title = self.font_large.render("SELECCIONA DIFICULTAD", True, Colors.CYAN)
        title_x = (self.SCREEN_WIDTH - title.get_width()) // 2
        self.screen.blit(title, (title_x, 50))
        
        # Opciones de dificultad
        difficulties = [
            {"name": "FÁCIL", "color": Colors.GREEN, "desc": "CPU más lento y predecible"},
            {"name": "MEDIO", "color": Colors.ORANGE, "desc": "CPU con velocidad moderada"},
            {"name": "DIFÍCIL", "color": Colors.RED, "desc": "CPU rápido y agresivo"}
        ]
        
        start_y = 150
        spacing = 80
        
        for i, diff in enumerate(difficulties):
            y_pos = start_y + (i * spacing)
            
            # Resaltar opción seleccionada
            if i == self.selected_difficulty:
                # Rectángulo de selección con resplandor
                rect = pygame.Rect(
                    self.SCREEN_WIDTH // 2 - 200,
                    y_pos - 10,
                    400,
                    60
                )
                self.draw_glow_rect(self.screen, diff["color"], rect, glow_size=8)
            
            # Nombre de la dificultad
            text = self.font_large.render(diff["name"], True, 
                                         Colors.WHITE if i == self.selected_difficulty else diff["color"])
            text_x = (self.SCREEN_WIDTH - text.get_width()) // 2
            self.screen.blit(text, (text_x, y_pos))
            
            # Descripción
            desc = self.font_small.render(diff["desc"], True, Colors.GRAY)
            desc_x = (self.SCREEN_WIDTH - desc.get_width()) // 2
            self.screen.blit(desc, (desc_x, y_pos + 30))
        
        # Instrucciones
        instructions = [
            "↑ ↓ - Seleccionar dificultad",
            "ENTER/ESPACIO - Confirmar"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, Colors.GRAY)
            text_x = (self.SCREEN_WIDTH - text.get_width()) // 2
            self.screen.blit(text, (text_x, self.SCREEN_HEIGHT - 50 + (i * 20)))
        
    def render(self):
        # Menú de dificultad
        if self.game_state == "difficulty_menu":
            self.render_difficulty_menu()
            return
        
        # Fondo con gradiente
        for y in range(self.SCREEN_HEIGHT):
            color_ratio = y / self.SCREEN_HEIGHT
            r = int(Colors.DARK_BLUE[0] * (1 - color_ratio) + Colors.BLUE_GRAY[0] * color_ratio)
            g = int(Colors.DARK_BLUE[1] * (1 - color_ratio) + Colors.BLUE_GRAY[1] * color_ratio)
            b = int(Colors.DARK_BLUE[2] * (1 - color_ratio) + Colors.BLUE_GRAY[2] * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.SCREEN_WIDTH, y))
            
        # Línea central punteada
        for y in range(0, self.SCREEN_HEIGHT, 20):
            pygame.draw.rect(self.screen, Colors.GRAY, 
                           (self.SCREEN_WIDTH // 2 - 2, y, 4, 10))
            
        # Trail de la pelota
        for i, (x, y) in enumerate(self.ball['trail']):
            alpha = (i + 1) / len(self.ball['trail']) * 100
            if alpha > 0:
                trail_surf = pygame.Surface((self.ball['radius'] * 2, self.ball['radius'] * 2))
                trail_surf.set_alpha(int(alpha))
                pygame.draw.circle(trail_surf, Colors.WHITE, 
                                 (self.ball['radius'], self.ball['radius']), 
                                 int(self.ball['radius'] * ((i + 1) / len(self.ball['trail']))))
                self.screen.blit(trail_surf, (x - self.ball['radius'], y - self.ball['radius']))
        
        # Paletas con resplandor
        player_rect = pygame.Rect(self.player['x'], self.player['y'], 
                                 self.player['width'], self.player['height'])
        self.draw_glow_rect(self.screen, self.player['color'], player_rect)
        
        cpu_rect = pygame.Rect(self.cpu['x'], self.cpu['y'], 
                              self.cpu['width'], self.cpu['height'])
        self.draw_glow_rect(self.screen, self.cpu['color'], cpu_rect)
        
        # Pelota con resplandor
        self.draw_glow_circle(self.screen, self.ball['color'], 
                             (int(self.ball['x']), int(self.ball['y'])), 
                             self.ball['radius'])
        
        # Pelotas adicionales
        for extra_ball in self.extra_balls:
            # Trail de pelota extra
            for i, (x, y) in enumerate(extra_ball['trail']):
                alpha = (i + 1) / len(extra_ball['trail']) * 100
                if alpha > 0:
                    trail_surf = pygame.Surface((extra_ball['radius'] * 2, extra_ball['radius'] * 2))
                    trail_surf.set_alpha(int(alpha))
                    pygame.draw.circle(trail_surf, Colors.ORANGE, 
                                     (extra_ball['radius'], extra_ball['radius']), 
                                     int(extra_ball['radius'] * ((i + 1) / len(extra_ball['trail']))))
                    self.screen.blit(trail_surf, (x - extra_ball['radius'], y - extra_ball['radius']))
            
            self.draw_glow_circle(self.screen, Colors.ORANGE, 
                                 (int(extra_ball['x']), int(extra_ball['y'])), 
                                 extra_ball['radius'])
        
        # Marcador
        player_text = self.font_large.render(f"Jugador: {self.player_score}", True, Colors.CYAN)
        cpu_text = self.font_large.render(f"CPU: {self.cpu_score}", True, Colors.RED)
        
        self.screen.blit(player_text, (20, 20))
        self.screen.blit(cpu_text, (self.SCREEN_WIDTH - cpu_text.get_width() - 20, 20))
        
        # Mostrar dificultad actual
        diff_names = {"easy": "FÁCIL", "medium": "MEDIO", "hard": "DIFÍCIL"}
        diff_colors = {"easy": Colors.GREEN, "medium": Colors.ORANGE, "hard": Colors.RED}
        if self.difficulty:
            diff_text = self.font_small.render(f"Dificultad: {diff_names[self.difficulty]}", 
                                              True, diff_colors[self.difficulty])
            diff_x = (self.SCREEN_WIDTH - diff_text.get_width()) // 2
            self.screen.blit(diff_text, (diff_x, 20))
        
        # Notificaciones de power-ups activos
        notification_y = 60
        if self.player_frozen:
            freeze_text = self.font_medium.render("⚡ JUGADOR CONGELADO ⚡", True, Colors.CYAN)
            freeze_x = (self.SCREEN_WIDTH - freeze_text.get_width()) // 2
            # Fondo semi-transparente
            freeze_bg = pygame.Surface((freeze_text.get_width() + 20, freeze_text.get_height() + 10))
            freeze_bg.set_alpha(180)
            freeze_bg.fill(Colors.DARK_BLUE)
            self.screen.blit(freeze_bg, (freeze_x - 10, notification_y - 5))
            self.screen.blit(freeze_text, (freeze_x, notification_y))
            notification_y += 35
        
        if self.cpu_frozen:
            freeze_text = self.font_medium.render("⚡ CPU CONGELADO ⚡", True, Colors.RED)
            freeze_x = (self.SCREEN_WIDTH - freeze_text.get_width()) // 2
            freeze_bg = pygame.Surface((freeze_text.get_width() + 20, freeze_text.get_height() + 10))
            freeze_bg.set_alpha(180)
            freeze_bg.fill(Colors.DARK_BLUE)
            self.screen.blit(freeze_bg, (freeze_x - 10, notification_y - 5))
            self.screen.blit(freeze_text, (freeze_x, notification_y))
            notification_y += 35
        
        if self.multi_ball_active:
            multi_text = self.font_medium.render("🔥 PELOTAS MÚLTIPLES 🔥", True, Colors.ORANGE)
            multi_x = (self.SCREEN_WIDTH - multi_text.get_width()) // 2
            multi_bg = pygame.Surface((multi_text.get_width() + 20, multi_text.get_height() + 10))
            multi_bg.set_alpha(180)
            multi_bg.fill(Colors.DARK_BLUE)
            self.screen.blit(multi_bg, (multi_x - 10, notification_y - 5))
            self.screen.blit(multi_text, (multi_x, notification_y))
            notification_y += 35
        
        # Estado del juego
        status_text = ""
        if self.game_state == "waiting":
            status_text = "Presiona ESPACIO para comenzar"
        elif self.game_state == "paused":
            status_text = "PAUSADO - Presiona ESPACIO para continuar"
        elif self.game_state == "game_over":
            winner = "Jugador" if self.player_score >= self.max_score else "CPU"
            status_text = f"¡{winner} gana! Presiona R para jugar de nuevo"
            
        if status_text:
            text_surface = self.font_medium.render(status_text, True, Colors.CYAN)
            text_x = (self.SCREEN_WIDTH - text_surface.get_width()) // 2
            self.screen.blit(text_surface, (text_x, 60))
            
        # Controles
        controls = [
            "Controles:",
            "↑ ↓ - Mover paleta",
            "ESPACIO - Pausar/Reanudar",
            "R - Reiniciar"
        ]
        
        for i, control in enumerate(controls):
            text = self.font_small.render(control, True, Colors.GRAY)
            self.screen.blit(text, (20, self.SCREEN_HEIGHT - 80 + i * 15))
            
        # Overlay de pausa
        if self.game_state == "paused":
            pause_surf = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
            pause_surf.set_alpha(128)
            pause_surf.fill(Colors.BLACK)
            self.screen.blit(pause_surf, (0, 0))
            
            pause_text = self.font_large.render("PAUSADO", True, Colors.CYAN)
            text_x = (self.SCREEN_WIDTH - pause_text.get_width()) // 2
            text_y = (self.SCREEN_HEIGHT - pause_text.get_height()) // 2
            self.screen.blit(pause_text, (text_x, text_y))
            
    def toggle_pause(self):
        if self.game_state == "waiting":
            self.game_state = "playing"
        elif self.game_state == "playing":
            self.game_state = "paused"
        elif self.game_state == "paused":
            self.game_state = "playing"
            
    def reset_game(self):
        self.player_score = 0
        self.cpu_score = 0
        self.init_game_objects()
        if self.difficulty:
            self.set_difficulty(self.difficulty)
        self.game_state = "difficulty_menu"
        self.selected_difficulty = 0
        # Resetear power-ups
        self.powerups = []
        self.powerup_spawn_timer = 0
        self.player_frozen = False
        self.player_frozen_timer = 0
        self.cpu_frozen = False
        self.cpu_frozen_timer = 0
        self.multi_ball_active = False
        self.multi_ball_timer = 0
        self.extra_balls = []
        
    def run(self):
        running = True
        
        while running:
            # Manejar eventos
            running = self.handle_events()
            
            # Actualizar juego
            self.update()
            
            # Renderizar
            self.render()
            
            # Actualizar pantalla
            pygame.display.flip()
            self.clock.tick(self.FPS)
            
        # Salir
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = PongGame()
    game.run()