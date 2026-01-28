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

class PongGame:
    def __init__(self):
        # Configuración de pantalla
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 400
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Pong Arcade - Tu Toque Personal")
        
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
        self.game_state = "waiting"  # waiting, playing, paused, game_over
        self.player_score = 0
        self.cpu_score = 0
        self.max_score = 5
        
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
            'color': Colors.RED
        }
        
        # Pelota
        self.ball = {
            'x': self.SCREEN_WIDTH // 2,
            'y': self.SCREEN_HEIGHT // 2,
            'radius': 8,
            'speed_x': 4,
            'speed_y': 3,
            'color': Colors.WHITE,
            'trail': []
        }
        
        self.reset_ball()
        
    def reset_ball(self):
        self.ball['x'] = self.SCREEN_WIDTH // 2
        self.ball['y'] = self.SCREEN_HEIGHT // 2
        self.ball['speed_x'] = random.choice([4, -4])
        self.ball['speed_y'] = random.uniform(-3, 3)
        self.ball['trail'] = []
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.toggle_pause()
                elif event.key == pygame.K_r:
                    self.reset_game()
                    
        return True
        
    def update(self):
        if self.game_state != "playing":
            return
            
        # Actualizar controles
        self.keys = pygame.key.get_pressed()
        
        # Movimiento del jugador
        if self.keys[pygame.K_UP] and self.player['y'] > 0:
            self.player['y'] -= self.player['speed']
        if self.keys[pygame.K_DOWN] and self.player['y'] < self.SCREEN_HEIGHT - self.player['height']:
            self.player['y'] += self.player['speed']
            
        # IA de la CPU
        cpu_center = self.cpu['y'] + self.cpu['height'] // 2
        ball_y = self.ball['y']
        
        if cpu_center < ball_y - 10:
            self.cpu['y'] += self.cpu['speed']
        elif cpu_center > ball_y + 10:
            self.cpu['y'] -= self.cpu['speed']
            
        # Mantener CPU en pantalla
        if self.cpu['y'] < 0:
            self.cpu['y'] = 0
        if self.cpu['y'] > self.SCREEN_HEIGHT - self.cpu['height']:
            self.cpu['y'] = self.SCREEN_HEIGHT - self.cpu['height']
            
        # Movimiento de la pelota
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
            self.ball['speed_x'] = abs(self.ball['speed_x'])
            
            # Calcular ángulo basado en dónde golpeó
            hit_pos = (self.ball['y'] - self.player['y']) / self.player['height']
            self.ball['speed_y'] = (hit_pos - 0.5) * 8
            
        # Colisión con paleta de la CPU
        if ball_rect.colliderect(cpu_rect) and self.ball['speed_x'] > 0:
            self.ball['speed_x'] = -abs(self.ball['speed_x'])
            
            # Calcular ángulo basado en dónde golpeó
            hit_pos = (self.ball['y'] - self.cpu['y']) / self.cpu['height']
            self.ball['speed_y'] = (hit_pos - 0.5) * 8
            
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
        
    def render(self):
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
        
        # Marcador
        player_text = self.font_large.render(f"Jugador: {self.player_score}", True, Colors.CYAN)
        cpu_text = self.font_large.render(f"CPU: {self.cpu_score}", True, Colors.RED)
        
        self.screen.blit(player_text, (20, 20))
        self.screen.blit(cpu_text, (self.SCREEN_WIDTH - cpu_text.get_width() - 20, 20))
        
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
        self.game_state = "waiting"
        
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