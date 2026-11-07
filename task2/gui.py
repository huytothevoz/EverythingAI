import pygame
import sys
import time
import random
import os
from config import Player, Action, Direction, AgentType, GRID_ROWS, GRID_COLS, HP_WALL
from game_state import GameState
from entities import Tank, Base, Wall, Bullet
from agent_loader import load_agent
from experiment import create_sample_game_state

# --- CẤU HÌNH GIAO DIỆN ---
CELL_SIZE = 30
BOARD_WIDTH = GRID_COLS * CELL_SIZE
BOARD_HEIGHT = GRID_ROWS * CELL_SIZE
SIDEBAR_WIDTH = 300
SCREEN_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT

ASSETS = {
    "tank_max": "assets/tank_max.png",
    "tank_min": "assets/tank_min.png",
    "base_max": "assets/base_max.png",
    "base_min": "assets/base_min.png",
    "bullet": "assets/bullet.png",          
    "explosion": "assets/explosion.png"     
}

COLOR_GRASS = (143, 172, 82)
COLOR_DIRT = (232, 207, 157)
COLOR_WALL = (139, 90, 43)
COLOR_WALL_DARK = (100, 60, 20)
COLOR_TANK_MAX = (80, 140, 50)    
COLOR_TANK_MIN = (60, 60, 70)     
COLOR_BULLET = (255, 220, 50)
COLOR_UI_BG = (30, 34, 40)
COLOR_UI_PANEL = (45, 50, 60)
COLOR_UI_TEXT = (220, 220, 220)
COLOR_BTN = (70, 80, 90)
COLOR_BTN_HOVER = (100, 110, 120)
COLOR_BTN_ACTIVE = (60, 160, 80)

# Góc xoay (Ảnh gốc chĩa sang TRÁI)
DIRECTION_ANGLE = {
    Direction.LEFT: 0,
    Direction.DOWN: 90,
    Direction.RIGHT: 180,
    Direction.UP: 270
}

class Button:
    def __init__(self, x, y, w, h, text, font, callback=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.callback = callback
        self.is_hovered = False
        self.is_active = False

    def draw(self, surface):
        color = COLOR_BTN_HOVER if self.is_hovered else (COLOR_BTN_ACTIVE if self.is_active else COLOR_BTN)
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (20, 20, 20), self.rect, 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, COLOR_UI_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.callback:
                self.callback()
                return True
        return False

class TankWarsGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pixel Tank Wars - AI Project")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.SysFont("consolas", 12)
        self.font_med = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_large = pygame.font.SysFont("consolas", 40, bold=True)

        self.images = self.load_assets()

        self.state = "MENU"
        self.paused = False
        self.auto_play = True
        self.ai_delay = 0.3  
        self.last_ai_time = 0

        self.mode = "AI_VS_AI" 
        self.ai1_type = AgentType.ALPHABETA_HEURISTIC
        self.ai2_type = AgentType.MINIMAX_HEURISTIC
        
        self.agent_max = None
        self.agent_min = None
        
        self.last_ai_stats = {"nodes": 0, "pruned": 0, "time": 0.0}
        self.last_actions = {Player.MAX: "None", Player.MIN: "None"}

        # Lưu hiệu ứng nổ
        self.explosions = []

        self.dirt_patches = []
        for _ in range(20):
            w = random.randint(2, 6)
            h = random.randint(2, 5)
            x = random.randint(0, GRID_COLS - w)
            y = random.randint(0, GRID_ROWS - h)
            self.dirt_patches.append(pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, w*CELL_SIZE, h*CELL_SIZE))

        self.setup_menu_buttons()

    def load_assets(self):
        imgs = {}
        current_dir = os.path.dirname(os.path.abspath(__file__)) 
        
        for key, default_path in ASSETS.items():
            base_name = default_path.rsplit('.', 1)[0]
            base_path = os.path.join(current_dir, base_name)
            possible_paths = [f"{base_path}.png", f"{base_path}.jpg", f"{base_path}.jpeg"]
            
            found = False
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        
                        # 1. Cắt viền thừa
                        rect = img.get_bounding_rect(min_alpha=1)
                        if rect.width > 0 and rect.height > 0:
                            img = img.subsurface(rect).copy()

                        # 2. Scale theo tỷ lệ phù hợp cho từng loại
                        if "tank" in key:
                            target_w = int(CELL_SIZE * 1.6) 
                        elif "bullet" in key:
                            target_w = int(CELL_SIZE * 0.5) # Đạn nhỏ hơn ô cờ
                        elif "explosion" in key:
                            target_w = int(CELL_SIZE * 1.0) # Kích thước nổ cơ bản, sẽ được phóng to sau
                        else:
                            target_w = int(CELL_SIZE * 0.9) # Base

                        scale_ratio = target_w / img.get_width()
                        target_h = int(img.get_height() * scale_ratio)
                        
                        imgs[key] = pygame.transform.scale(img, (target_w, target_h))
                        print(f"✅ Đã tải: {path} -> {imgs[key].get_size()}")
                        found = True
                        break
                    except Exception as e:
                        print(f"❌ Lỗi khi tải {path}: {e}")
            
            if not found:
                print(f"⚠️ KHÔNG TÌM THẤY ẢNH: {base_name} -> Dùng mặc định.")
                imgs[key] = None
        return imgs

    def setup_menu_buttons(self):
        cx = SCREEN_WIDTH // 2
        self.menu_buttons = [
            Button(cx - 150, 200, 300, 40, f"Mode: {self.mode}", self.font_med, self.toggle_mode),
            Button(cx - 150, 260, 300, 40, f"AI MAX: {self.ai1_type.value}", self.font_med, self.cycle_ai1),
            Button(cx - 150, 320, 300, 40, f"AI MIN: {self.ai2_type.value}", self.font_med, self.cycle_ai2),
            Button(cx - 150, 420, 300, 50, "START GAME", self.font_large, self.start_game),
        ]

    def setup_game_buttons(self):
        sx = BOARD_WIDTH + 20
        self.game_buttons = [
            Button(sx, 330, 260, 40, "Pause / Resume", self.font_med, self.toggle_pause),
            Button(sx, 390, 260, 40, "Step (AI only)", self.font_med, self.step_ai),
            Button(sx, 450, 260, 40, "Toggle Auto Play", self.font_med, self.toggle_auto),
            Button(sx, 540, 260, 40, "Back to Menu", self.font_med, self.back_to_menu),
        ]

    def toggle_mode(self):
        self.mode = "USER_VS_AI" if self.mode == "AI_VS_AI" else "AI_VS_AI"
        self.menu_buttons[0].text = f"Mode: {self.mode}"
        self.menu_buttons[1].text = f"AI MAX: {self.ai1_type.value}" if self.mode == "AI_VS_AI" else "AI MAX: (User)"

    def cycle_ai1(self):
        if self.mode == "AI_VS_AI":
            types = list(AgentType)
            idx = types.index(self.ai1_type)
            self.ai1_type = types[(idx + 1) % len(types)]
            self.menu_buttons[1].text = f"AI MAX: {self.ai1_type.value}"

    def cycle_ai2(self):
        types = list(AgentType)
        idx = types.index(self.ai2_type)
        self.ai2_type = types[(idx + 1) % len(types)]
        self.menu_buttons[2].text = f"AI MIN: {self.ai2_type.value}"

    def start_game(self):
        self.state = "PLAYING"
        self.paused = False
        self.auto_play = True
        self.last_ai_time = time.time()
        
        self.gs = create_sample_game_state()
        
        self.last_ai_stats = {"nodes": 0, "pruned": 0, "time": 0.0}
        self.last_actions = {Player.MAX: "None", Player.MIN: "None"}
        self.explosions = [] 
        
        if self.mode == "AI_VS_AI":
            self.agent_max = load_agent(self.ai1_type, depth=3)
        else:
            self.agent_max = None
            
        self.agent_min = load_agent(self.ai2_type, depth=3)
        self.setup_game_buttons()

    def back_to_menu(self):
        self.state = "MENU"

    def toggle_pause(self):
        self.paused = not self.paused

    def toggle_auto(self):
        self.auto_play = not self.auto_play

    def step_ai(self):
        if not self.paused:
            self.paused = True 
        self._do_ai_turn()

    def _create_explosion(self, pos):
        r, c = pos
        cx, cy = c * CELL_SIZE + CELL_SIZE//2, r * CELL_SIZE + CELL_SIZE//2
        self.explosions.append({
            "x": cx, "y": cy, 
            "scale": 0.5, 
            "alpha": 255
        })

    def _check_destruction(self, old_state, new_state):
        for pos in old_state.walls:
            if pos not in new_state.walls:
                self._create_explosion(pos)
        for player, tank in old_state.tanks.items():
            if player not in new_state.tanks:
                self._create_explosion(tank.position)
        for player, base in old_state.bases.items():
            if player not in new_state.bases:
                self._create_explosion(base.position)

    def _do_ai_turn(self):
        if self.gs.is_terminal():
            return
            
        current_player = self.gs.current_player
        agent = self.agent_max if current_player == Player.MAX else self.agent_min
        
        if agent:
            action = agent.choose_action(self.gs)
            if action:
                old_gs = self.gs
                self.gs = self.gs.apply_action(action)
                self._check_destruction(old_gs, self.gs)
                self.last_actions[current_player] = action.name.replace("_", " ")
            
            self.last_ai_stats = {
                "nodes": agent.nodes_expanded,
                "pruned": agent.pruned_count,
                "time": agent.execution_time * 1000
            }
            self.last_ai_time = time.time()

    def draw_menu(self):
        self.screen.fill(COLOR_GRASS)
        for patch in self.dirt_patches:
            pygame.draw.rect(self.screen, COLOR_DIRT, patch, border_radius=10)

        title_surf = self.font_large.render("Pixel Tank Wars", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, 100))
        shadow_surf = self.font_large.render("Pixel Tank Wars", True, (0, 0, 0))
        self.screen.blit(shadow_surf, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title_surf, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.menu_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)

    def draw_game(self):
        self.screen.fill(COLOR_UI_BG)
        
        board_surf = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
        board_surf.fill(COLOR_GRASS)
        for patch in self.dirt_patches:
            pygame.draw.rect(board_surf, COLOR_DIRT, patch, border_radius=10)
            
        # 1. Vẽ Walls & Thanh máu
        for wall in self.gs.walls.values():
            r, c = wall.position
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(board_surf, COLOR_WALL, rect)
            pygame.draw.rect(board_surf, COLOR_WALL_DARK, rect, 2)
            pygame.draw.line(board_surf, COLOR_WALL_DARK, (rect.left, rect.centery), (rect.right, rect.centery), 2)
            
            if wall.hp < HP_WALL:
                ratio = max(0, wall.hp / HP_WALL)
                bar_w = CELL_SIZE - 6
                bar_h = 4
                bar_x = rect.x + 3
                bar_y = rect.y + 3
                pygame.draw.rect(board_surf, (150, 0, 0), (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(board_surf, (0, 255, 0), (bar_x, bar_y, bar_w * ratio, bar_h))

        # 2. Vẽ Bases
        for player, base in self.gs.bases.items():
            r, c = base.position
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_key = "base_max" if player == Player.MAX else "base_min"
            
            if self.images[img_key]:
                img_rect = self.images[img_key].get_rect(center=rect.center)
                board_surf.blit(self.images[img_key], img_rect)
            else:
                color = COLOR_TANK_MAX if player == Player.MAX else COLOR_TANK_MIN
                pygame.draw.rect(board_surf, color, rect)
                pygame.draw.rect(board_surf, (255, 255, 255), rect, 2)
            
            hp_surf = self.font_med.render(str(base.hp), True, (255, 50, 50))
            board_surf.blit(hp_surf, (rect.centerx - 8, rect.centery - 10))

        # 3. Vẽ Tanks
        for player, tank in self.gs.tanks.items():
            r, c = tank.position
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            img_key = "tank_max" if player == Player.MAX else "tank_min"
            
            if self.images[img_key]:
                angle = DIRECTION_ANGLE.get(tank.direction, 0)
                rotated_img = pygame.transform.rotate(self.images[img_key], angle)
                rot_rect = rotated_img.get_rect(center=rect.center)
                board_surf.blit(rotated_img, rot_rect)
            else:
                cx, cy = rect.centerx, rect.centery
                color = COLOR_TANK_MAX if player == Player.MAX else COLOR_TANK_MIN
                pygame.draw.circle(board_surf, color, (cx, cy), CELL_SIZE//2 - 2)
                pygame.draw.circle(board_surf, (0, 0, 0), (cx, cy), CELL_SIZE//2 - 2, 1)
                dx, dy = tank.direction.value
                end_x = cx + dx * (CELL_SIZE // 2 + 4)
                end_y = cy + dy * (CELL_SIZE // 2 + 4)
                pygame.draw.line(board_surf, (20, 20, 20), (cx, cy), (end_x, end_y), 4)

        # 4. Vẽ Bullets
        for bullet in self.gs.bullets:
            r, c = bullet.position
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            
            if self.images["bullet"]:
                # Đạn cũng xoay theo hướng bay
                angle = DIRECTION_ANGLE.get(bullet.direction, 0)
                rotated_bullet = pygame.transform.rotate(self.images["bullet"], angle)
                bullet_rect = rotated_bullet.get_rect(center=rect.center)
                board_surf.blit(rotated_bullet, bullet_rect)
            else:
                cx, cy = rect.centerx, rect.centery
                pygame.draw.circle(board_surf, COLOR_BULLET, (cx, cy), 5)
                pygame.draw.circle(board_surf, (200, 100, 0), (cx, cy), 5, 1)

        # 5. Vẽ Hiệu ứng nổ
        for exp in self.explosions:
            if exp["alpha"] > 0:
                if self.images["explosion"]:
                    # Scale ảnh nổ to dần
                    base_img = self.images["explosion"]
                    w = int(base_img.get_width() * exp["scale"])
                    h = int(base_img.get_height() * exp["scale"])
                    scaled_exp = pygame.transform.scale(base_img, (w, h))
                    # Làm mờ dần
                    scaled_exp.set_alpha(int(exp["alpha"]))
                    
                    exp_rect = scaled_exp.get_rect(center=(exp["x"], exp["y"]))
                    board_surf.blit(scaled_exp, exp_rect)
                else:
                    # Fallback vẽ hình tròn
                    exp_surf = pygame.Surface((exp["scale"]*40, exp["scale"]*40), pygame.SRCALPHA)
                    pygame.draw.circle(exp_surf, (255, 100, 0, int(exp["alpha"])), 
                                       (exp["scale"]*20, exp["scale"]*20), exp["scale"]*20)
                    board_surf.blit(exp_surf, (exp["x"] - exp["scale"]*20, exp["y"] - exp["scale"]*20))

        self.screen.blit(board_surf, (0, 0))

        # --- SIDEBAR UI ---
        pygame.draw.rect(self.screen, COLOR_UI_PANEL, (BOARD_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, (0,0,0), (BOARD_WIDTH, 0), (BOARD_WIDTH, SCREEN_HEIGHT), 2)

        turn_color = (100, 255, 100) if self.gs.current_player == Player.MAX else (255, 100, 100)
        turn_text = f"TURN: {'MAX' if self.gs.current_player == Player.MAX else 'MIN'}"
        turn_surf = self.font_large.render(turn_text, True, turn_color)
        self.screen.blit(turn_surf, (BOARD_WIDTH + 20, 20))

        max_tank = self.gs.tanks.get(Player.MAX)
        min_tank = self.gs.tanks.get(Player.MIN)
        hp_text = [
            f"MAX Tank HP: {max_tank.hp if max_tank else 0}",
            f"MIN Tank HP: {min_tank.hp if min_tank else 0}",
        ]
        for i, text in enumerate(hp_text):
            surf = self.font_med.render(text, True, COLOR_UI_TEXT)
            self.screen.blit(surf, (BOARD_WIDTH + 20, 80 + i * 25))

        pygame.draw.line(self.screen, (100,100,100), (BOARD_WIDTH+20, 140), (SCREEN_WIDTH-20, 140), 1)
        act_max = self.last_actions[Player.MAX]
        act_min = self.last_actions[Player.MIN]
        
        act_text = [
            f"MAX Last: {act_max}",
            f"MIN Last: {act_min}"
        ]
        for i, text in enumerate(act_text):
            color = (150, 255, 150) if i == 0 else (255, 150, 150)
            surf = self.font_med.render(text, True, color)
            self.screen.blit(surf, (BOARD_WIDTH + 20, 155 + i * 25))

        pygame.draw.line(self.screen, (100,100,100), (BOARD_WIDTH+20, 210), (SCREEN_WIDTH-20, 210), 1)
        stats_text = [
            "--- AI LAST MOVE STATS ---",
            f"Nodes Expanded: {self.last_ai_stats['nodes']}",
            f"Pruned Branches: {self.last_ai_stats['pruned']}",
            f"Think Time: {self.last_ai_stats['time']:.2f} ms",
            "",
            f"Auto Play: {'ON' if self.auto_play else 'OFF'}",
            f"Paused: {'YES' if self.paused else 'NO'}"
        ]
        for i, text in enumerate(stats_text):
            color = (150, 200, 255) if "---" in text else COLOR_UI_TEXT
            surf = self.font_small.render(text, True, color)
            self.screen.blit(surf, (BOARD_WIDTH + 20, 220 + i * 20))

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.game_buttons:
            if btn.text == "Pause / Resume":
                btn.is_active = self.paused
            elif btn.text == "Toggle Auto Play":
                btn.is_active = self.auto_play
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)

        if self.gs.is_terminal():
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            utility = self.gs.get_utility(0)
            if utility > 0: winner = "MAX WINS!"
            elif utility < 0: winner = "MIN WINS!"
            else: winner = "DRAW!"
            
            win_surf = self.font_large.render(winner, True, COLOR_BULLET)
            win_rect = win_surf.get_rect(center=(BOARD_WIDTH//2, BOARD_HEIGHT//2))
            self.screen.blit(win_surf, win_rect)

    def update(self):
        # Cập nhật hiệu ứng nổ (to dần và mờ dần)
        for exp in self.explosions[:]:
            exp["scale"] += 0.05
            exp["alpha"] -= 15
            if exp["alpha"] <= 0:
                self.explosions.remove(exp)

        if self.state != "PLAYING" or self.paused or self.gs.is_terminal():
            return

        current_player = self.gs.current_player
        
        if self.mode == "USER_VS_AI" and current_player == Player.MAX:
            pass 
        else:
            if self.auto_play:
                now = time.time()
                if now - self.last_ai_time > self.ai_delay:
                    self._do_ai_turn()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == "MENU":
                    for btn in self.menu_buttons:
                        btn.handle_event(event)
                        
                elif self.state == "PLAYING":
                    for btn in self.game_buttons:
                        btn.handle_event(event)
                        
                    if event.type == pygame.KEYDOWN:
                        if self.mode == "USER_VS_AI" and self.gs.current_player == Player.MAX and not self.gs.is_terminal():
                            action = None
                            if event.key == pygame.K_w: action = Action.MOVE_UP
                            elif event.key == pygame.K_s: action = Action.MOVE_DOWN
                            elif event.key == pygame.K_a: action = Action.MOVE_LEFT
                            elif event.key == pygame.K_d: action = Action.MOVE_RIGHT
                            elif event.key == pygame.K_SPACE: action = Action.FIRE
                            
                            if action:
                                old_gs = self.gs
                                self.gs = self.gs.apply_action(action)
                                self._check_destruction(old_gs, self.gs)
                                self.last_actions[Player.MAX] = action.name.replace("_", " ")

            self.update()

            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "PLAYING":
                self.draw_game()

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = TankWarsGUI()
    game.run()