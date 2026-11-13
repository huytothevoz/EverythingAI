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

CELL_SIZE = 30
BOARD_WIDTH = GRID_COLS * CELL_SIZE
BOARD_HEIGHT = GRID_ROWS * CELL_SIZE
SIDEBAR_WIDTH = 300
SCREEN_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT

# Hiệu ứng nháy trắng khi thực thể nhận sát thương
DAMAGE_FLASH_FRAMES = 10
MAX_FLASH_ALPHA = 220

#ĐƯỜNG DẪN CÁC FILE MÔ HÌNH
ASSETS = {
    "tank_max": "assets/tank_max.png",
    "tank_min": "assets/tank_min.png",
    "base_max": "assets/base_max.png",
    "base_min": "assets/base_min.png",
    "bullet": "assets/bullet.png",
    "explosion": "assets/explosion.png"
}

#ĐƯỜNG DẪN CÁC FILE ÂM THANH 
SOUND_FILES = {
    "tank_move":    "assets/sounds/tank_move.wav",     # xe tăng di chuyển
    "tank_fire":    "assets/sounds/tank_fire.wav",     # xe tăng bắn
    "bullet_hit":   "assets/sounds/bullet_hit.wav",    # đạn trúng đích (chưa phá hủy)
    "destroyed":    "assets/sounds/destroyed.wav",     # thực thể bị phá hủy
    "game_over":    "assets/sounds/game_over.wav",     # kết thúc trận đấu
    "button_click": "assets/sounds/button_click.wav",  # button click 
}
BGM_FILES = {
    "menu":   "assets/sounds/menu_bgm.mp3",   # nhạc nền menu
    "battle": "assets/sounds/battle_bgm.mp3", # nhạc nền trong trận
}

# Âm lượng: 
BGM_MENU_VOLUME   = 0.2   
BGM_BATTLE_VOLUME = 0.4
SFX_VOLUME = 0.7

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

# Góc xoay 
DIRECTION_ANGLE = {
    Direction.LEFT: 90,
    Direction.DOWN: 180,
    Direction.RIGHT: 270,
    Direction.UP: 0
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
        """Trả về True nếu nút được click (để phía gọi tự phát SFX)."""
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
        self.init_audio()

        self.state = "MENU"
        self.paused = False
        # self.auto_play đã được bỏ — AI luôn tự chạy khi không bị pause.
        self.ai_delay = 0.3
        self.last_ai_time = 0

        self.mode = "AI_VS_AI"
        self.ai1_type = AgentType.ALPHABETA_HEURISTIC
        self.ai2_type = AgentType.MINIMAX_HEURISTIC

        self.agent_max = None
        self.agent_min = None

        self.last_actions = {Player.MAX: "None", Player.MIN: "None"}
        self.move_count = 0

        # Lưu hiệu ứng nổ
        self.explosions = []

        # Hiệu ứng nháy trắng khi bị thương
        self.damage_flashes = []
        self.game_over_played = False

        self.dirt_patches = []
        for _ in range(20):
            w = random.randint(2, 6)
            h = random.randint(2, 5)
            x = random.randint(0, GRID_COLS - w)
            y = random.randint(0, GRID_ROWS - h)
            self.dirt_patches.append(pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, w*CELL_SIZE, h*CELL_SIZE))

        self.setup_menu_buttons()

        # Nhạc nền menu
        self.play_bgm("menu")

    # ÂM THANH
    def init_audio(self):
        self.audio_available = False
        self.sounds = {}
        self.bgm_paths = {}
        self.current_bgm = None

        try:
            pygame.mixer.init()
            self.audio_available = True
        except pygame.error as e:
            print(f"[AUDIO] Không thể khởi tạo mixer: {e}")
            return

        current_dir = os.path.dirname(os.path.abspath(__file__))

        # SFX
        for key, rel_path in SOUND_FILES.items():
            full_path = os.path.join(current_dir, rel_path)
            if os.path.exists(full_path):
                try:
                    snd = pygame.mixer.Sound(full_path)
                    snd.set_volume(SFX_VOLUME)
                    self.sounds[key] = snd
                except Exception as e:
                    print(f"[SFX] Lỗi tải {key}: {e}")
                    self.sounds[key] = None
            else:
                print(f"[SFX] Không tìm thấy: {rel_path}")
                self.sounds[key] = None

        # BGM
        for key, rel_path in BGM_FILES.items():
            full_path = os.path.join(current_dir, rel_path)
            if os.path.exists(full_path):
                self.bgm_paths[key] = full_path
            else:
                print(f"[BGM] Không tìm thấy: {rel_path}")
                self.bgm_paths[key] = None

    def play_sound(self, key):
        if not self.audio_available:
            return
        snd = self.sounds.get(key)
        if snd:
            snd.play()

    def play_bgm(self, key):
        if not self.audio_available:
            return
        if self.current_bgm == key:
            return
        path = self.bgm_paths.get(key)
        if path and os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                # Menu nhỏ hơn battle 50%
                volume = BGM_MENU_VOLUME if key == "menu" else BGM_BATTLE_VOLUME
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)
                self.current_bgm = key
            except Exception as e:
                print(f"[BGM] Lỗi phát {key}: {e}")

    def stop_bgm(self):
        if not self.audio_available:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.current_bgm = None

    # ASSETS
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
                        rect = img.get_bounding_rect(min_alpha=1)
                        if rect.width > 0 and rect.height > 0:
                            img = img.subsurface(rect).copy()

                        if "tank" in key:
                            # Giảm kích thước tank (trước đây 1.6)
                            target_w = int(CELL_SIZE * 1.2)
                        elif "bullet" in key:
                            target_w = int(CELL_SIZE * 0.5)
                        elif "explosion" in key:
                            target_w = int(CELL_SIZE * 1.0)
                        else:
                            target_w = int(CELL_SIZE * 0.9)

                        scale_ratio = target_w / img.get_width()
                        target_h = int(img.get_height() * scale_ratio)
                        imgs[key] = pygame.transform.scale(img, (target_w, target_h))
                        found = True
                        break
                    except Exception as e:
                        print(f"Lỗi khi tải {path}: {e}")

            if not found:
                imgs[key] = None
        return imgs

    # MENU / GAME FLOW
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
            Button(sx, 470, 260, 40, "Back to Menu", self.font_med, self.back_to_menu),
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
        self.last_ai_time = time.time()

        self.gs = create_sample_game_state()

        self.last_actions = {Player.MAX: "None", Player.MIN: "None"}
        self.move_count = 0
        self.explosions = []
        self.damage_flashes = []
        self.game_over_played = False

        if self.mode == "AI_VS_AI":
            self.agent_max = load_agent(self.ai1_type, depth=3)
        else:
            self.agent_max = None

        self.agent_min = load_agent(self.ai2_type, depth=3)
        self.setup_game_buttons()

        # Nhạc nền trận đấu
        self.play_bgm("battle")

    def back_to_menu(self):
        self.state = "MENU"
        self.damage_flashes = []
        self.play_bgm("menu")

    def toggle_pause(self):
        self.paused = not self.paused

    def step_ai(self):
        if not self.paused:
            self.paused = True
        self._do_ai_turn()

    # HIỆU ỨNG
    def _create_explosion(self, pos):
        r, c = pos
        cx, cy = c * CELL_SIZE + CELL_SIZE//2, r * CELL_SIZE + CELL_SIZE//2
        self.explosions.append({
            "x": cx, "y": cy,
            "scale": 0.5,
            "alpha": 255
        })

    def _add_damage_flash(self, pos, entity_type):
        for f in self.damage_flashes:
            if f["pos"] == pos and f["type"] == entity_type:
                f["timer"] = DAMAGE_FLASH_FRAMES
                return
        self.damage_flashes.append({
            "pos": pos,
            "type": entity_type,
            "timer": DAMAGE_FLASH_FRAMES
        })

    def _check_destruction_and_damage(self, old_state, new_state):
        for pos in old_state.walls:
            if pos not in new_state.walls:
                self._create_explosion(pos)
                self.play_sound("destroyed")
        for player, tank in old_state.tanks.items():
            if player not in new_state.tanks:
                self._create_explosion(tank.position)
                self.play_sound("destroyed")
        for player, base in old_state.bases.items():
            if player not in new_state.bases:
                self._create_explosion(base.position)
                self.play_sound("destroyed")

        for pos, wall in old_state.walls.items():
            if pos in new_state.walls and new_state.walls[pos].hp < wall.hp:
                self._add_damage_flash(pos, "wall")
                self.play_sound("bullet_hit")
        for player, tank in old_state.tanks.items():
            if player in new_state.tanks:
                new_tank = new_state.tanks[player]
                if new_tank.hp < tank.hp:
                    self._add_damage_flash(new_tank.position, "tank")
                    self.play_sound("bullet_hit")
        for player, base in old_state.bases.items():
            if player in new_state.bases:
                new_base = new_state.bases[player]
                if new_base.hp < base.hp:
                    self._add_damage_flash(new_base.position, "base")
                    self.play_sound("bullet_hit")

    def _apply_action(self, action):
        if self.gs.is_terminal():
            return

        current_player = self.gs.current_player
        old_gs = self.gs
        new_gs = self.gs.apply_action(action)

        if action == Action.FIRE:
            self.play_sound("tank_fire")
        elif action in (Action.MOVE_UP, Action.MOVE_DOWN, Action.MOVE_LEFT, Action.MOVE_RIGHT):
            old_tank = old_gs.tanks.get(current_player)
            new_tank = new_gs.tanks.get(current_player)
            if old_tank and new_tank and old_tank.position != new_tank.position:
                self.play_sound("tank_move")

        self.gs = new_gs
        self._check_destruction_and_damage(old_gs, new_gs)
        self.last_actions[current_player] = action.name.replace("_", " ")
        self.move_count += 1

        if new_gs.is_terminal() and not self.game_over_played:
            self.play_sound("game_over")
            self.stop_bgm()
            self.game_over_played = True

    def _do_ai_turn(self):
        if self.gs.is_terminal():
            return

        current_player = self.gs.current_player
        agent = self.agent_max if current_player == Player.MAX else self.agent_min

        if agent:
            action = agent.choose_action(self.gs)
            if action:
                self._apply_action(action)

            self.last_ai_time = time.time()

    # VẼ
    def _draw_damage_flash(self, surface, pos, entity_type, rect):
        for f in self.damage_flashes:
            if f["pos"] == pos and f["type"] == entity_type:
                alpha = int(MAX_FLASH_ALPHA * (f["timer"] / DAMAGE_FLASH_FRAMES))
                if alpha <= 0:
                    return
                flash = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                if entity_type == "tank":
                    pygame.draw.circle(flash, (255, 255, 255, alpha),
                                       (rect.width // 2, rect.height // 2),
                                       rect.width // 2)
                else:
                    flash.fill((255, 255, 255, alpha))
                surface.blit(flash, rect.topleft)
                return

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

        # 1. Walls
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

            self._draw_damage_flash(board_surf, wall.position, "wall", rect)

        # 2. Bases
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

            self._draw_damage_flash(board_surf, base.position, "base", rect)

        # 3. Tanks
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

            self._draw_damage_flash(board_surf, tank.position, "tank", rect)

        # 4. Bullets
        for bullet in self.gs.bullets:
            r, c = bullet.position
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            if self.images["bullet"]:
                angle = DIRECTION_ANGLE.get(bullet.direction, 0)
                rotated_bullet = pygame.transform.rotate(self.images["bullet"], angle)
                bullet_rect = rotated_bullet.get_rect(center=rect.center)
                board_surf.blit(rotated_bullet, bullet_rect)
            else:
                cx, cy = rect.centerx, rect.centery
                pygame.draw.circle(board_surf, COLOR_BULLET, (cx, cy), 5)
                pygame.draw.circle(board_surf, (200, 100, 0), (cx, cy), 5, 1)

        # 5. Explosions
        for exp in self.explosions:
            if exp["alpha"] > 0:
                if self.images["explosion"]:
                    base_img = self.images["explosion"]
                    w = int(base_img.get_width() * exp["scale"])
                    h = int(base_img.get_height() * exp["scale"])
                    scaled_exp = pygame.transform.scale(base_img, (w, h))
                    scaled_exp.set_alpha(int(exp["alpha"]))
                    exp_rect = scaled_exp.get_rect(center=(exp["x"], exp["y"]))
                    board_surf.blit(scaled_exp, exp_rect)
                else:
                    exp_surf = pygame.Surface((exp["scale"]*40, exp["scale"]*40), pygame.SRCALPHA)
                    pygame.draw.circle(exp_surf, (255, 100, 0, int(exp["alpha"])),
                                       (exp["scale"]*20, exp["scale"]*20), exp["scale"]*20)
                    board_surf.blit(exp_surf, (exp["x"] - exp["scale"]*20, exp["y"] - exp["scale"]*20))

        self.screen.blit(board_surf, (0, 0))

        # --- SIDEBAR UI ---
        pygame.draw.rect(self.screen, COLOR_UI_PANEL, (BOARD_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, (0, 0, 0), (BOARD_WIDTH, 0), (BOARD_WIDTH, SCREEN_HEIGHT), 2)

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

        pygame.draw.line(self.screen, (100, 100, 100), (BOARD_WIDTH+20, 140), (SCREEN_WIDTH-20, 140), 1)
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

        pygame.draw.line(self.screen, (100, 100, 100), (BOARD_WIDTH+20, 210), (SCREEN_WIDTH-20, 210), 1)

        step_surf = self.font_med.render(f"Step Count: {self.move_count}", True, (150, 200, 255))
        self.screen.blit(step_surf, (BOARD_WIDTH + 20, 230))

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.game_buttons:
            if btn.text == "Pause / Resume":
                btn.is_active = self.paused
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)

        if self.gs.is_terminal():
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            utility = self.gs.get_utility(0)
            if utility > 0:
                winner = "MAX WINS!"
            elif utility < 0:
                winner = "MIN WINS!"
            else:
                winner = "DRAW!"

            win_surf = self.font_large.render(winner, True, COLOR_BULLET)
            win_rect = win_surf.get_rect(center=(BOARD_WIDTH//2, BOARD_HEIGHT//2))
            self.screen.blit(win_surf, win_rect)

    # UPDATE
    def update(self):
        for exp in self.explosions[:]:
            exp["scale"] += 0.05
            exp["alpha"] -= 15
            if exp["alpha"] <= 0:
                self.explosions.remove(exp)

        for f in self.damage_flashes[:]:
            f["timer"] -= 1
            if f["timer"] <= 0:
                self.damage_flashes.remove(f)

        if self.state != "PLAYING" or self.paused or self.gs.is_terminal():
            return

        current_player = self.gs.current_player

        if self.mode == "USER_VS_AI" and current_player == Player.MAX:
            return

        # AI luôn tự chạy khi không pause
        now = time.time()
        if now - self.last_ai_time > self.ai_delay:
            self._do_ai_turn()

    # RUN LOOP
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == "MENU":
                    for btn in self.menu_buttons:
                        if btn.handle_event(event):
                            self.play_sound("button_click")

                elif self.state == "PLAYING":
                    for btn in self.game_buttons:
                        if btn.handle_event(event):
                            self.play_sound("button_click")

                    if event.type == pygame.KEYDOWN:
                        if self.mode == "USER_VS_AI" and self.gs.current_player == Player.MAX and not self.gs.is_terminal():
                            action = None
                            if event.key == pygame.K_w:
                                action = Action.MOVE_UP
                            elif event.key == pygame.K_s:
                                action = Action.MOVE_DOWN
                            elif event.key == pygame.K_a:
                                action = Action.MOVE_LEFT
                            elif event.key == pygame.K_d:
                                action = Action.MOVE_RIGHT
                            elif event.key == pygame.K_SPACE:
                                action = Action.FIRE

                            if action:
                                self._apply_action(action)

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