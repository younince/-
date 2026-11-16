import pygame
import math
import random
import sys

# ==========================================
# 1. 기본 설정 및 모던 라이트 테마
# ==========================================
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 540, 750
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("단단벽 (DanDanBrick)")
clock = pygame.time.Clock()


# ==========================================
# 테마별 처치 사운드 (외부 음원 파일 없이 생성)
# ==========================================
class ThemeSound:
    def __init__(self):
        self.enabled = pygame.mixer.get_init() is not None
        self.cache = {}
        if not self.enabled:
            return

        # 테마마다 음색, 높이, 길이가 다른 짧은 효과음을 미리 생성
        presets = {
            "GRASS":  (520, 0.10, "soft"),
            "NEON":   (880, 0.13, "digital"),
            "MAGIC":  (660, 0.22, "magic"),
            "GOLD":   (310, 0.20, "metal"),
            "SPACE":  (190, 0.30, "cosmic"),
            "GLITCH": (1040, 0.16, "glitch"),
        }
        for key, (freq, duration, style) in presets.items():
            self.cache[key] = self.make_sound(freq, duration, style)

    def make_sound(self, freq, duration, style):
        import struct
        sample_rate = 22050
        total = int(sample_rate * duration)
        raw = bytearray()
        for i in range(total):
            t = i / sample_rate
            progress = i / max(1, total - 1)
            envelope = (1.0 - progress) ** 2
            if style == "digital":
                wave = math.sin(2 * math.pi * freq * t) + 0.35 * math.sin(2 * math.pi * freq * 2.01 * t)
                envelope *= 0.9
            elif style == "magic":
                sweep = freq * (1.0 + 0.7 * progress)
                wave = math.sin(2 * math.pi * sweep * t) + 0.45 * math.sin(2 * math.pi * sweep * 1.5 * t)
            elif style == "metal":
                wave = math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(2 * math.pi * freq * 2.7 * t)
            elif style == "cosmic":
                sweep = freq * (1.0 - 0.55 * progress)
                wave = math.sin(2 * math.pi * sweep * t) + 0.3 * math.sin(2 * math.pi * sweep * 0.5 * t)
            elif style == "glitch":
                wave = math.sin(2 * math.pi * freq * t) * (1 if (i // 90) % 2 == 0 else -0.5)
            else:
                wave = math.sin(2 * math.pi * freq * t) + 0.2 * math.sin(2 * math.pi * freq * 1.8 * t)
            sample = int(max(-1.0, min(1.0, wave * envelope * 0.42)) * 32767)
            raw.extend(struct.pack("<h", sample))
        return pygame.mixer.Sound(buffer=bytes(raw))

    def play_destroy(self, theme_key):
        if self.enabled:
            sound = self.cache.get(theme_key)
            if sound:
                sound.play()

FONT_TITLE = pygame.font.SysFont("malgungothic", 42, bold=True)
FONT_LARGE = pygame.font.SysFont("malgungothic", 24, bold=True)
FONT_MED = pygame.font.SysFont("malgungothic", 18, bold=True)
FONT_SMALL = pygame.font.SysFont("malgungothic", 14, bold=True)
FONT_TINY = pygame.font.SysFont("malgungothic", 12, bold=True)

HEADER_HEIGHT = 80
FOOTER_HEIGHT = 60
FIELD_TOP = HEADER_HEIGHT
FIELD_BOTTOM = HEIGHT - FOOTER_HEIGHT
GRID_ROWS = 9
GRID_COLS = 6
TILE_WIDTH = WIDTH // GRID_COLS
TILE_HEIGHT = (FIELD_BOTTOM - FIELD_TOP) // (GRID_ROWS + 1)
DANGER_Y = FIELD_TOP + (GRID_ROWS - 1) * TILE_HEIGHT

# ==========================================
# 2. 챕터 및 맵 테마 데이터 정의
# ==========================================
CHAPTERS = [
    {
        "id": 1, "name": "제 1관문 : 초원의 성벽", "start_stage": 1, "max_stage": 20,
        "desc": "단단벽의 입구. 기본 블록과 첫 수호자가 등장합니다.",
        "rewards": [("관문 클리어", "💎 300"), ("방어선 50% 유지", "💎 500"), ("완벽 클리어", "💎 800")]
    },
    {
        "id": 2, "name": "제 2관문 : 네온 요새", "start_stage": 21, "max_stage": 40,
        "desc": "단단한 실버/골드 장갑 블록이 대거 출현합니다.",
        "rewards": [("관문 클리어", "💎 500"), ("방어선 50% 유지", "💎 800"), ("완벽 클리어", "💎 1200")]
    },
    {
        "id": 3, "name": "제 3관문 : 마력의 탑", "start_stage": 41, "max_stage": 60,
        "desc": "높은 체력의 다이아 블록을 속성 구체로 돌파하세요.",
        "rewards": [("관문 클리어", "💎 800"), ("방어선 50% 유지", "💎 1200"), ("완벽 클리어", "💎 1800")]
    },
    {
        "id": 4, "name": "제 4관문 : 황금 미궁", "start_stage": 61, "max_stage": 80,
        "desc": "거대 보스 군단이 몰려오는 고난이도 구역입니다.",
        "rewards": [("관문 클리어", "💎 1200"), ("방어선 50% 유지", "💎 1800"), ("완벽 클리어", "💎 2500")]
    },
    {
        "id": 5, "name": "제 5관문 : 심연의 핵", "start_stage": 81, "max_stage": 100,
        "desc": "최종 100스테이지까지 이어지는 극한의 시험장입니다.",
        "rewards": [("관문 클리어", "💎 2000"), ("방어선 50% 유지", "💎 3000"), ("완벽 클리어", "💎 5000")]
    }
]

MAP_THEMES = {
    "GRASS": {
        "key": "GRASS", "name": "초원의 시작", "grade": "일반", "color": (100, 180, 100),
        "bg": (240, 244, 250), "block": (100, 120, 150), "particle": (60, 140, 240)
    },
    "NEON": {
        "key": "NEON", "name": "네온 시티", "grade": "희귀", "color": (0, 240, 255),
        "bg": (15, 18, 30), "block": (35, 40, 55), "particle": (0, 240, 255)
    },
    "MAGIC": {
        "key": "MAGIC", "name": "마법사의 서재", "grade": "영웅", "color": (180, 80, 220),
        "bg": (30, 20, 45), "block": (70, 45, 90), "particle": (180, 60, 220)
    },
    "GOLD": {
        "key": "GOLD", "name": "황금 사막 유적", "grade": "전설", "color": (255, 200, 0),
        "bg": (50, 35, 20), "block": (120, 90, 40), "particle": (255, 215, 0)
    },
    "SPACE": {
        "key": "SPACE", "name": "성운의 심장부", "grade": "신화", "color": (255, 50, 150),
        "bg": (10, 10, 25), "block": (50, 20, 70), "particle": (255, 20, 147)
    },
    "GLITCH": {
        "key": "GLITCH", "name": "디지털 글리치", "grade": "초월", "color": (50, 255, 100),
        "bg": (5, 15, 10), "block": (20, 60, 30), "particle": (50, 255, 100)
    }
}

ALL_SKILLS = [
    {"id": "ICE", "name": "빙결의 구체", "desc": "적을 1턴간 얼림. 해제 직후 다음 턴은 재빙결 면역"},
    {"id": "ELEC", "name": "전뇌의 구체", "desc": "충돌 시 주변 적들에게 도트 피해"},
    {"id": "FIRE", "name": "화염의 구체", "desc": "단일 적에게 강력한 지속 화염 피해"},
    {"id": "BOMB", "name": "폭발의 구체", "desc": "충돌 시 넓은 범위 폭발 피해"},
    {"id": "CROSS", "name": "십자 구체", "desc": "십자 방향 마력 빔 방출"},
    {"id": "LINE", "name": "일자 구체", "desc": "가로 방향 마력 빔 방출"},
    {"id": "DIR4", "name": "동서남북 구체", "desc": "4방향 관통 빔 방출"},
    {"id": "ULTIMATE", "name": "단단 파괴공", "desc": "닿은 적에게만 3턴간 7 지속딜 (보스 2배, 획득당 공+2개)"},
    {"id": "DUPLICATE", "name": "복제공", "desc": "벽에 맞으면 2개의 복제공으로 분열 (복제공은 재복제 불가)"},
    {"id": "CORROSION", "name": "부식공", "desc": "맞은 벽이 5초간 부식되어 모든 피해를 2배로 받음"},
    {"id": "EXECUTION", "name": "처형공", "desc": "체력이 최대치의 5% 미만인 벽을 즉시 파괴하고 기본공 15개 발사"},
    {"id": "LASER_TRAIL", "name": "레이저공", "desc": "지나간 자취가 남고 다음 턴 이동한 벽에 최대 체력의 3% 피해"},
    {"id": "SPEED", "name": "신속공", "desc": "1초마다 속도 0.5 증가, 경과 시간에 비례해 공격력 증가"},
    {"id": "EXPLOSIVE", "name": "폭파공", "desc": "벽에 3번 맞으면 폭발하여 주변에 공격력의 5배 피해"},
    {"id": "BOUNCE", "name": "바운스공", "desc": "회수 지점에서 1회 더 튕기며 공격, 두 번째 도달 시 회수"},
    {"id": "MOSQUITO", "name": "모기공", "desc": "벽에 붙어 3초간 체력을 흡수하며 커지고, 이후 조금 느려짐"},
    {"id": "CAPACITY", "name": "기반 마력 확장", "desc": "기본 발사 구체 수 +2 증가"}
]

# 로비의 영구 구체 강화 목록. 강화는 챕터를 새로 시작해도 유지된다.
UPGRADE_INFO = [
    ("NORMAL", "기본 구체", "적중 시 직접 피해 증가"),
    ("ICE", "빙결 구체", "강화 단계마다 주변 적 1명 추가 빙결"),
    ("FIRE", "화염 구체", "화상 피해와 지속 턴 증가"),
    ("ELEC", "전기 구체", "전기 도트 피해 증가"),
    ("BOMB", "폭발 구체", "폭발 피해 및 범위 증가"),
    ("CROSS", "십자 구체", "십자 빔 피해 증가"),
    ("LINE", "일자 구체", "가로 빔 피해 증가"),
    ("DIR4", "4방향 구체", "4방향 빔 피해 증가"),
    ("ULTIMATE", "단단 파괴공", "충돌 피해와 지속 피해/턴 증가"),
    ("DUPLICATE", "복제공", "복제공의 공격력 증가"),
    ("CORROSION", "부식공", "부식 지속 시간 증가"),
    ("EXECUTION", "처형공", "즉시 처형 가능한 체력 기준 증가"),
    ("LASER_TRAIL", "레이저공", "레이저 자취 피해 비율 증가"),
    ("SPEED", "신속공", "가속도와 시간당 공격력 증가"),
    ("EXPLOSIVE", "폭파공", "폭발 피해 배율 증가"),
    ("BOUNCE", "바운스공", "바운스공의 직접 공격력 증가"),
    ("MOSQUITO", "모기공", "흡혈 피해량과 성장 크기 증가"),
]

# ==========================================
# 3. 게임 객체 클래스 정의
# ==========================================

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = color
        self.radius = random.randint(3, 6)
        self.life = 1.0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.05

    def draw(self, surface):
        if self.life > 0:
            alpha = max(0, min(255, int(255 * self.life)))
            r, g, b = self.color
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha), (self.radius, self.radius), self.radius)
            surface.blit(s, (self.x - self.radius, self.y - self.radius))

class LaserEffect:
    def __init__(self, x, y, direction, color):
        self.x, self.y = int(x), int(y)
        self.direction = direction
        self.color = color
        self.life = 1.0

    def update(self):
        self.life -= 0.055

    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = max(0, min(255, int(235 * self.life)))
        pulse = 1.0 + (1.0 - self.life) * 0.8
        core = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        if self.direction == "DIR4":
            lines = [((self.x, self.y), (self.x, FIELD_TOP)),
                     ((self.x, self.y), (self.x, FIELD_BOTTOM)),
                     ((self.x, self.y), (0, self.y)),
                     ((self.x, self.y), (WIDTH, self.y))]
            width = max(3, int(9 * pulse))
        elif self.direction == "LINE":
            lines = [((0, self.y), (WIDTH, self.y))]
            width = max(3, int(10 * pulse))
        else:
            lines = [((self.x, FIELD_TOP), (self.x, FIELD_BOTTOM)),
                     ((0, self.y), (WIDTH, self.y))]
            width = max(3, int(8 * pulse))

        for p1, p2 in lines:
            pygame.draw.line(glow, (*self.color, int(alpha * 0.28)), p1, p2, width * 4)
            pygame.draw.line(core, (*self.color, alpha), p1, p2, width)
            pygame.draw.line(core, (245, 255, 255, alpha), p1, p2, max(1, width // 3))

        radius = int(9 + (1.0 - self.life) * 22)
        pygame.draw.circle(glow, (*self.color, int(alpha * 0.45)),
                           (self.x, self.y), radius * 2)
        pygame.draw.circle(core, (245, 255, 255, alpha),
                           (self.x, self.y), max(3, radius // 2), 2)
        surface.blit(glow, (0, 0))
        surface.blit(core, (0, 0))


class ExplosionEffect:
    def __init__(self, x, y):
        self.x, self.y = int(x), int(y)
        self.life = 1.0

    def update(self):
        self.life -= 0.065

    def draw(self, surface):
        if self.life <= 0:
            return
        progress = 1.0 - self.life
        alpha = max(0, min(255, int(230 * self.life)))
        radius = int(8 + progress * 58)
        fx = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(fx, (255, 95, 35, alpha), (self.x, self.y),
                           radius, max(2, int(8 * self.life)))
        pygame.draw.circle(fx, (255, 205, 85, alpha), (self.x, self.y),
                           max(3, int(radius * 0.62)), max(2, int(5 * self.life)))
        pygame.draw.circle(fx, (255, 245, 205, alpha), (self.x, self.y),
                           max(2, int(radius * 0.25)))
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            p1 = (int(self.x + math.cos(rad) * radius * 0.72),
                  int(self.y + math.sin(rad) * radius * 0.72))
            p2 = (int(self.x + math.cos(rad) * radius * 1.12),
                  int(self.y + math.sin(rad) * radius * 1.12))
            pygame.draw.line(fx, (255, 225, 135, alpha), p1, p2, 3)
        surface.blit(fx, (0, 0))

class Block:
    def __init__(self, col, row, hp, block_type="normal", theme_data=None):
        self.col = col
        self.row = row
        self.hp = hp
        self.max_hp = hp
        self.type = block_type
        self.frozen = False
        # 빙결 직후 다음 턴에는 재빙결되지 않도록 하는 1턴 면역
        self.freeze_immunity = 0
        self.dot_fire = 0
        self.dot_fire_dmg = 1
        self.dot_elec = 0
        self.dot_ult = 0
        self.dot_ult_dmg = 0
        self.corrosion_until = 0
        self.theme = theme_data

    def get_rect(self):
        x = self.col * TILE_WIDTH + 3
        y = FIELD_TOP + self.row * TILE_HEIGHT + 3
        w = TILE_WIDTH - 6
        h = TILE_HEIGHT - 6
        if self.type == "boss":
            w = TILE_WIDTH * 2 - 6
            h = TILE_HEIGHT * 2 - 6
        return pygame.Rect(x, y, w, h)

    def draw(self, surface):
        rect = self.get_rect()
        if self.type == "boss":
            base_color = (220, 80, 90)
        elif self.type == "silver":
            base_color = (170, 185, 200)
        elif self.type == "gold":
            base_color = (245, 190, 50)
        elif self.type == "diamond":
            base_color = (60, 190, 220)
        else:
            base_color = self.theme["block"] if self.theme else (100, 120, 150)
        if self.frozen:
            base_color = (105, 185, 235)

        theme_key = self.theme.get("key", "GRASS") if self.theme else "GRASS"
        accent = self.theme.get("color", (255, 255, 255)) if self.theme else (255, 255, 255)
        pygame.draw.rect(surface, base_color, rect, border_radius=8)

        if theme_key in ("NEON", "GLITCH"):
            pygame.draw.rect(surface, accent, rect, 2, border_radius=8)
            pygame.draw.line(surface, (255, 255, 255), (rect.left + 7, rect.top + 5),
                             (rect.right - 7, rect.top + 5), 1)
            if theme_key == "GLITCH":
                pygame.draw.line(surface, (255, 70, 110), (rect.left + 4, rect.bottom - 5),
                                 (rect.right - 4, rect.bottom - 5), 2)
        elif theme_key in ("MAGIC", "SPACE"):
            pygame.draw.rect(surface, accent, rect, 2, border_radius=8)
            pygame.draw.circle(surface, (245, 235, 255), rect.center,
                               max(3, min(rect.width, rect.height)//7), 1)
            pygame.draw.circle(surface, accent, rect.center,
                               max(5, min(rect.width, rect.height)//3), 1)
        elif theme_key == "GOLD":
            pygame.draw.rect(surface, (255, 225, 130), rect, 3, border_radius=8)
            pygame.draw.line(surface, (255, 245, 190), (rect.left + 5, rect.top + 6),
                             (rect.right - 5, rect.top + 6), 2)
        else:
            pygame.draw.rect(surface, (220, 235, 220), rect, 2, border_radius=8)

        # 화염 상태: 블록 위로 불꽃이 솟고 붉은 테두리가 점멸
        if self.dot_fire > 0:
            tick = pygame.time.get_ticks() / 90.0
            for i in range(4):
                fx = rect.left + 7 + i * max(7, (rect.width - 14) // 4)
                wobble = int(math.sin(tick + i * 1.7) * 3)
                flame_h = 8 + (i % 2) * 4
                pygame.draw.polygon(surface, (255, 95, 25), [
                    (fx - 4, rect.top + 5), (fx + wobble, rect.top - flame_h),
                    (fx + 4, rect.top + 5)])
                pygame.draw.polygon(surface, (255, 210, 65), [
                    (fx - 2, rect.top + 4), (fx + wobble, rect.top - flame_h + 5),
                    (fx + 2, rect.top + 4)])
            pygame.draw.rect(surface, (255, 95, 25), rect, 2, border_radius=8)

        # 전기 상태: 노란 번개가 적 주위를 흐르는 모습
        if self.dot_elec > 0:
            tick = pygame.time.get_ticks() // 100
            for i in range(2):
                ex = rect.left + 8 + ((i * 19 + tick * 3) % max(1, rect.width - 16))
                ey = rect.top + 4 + (i * 11) % max(1, rect.height - 8)
                pygame.draw.lines(surface, (255, 245, 80), False,
                                  [(ex, ey), (ex - 4, ey + 6), (ex + 2, ey + 7),
                                   (ex - 2, ey + 13)], 3)
            pygame.draw.rect(surface, (255, 220, 40), rect, 2, border_radius=8)

        # 빙결 상태: 푸른 얼음막과 결정 파편이 적에게 붙어 있음
        if self.frozen:
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            overlay.fill((115, 220, 255, 75))
            surface.blit(overlay, rect.topleft)
            pygame.draw.rect(surface, (165, 240, 255), rect, 3, border_radius=8)
            cx, cy = rect.center
            pygame.draw.line(surface, (235, 255, 255), (cx, rect.top + 4),
                             (cx, rect.bottom - 4), 2)
            pygame.draw.line(surface, (235, 255, 255), (rect.left + 5, cy),
                             (rect.right - 5, cy), 2)
            pygame.draw.line(surface, (210, 250, 255), (rect.left + 8, rect.top + 7),
                             (rect.right - 8, rect.bottom - 7), 1)
            pygame.draw.line(surface, (210, 250, 255), (rect.right - 8, rect.top + 7),
                             (rect.left + 8, rect.bottom - 7), 1)
            for px, py in [(rect.left + 5, rect.top + 5), (rect.right - 5, rect.top + 5),
                           (rect.left + 5, rect.bottom - 5), (rect.right - 5, rect.bottom - 5)]:
                pygame.draw.polygon(surface, (225, 250, 255), [
                    (px, py - 4), (px + 3, py), (px, py + 4), (px - 3, py)])

        if self.dot_ult > 0:
            pygame.draw.rect(surface, (220, 50, 120), rect, 2, border_radius=8)

        if pygame.time.get_ticks() < self.corrosion_until:
            pygame.draw.rect(surface, (125, 255, 105), rect, 3, border_radius=8)
            for i in range(3):
                px = rect.left + 8 + i * max(8, rect.width // 4)
                pygame.draw.circle(surface, (175, 255, 125), (px, rect.bottom - 7 - (i % 2) * 5), 2)

        txt = FONT_MED.render(str(self.hp), True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=rect.center))

class Ball:
    def __init__(self, x, y, vx, vy, ball_type="NORMAL", is_clone=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 10 if ball_type == "ULTIMATE" else 7
        self.type = ball_type
        self.is_clone = is_clone
        self.has_split = False
        self.hit_count = 0
        self.bounce_count = 0
        self.created_at = pygame.time.get_ticks()
        self.speed_factor = 1.0
        self.last_trail_x = x
        self.last_trail_y = y
        # 모기공 흡혈 상태
        self.attached_block = None
        self.last_siphoned_block = None
        self.attach_started = 0
        self.siphon_damage_applied = 0
        self.siphon_start_radius = self.radius
        self.siphon_vx = vx
        self.siphon_vy = vy
        # 말라리아 모기공은 흡혈한 적을 기억해 같은 적을 반복 방문하지 않는다.
        self.malaria_hit_ids = set()
        self.malaria_power = 1.0

    def draw(self, surface):
        x, y, r = int(self.x), int(self.y), self.radius
        palette = {
            "NORMAL": ((65, 145, 255), (220, 240, 255)),
            "ICE": ((85, 210, 255), (235, 255, 255)),
            "FIRE": ((245, 75, 25), (255, 225, 90)),
            "ELEC": ((255, 215, 35), (255, 255, 190)),
            "BOMB": ((95, 75, 90), (255, 110, 70)),
            "CROSS": ((190, 100, 255), (245, 220, 255)),
            "LINE": ((70, 235, 190), (220, 255, 245)),
            "DIR4": ((255, 90, 180), (255, 225, 245)),
            "ULTIMATE": ((255, 55, 125), (255, 235, 245)),
            "DUPLICATE": ((125, 110, 255), (230, 225, 255)),
            "CORROSION": ((105, 190, 65), (225, 255, 150)),
            "EXECUTION": ((220, 35, 65), (255, 225, 225)),
            "LASER_TRAIL": ((40, 220, 245), (245, 255, 255)),
            "SPEED": ((255, 175, 35), (255, 250, 190)),
            "EXPLOSIVE": ((90, 65, 55), (255, 145, 60)),
            "BOUNCE": ((50, 210, 160), (225, 255, 245)),
            "MOSQUITO": ((125, 65, 155), (255, 125, 185)),
        }
        color, highlight = palette.get(self.type, palette["NORMAL"])
        pygame.draw.circle(surface, color, (x, y), r)
        pygame.draw.circle(surface, highlight, (x - 2, y - 2), max(2, r // 3))
        if self.type == "ICE":
            pygame.draw.polygon(surface, (230, 255, 255), [
                (x, y-r-3), (x+3, y-2), (x+r+3, y), (x+2, y+3),
                (x, y+r+3), (x-3, y+2), (x-r-3, y), (x-2, y-3)], 2)
        elif self.type == "FIRE":
            pygame.draw.polygon(surface, (255, 225, 75), [
                (x, y-r-5), (x+4, y-1), (x, y+r+2), (x-4, y-1)])
        elif self.type == "ELEC":
            pygame.draw.lines(surface, (255, 255, 210), False,
                              [(x-2, y-r-4), (x+2, y-1), (x-2, y+1), (x+3, y+r+4)], 2)
        elif self.type == "BOMB":
            pygame.draw.circle(surface, (255, 160, 80), (x, y), r + 3, 2)
            pygame.draw.circle(surface, (65, 45, 55), (x, y), max(2, r - 3), 1)
            pygame.draw.line(surface, (255, 235, 150), (x + 2, y - r + 1), (x + 6, y - r - 5), 2)
            pygame.draw.circle(surface, (255, 225, 95), (x + 6, y - r - 5), 2)
        elif self.type == "DIR4":
            pygame.draw.line(surface, highlight, (x-r-5, y), (x+r+5, y), 2)
            pygame.draw.line(surface, highlight, (x, y-r-5), (x, y+r+5), 2)
        elif self.type == "LINE":
            pygame.draw.line(surface, highlight, (x-r-7, y), (x+r+7, y), 3)
        elif self.type == "ULTIMATE":
            angle = math.atan2(self.vy, self.vx)
            back_x = x - math.cos(angle) * (r + 5)
            back_y = y - math.sin(angle) * (r + 5)
            pygame.draw.line(surface, (105, 45, 75), (int(back_x), int(back_y)), (x, y), 5)
            pygame.draw.ellipse(surface, (65, 35, 55), (x-r-3, y+r-2, r*2+6, max(4, r//2)))
            pts = [(x-r, y-r//2), (x-r//2, y-r), (x+r//2, y-r),
                   (x+r, y-r//2), (x+r, y+r//2), (x+r//2, y+r),
                   (x-r//2, y+r), (x-r, y+r//2)]
            pygame.draw.polygon(surface, (105, 55, 75), pts)
            pygame.draw.polygon(surface, (235, 100, 145), pts, 2)
        elif self.type == "DUPLICATE":
            pygame.draw.circle(surface, (255, 255, 255), (x, y), r + 3, 1)
            pygame.draw.circle(surface, highlight, (x + 3, y), 3)
        elif self.type == "CORROSION":
            pygame.draw.circle(surface, (65, 115, 35), (x, y), r + 2, 2)
            pygame.draw.circle(surface, (245, 255, 170), (x + 2, y + 2), 2)
        elif self.type == "EXECUTION":
            pygame.draw.polygon(surface, (255, 245, 245), [(x, y-r-4), (x+r+4, y), (x, y+r+4), (x-r-4, y)])
        elif self.type == "LASER_TRAIL":
            pygame.draw.circle(surface, (255, 255, 255), (x, y), r + 3, 1)
            pygame.draw.line(surface, (255, 255, 255), (x-r-4, y), (x+r+4, y), 2)
        elif self.type == "SPEED":
            pygame.draw.line(surface, (255, 255, 225), (x-r-7, y-4), (x-2, y-4), 2)
            pygame.draw.line(surface, (255, 255, 225), (x-r-5, y+3), (x-1, y+3), 2)
        elif self.type == "EXPLOSIVE":
            pygame.draw.circle(surface, (255, 155, 70), (x, y), r + 3, 2)
            pygame.draw.line(surface, (255, 240, 160), (x, y-r-3), (x+4, y-r-8), 2)
        elif self.type == "BOUNCE":
            pygame.draw.arc(surface, (235, 255, 250), (x-r+1, y-r+1, r*2-2, r*2-2), 0.2, 2.8, 2)
            pygame.draw.arc(surface, (235, 255, 250), (x-r+1, y-r+1, r*2-2, r*2-2), 3.4, 6.0, 2)
        elif self.type in ("MOSQUITO", "MALARIA"):
            # 말라리아 모기공은 붉은빛 날개와 강화된 흡혈 침으로 구분
            wing = (255, 115, 135) if self.type == "MALARIA" else (220, 205, 255)
            pygame.draw.ellipse(surface, wing, (x-r-5, y-r-4, 8, 6), 1)
            pygame.draw.ellipse(surface, wing, (x+r-3, y-r-4, 8, 6), 1)
            pygame.draw.line(surface, (255, 220, 235), (x, y), (x+2, y+r+6), 2)
            pygame.draw.circle(surface, (255, 45, 75) if self.type == "MALARIA" else (255, 90, 150), (x, y), max(2, r//3), 1)
            if self.type == "MALARIA":
                pygame.draw.circle(surface, (255, 230, 90), (x, y), r + 3, 1)

# ==========================================
# 4. 메인 게임 클래스 및 로직
# ==========================================

class Game:
    def __init__(self):
        self.state = "TOUCH_START"
        self.touch_alpha_timer = 0
        self.transition_alpha = 0
        self.loading_progress = 0.0
        
        self.main_tab = "LOBBY"
        
        # 재화 및 계정 데이터
        self.diamonds = 2500
        self.stamina = 30
        self.max_stamina = 50
        self.upgrade_levels = {key: 0 for key, _, _ in UPGRADE_INFO}
        self.upgrade_btns = []
        self.upgrade_msg = ""
        self.free_gacha_available = True
        self.owned_themes = ["GRASS"]
        self.equipped_theme = "GRASS"
        self.gacha_result_msg = ""
        self.theme_sound = ThemeSound()
        
        # 상점 및 초보자 패키지 구매 여부
        self.beginner_pack_purchased = False
        self.shop_msg = ""
        self.shop_selected_item = None
        self.shop_quantity = 1
        self.shop_slider_dragging = False
        self.shop_slider_rect = pygame.Rect(WIDTH // 2 - 115, HEIGHT // 2 + 12, 230, 12)
        self.shop_confirm_btn = pygame.Rect(WIDTH // 2 - 115, HEIGHT // 2 + 82, 145, 38)
        self.shop_cancel_btn = pygame.Rect(WIDTH // 2 + 40, HEIGHT // 2 + 82, 75, 38)

        # 이벤트 수령 상태
        self.event_claimed = False
        self.event_msg = ""

        # 챕터 선택 변수
        self.selected_chapter_idx = 0
        self.cleared_chapters = set()
        self.chapter_status_msg = ""
        # 말라리아 모기공 각성 연출 상태
        self.awakening_started_at = 0
        self.awakening_duration = 2200
        self.target_max_stage = 20
        self.victory_reward = 300

        # UI 버튼 영역 (상단 및 하단)
        self.surrender_btn = pygame.Rect(WIDTH - 105, 45, 90, 28)
        self.skip_btn = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 48, 180, 36)
        
        self.shop_btn = pygame.Rect(15, 42, 75, 30)
        self.event_btn = pygame.Rect(98, 42, 80, 30)
        self.quest_btn = pygame.Rect(WIDTH - 170, 42, 80, 30)
        self.gacha_btn = pygame.Rect(WIDTH - 83, 42, 70, 30)
        
        self.tab_inven_btn = pygame.Rect(WIDTH // 2 - 140, HEIGHT - 50, 90, 40)
        self.tab_lobby_btn = pygame.Rect(WIDTH // 2 - 45, HEIGHT - 50, 90, 40)
        self.tab_upgrade_btn = pygame.Rect(WIDTH // 2 + 50, HEIGHT - 50, 90, 40)
        
        self.stage_start_btn = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2 + 30, 220, 55)

        # 팝업 창 내부 버튼 영역 (상점 팝업)
        self.popup_close_btn = pygame.Rect(WIDTH // 2 + 115, HEIGHT // 2 - 175, 40, 32)
        self.buy_pack_btn = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 - 110, 260, 48)
        self.buy_stamina_btn = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 - 45, 260, 45)

        # 이벤트 팝업 내부 버튼
        self.claim_event_btn = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2 + 10, 220, 50)

        # 뽑기 팝업 내부 버튼
        self.gacha_action_btn = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2 + 80, 220, 50)

        # 스테이지 선택창 버튼
        self.chap_prev_btn = pygame.Rect(22, HEIGHT // 2 - 45, 36, 70)
        self.chap_next_btn = pygame.Rect(WIDTH - 58, HEIGHT // 2 - 45, 36, 70)
        self.chap_close_btn = pygame.Rect(WIDTH - 85, 115, 50, 32)
        self.sweep_btn = pygame.Rect(65, HEIGHT // 2 + 135, 175, 58)
        self.enter_stage_btn = pygame.Rect(255, HEIGHT // 2 + 135, 220, 58)

        self.stage = 1
        self.level = 1
        self.exp = 0
        self.max_exp = 30
        self.base_ball_count = 5
        self.skills = {}
        self.ultimate_acquisitions = 0
        self.pending_levelup = False
        # 관문 클리어 후 다음 관문으로 넘어갈 때 성장 상태를 이어받는다.
        self.carryover_ready = False
        
        self.blocks = []
        self.balls = []
        self.mosquito_ball_count = 0
        self.malaria_ball_count = 0
        self.mosquito_eggs = []  # 다음 턴 시작 시 부화할 알
        self.particles = []
        self.lasers = []
        self.laser_trails = []  # 레이저공이 남긴 선분: 공 회수 후에도 다음 턴까지 유지
        self.explosions = []
        
        self.launcher_x = WIDTH // 2
        self.launcher_y = FIELD_BOTTOM - 12
        self.aim_angle = -math.pi / 2
        self.is_aiming = False
        
        self.spawn_queue = []
        self.spawn_timer = 0
        self.skill_choices = []

    def start_chapter(self, chap):
        self.stage = chap["start_stage"]
        self.target_max_stage = chap["max_stage"]

        # 첫 관문은 기본 상태로 시작하고, 이전 관문을 클리어한 뒤라면
        # 레벨/경험치/최대 경험치/공 구성/획득 스킬을 그대로 이어받는다.
        if not self.carryover_ready:
            self.level = 1
            self.exp = 0
            self.max_exp = 30
            self.base_ball_count = 5
            self.skills = {}
            self.ultimate_acquisitions = 0
            self.mosquito_ball_count = 0
            self.malaria_ball_count = 0
            self.pending_levelup = False

        # carryover_ready가 True일 때는 미처 선택하지 못한 레벨업도 보존한다.
        self.carryover_ready = False

        # 전투 필드와 진행 중인 투사체만 새 관문에 맞게 초기화한다.
        # 공의 종류와 수량은 위에서 보존한 성장 데이터로 다시 구성된다.
        self.blocks.clear()
        self.balls.clear()
        self.mosquito_eggs.clear()
        self.particles.clear()
        self.lasers.clear()
        self.laser_trails.clear()
        self.spawn_queue.clear()
        self.setup_stage()
        if self.pending_levelup:
            self.pending_levelup = False
            self.trigger_level_up()
        else:
            self.state = "AIMING"

    def setup_stage(self):
        self.blocks.clear()
        self.spawn_new_row()

    def damage_block(self, block, amount):
        """부식 중인 벽은 모든 종류의 피해를 2배로 받는다."""
        if block not in self.blocks:
            return
        multiplier = 2 if pygame.time.get_ticks() < block.corrosion_until else 1
        block.hp -= max(1, int(math.ceil(amount * multiplier)))
        if block.hp <= 0:
            self.destroy_block(block)

    def record_laser_trail(self, ball, force=False):
        if ball.type != "LASER_TRAIL":
            return
        dx = ball.x - ball.last_trail_x
        dy = ball.y - ball.last_trail_y
        if force or dx * dx + dy * dy >= 25:
            if dx * dx + dy * dy >= 1:
                self.laser_trails.append((ball.last_trail_x, ball.last_trail_y, ball.x, ball.y))
            ball.last_trail_x, ball.last_trail_y = ball.x, ball.y

    def apply_laser_trails(self):
        """벽이 한 칸 이동한 다음 레이저 선에 닿은 벽마다 한 번만 피해를 준다."""
        if not self.laser_trails:
            return
        hit_blocks = set()
        for block in list(self.blocks):
            rect = block.get_rect()
            for x1, y1, x2, y2 in self.laser_trails:
                if rect.clipline((int(x1), int(y1)), (int(x2), int(y2))):
                    hit_blocks.add(block)
                    break
        for block in list(hit_blocks):
            if block in self.blocks:
                damage = max(1, math.ceil(block.max_hp * (0.03 + self.upgrade_levels.get("LASER_TRAIL", 0) * 0.005)))
                self.damage_block(block, damage)
        self.laser_trails.clear()

    def hatch_mosquito_eggs(self):
        """이전 턴에 낳은 알을 부화시켜 주변 적에게 모기 떼 피해를 준다."""
        if not self.mosquito_eggs:
            return
        eggs, self.mosquito_eggs = self.mosquito_eggs, []
        for egg in eggs:
            ex, ey = egg["x"], egg["y"]
            radius = TILE_WIDTH * 1.65
            targets = [b for b in self.blocks
                       if math.hypot(b.get_rect().centerx - ex, b.get_rect().centery - ey) <= radius]
            for target in targets:
                self.damage_block(target, max(1, int(target.max_hp * 0.08)))
                rect = target.get_rect()
                for _ in range(7):
                    self.particles.append(Particle(rect.centerx, rect.centery,
                                                   random.choice([(120, 35, 55), (210, 55, 85), (255, 125, 145)])))
            for _ in range(22):
                angle = random.uniform(0, math.tau)
                dist = random.uniform(5, 42)
                self.particles.append(Particle(ex + math.cos(angle) * dist,
                                               ey + math.sin(angle) * dist,
                                               (205, 45, 80)))

    def continue_malaria_chain(self, ball):
        """가장 가까운 미흡혈 적에게 말라리아 모기공을 날려 보낸다."""
        candidates = [b for b in self.blocks if id(b) not in ball.malaria_hit_ids]
        if not candidates:
            ball.attached_block = None
            ball.vx = ball.siphon_vx * 0.8
            ball.vy = ball.siphon_vy * 0.8
            return
        target = min(candidates, key=lambda b: math.hypot(
            b.get_rect().centerx - ball.x, b.get_rect().centery - ball.y))
        rect = target.get_rect()
        dx, dy = rect.centerx - ball.x, rect.centery - ball.y
        distance = max(1.0, math.hypot(dx, dy))
        speed = max(6.0, math.hypot(ball.siphon_vx, ball.siphon_vy))
        ball.vx, ball.vy = dx / distance * speed, dy / distance * speed
        ball.attached_block = None
        ball.last_siphoned_block = None

    def spawn_new_row(self):
        # 기존 적을 한 칸 아래로 이동시킨 직후 방어선 침범 여부를 검사한다.
        for b in self.blocks:
            if not b.frozen:
                b.row += 1
            else:
                b.frozen = False

        # 블럭이 이동한 뒤, 이전 턴에 남겨진 레이저 선과 접촉했는지 판정한다.
        self.apply_laser_trails()
        self.hatch_mosquito_eggs()

        # 이동한 적의 실제 사각형 하단이 최후의 방어선에 닿거나 넘어가면 즉시 패배.
        if any(block.get_rect().bottom >= DANGER_Y for block in self.blocks):
            self.state = "GAME_OVER"
            self.balls.clear()
            self.spawn_queue.clear()
            return

        current_theme_data = MAP_THEMES[self.equipped_theme]

        if self.stage % 20 == 0 and not any(b.type == "boss" for b in self.blocks):
            hp = self.stage * 40
            self.blocks.append(Block(2, 0, hp, "boss", current_theme_data))
            return

        existing_cols = {b.col for b in self.blocks if b.row == 0}
        if any(b.type == "boss" for b in self.blocks):
            existing_cols.update({0, 1, 2, 3, 4, 5})

        available_cols = [c for c in range(GRID_COLS) if c not in existing_cols]
        if not available_cols:
            return

        count = random.randint(1, min(len(available_cols), 2 if self.stage <= 10 else 4))
        cols = random.sample(available_cols, count)
        base_hp = max(1, self.stage * 2 + random.randint(-1, 2))

        for col in cols:
            rand_val = random.random()
            b_type = "normal"
            hp = base_hp
            if self.stage >= 5 and rand_val < 0.1:
                b_type = "diamond"
                hp = base_hp * 3
            elif self.stage >= 3 and rand_val < 0.25:
                b_type = "gold"
                hp = base_hp * 2
            elif rand_val < 0.45:
                b_type = "silver"
                hp = int(base_hp * 1.5)

            self.blocks.append(Block(col, 0, int(hp), b_type, current_theme_data))

    def add_exp(self, amount):
        self.exp += amount
        if self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level += 1
            self.max_exp = int(self.max_exp * 1.4)
            self.pending_levelup = True

    def trigger_level_up(self):
        self.state = "LEVELUP"
        available = [s for s in ALL_SKILLS]
        self.skill_choices = random.sample(available, 3)

    def select_skill(self, skill):
        s_id = skill["id"]
        awakened = False

        if s_id == "CAPACITY":
            self.base_ball_count += 2
        elif s_id == "ULTIMATE":
            self.ultimate_acquisitions += 1
        elif s_id == "MOSQUITO":
            # 모기공을 선택하면 60% 확률로 말라리아 모기공으로 각성한다.
            self.skills[s_id] = self.skills.get(s_id, 0) + 1
            if random.random() < 0.60:
                self.malaria_ball_count += 1
                self.chapter_status_msg = "각성! 말라리아 모기공 획득! (60%)"
                awakened = True
            else:
                self.mosquito_ball_count += 1
                self.chapter_status_msg = "모기공 추가 획득!"
        else:
            if s_id not in self.skills:
                self.skills[s_id] = 1
            else:
                self.skills[s_id] += 1

        if awakened:
            # 각성 연출이 끝난 뒤 다음 스테이지로 넘어가도록 잠시 전투를 멈춘다.
            self.state = "AWAKENING"
            self.awakening_started_at = pygame.time.get_ticks()
        else:
            self.state = "AIMING"
            self.stage += 1
            self.spawn_new_row()

    def upgrade_cost(self, skill_id):
        level = self.upgrade_levels.get(skill_id, 0)
        return 1000 * (level + 1)

    def purchase_upgrade(self, skill_id):
        level = self.upgrade_levels.get(skill_id, 0)
        if level >= 5:
            self.upgrade_msg = "이미 최대 강화 단계입니다."
            return
        cost = self.upgrade_cost(skill_id)
        if self.diamonds < cost:
            self.upgrade_msg = f"다이아가 부족합니다. 필요량: 💎 {cost:,}"
            return
        self.diamonds -= cost
        self.upgrade_levels[skill_id] = level + 1
        name = next((name for key, name, _ in UPGRADE_INFO if key == skill_id), skill_id)
        self.upgrade_msg = f"{name} 강화 성공! Lv.{level + 1}"

    def fire_balls(self):
        self.state = "FIRING"
        self.spawn_queue.clear()
        
        ball_types = ["NORMAL"] * self.base_ball_count + [k for k in self.skills.keys() if k != "MOSQUITO"]
        ball_types.extend(["MOSQUITO"] * self.mosquito_ball_count)
        ball_types.extend(["MALARIA"] * self.malaria_ball_count)
        if self.ultimate_acquisitions > 0:
            ball_types.extend(["ULTIMATE"] * (self.ultimate_acquisitions * 2))

        for i, t in enumerate(ball_types):
            self.spawn_queue.append((t, i * 3))

        self.spawn_timer = 0

    def recall_balls(self):
        if self.state == "FIRING":
            for ball in list(self.balls):
                self.record_laser_trail(ball, force=True)
            self.balls.clear()
            self.spawn_queue.clear()
            self.end_turn()

    def end_turn(self):
        theme_particle_color = MAP_THEMES[self.equipped_theme]["particle"]

        # frozen 상태는 spawn_new_row()가 확인해 해당 턴의 전진을 막은 뒤 해제한다.
        # 빙결되지 않은 상태로 턴이 끝나면 재빙결 면역 1턴을 소모한다.
        for block in self.blocks:
            if not block.frozen and block.freeze_immunity > 0:
                block.freeze_immunity -= 1

        for b in list(self.blocks):
            total_dot = (b.dot_fire * b.dot_fire_dmg) + b.dot_elec + (b.dot_ult_dmg if b.dot_ult > 0 else 0)
            if total_dot > 0:
                self.damage_block(b, total_dot)
                for _ in range(3):
                    self.particles.append(Particle(b.get_rect().centerx, b.get_rect().centery, theme_particle_color))

            b.dot_fire = max(0, b.dot_fire - 1)
            if b.dot_fire == 0:
                b.dot_fire_dmg = 1
            b.dot_elec = max(0, b.dot_elec - 1)
            if b.dot_ult > 0:
                b.dot_ult -= 1
                if b.dot_ult == 0:
                    b.dot_ult_dmg = 0

        for b in self.blocks:
            rect = b.get_rect()
            if rect.bottom >= DANGER_Y:
                self.state = "GAME_OVER"
                return

        if self.stage >= self.target_max_stage and not any(b.type == "boss" for b in self.blocks):
            chap = CHAPTERS[self.selected_chapter_idx]
            self.cleared_chapters.add(chap["id"])
            # 다음 관문 진입 시 현재 레벨과 공/스킬 구성을 이어받도록 표시한다.
            self.carryover_ready = True
            # 목표 스테이지(예: 20스테이지)까지 보스를 처치하면 보상 2배.
            # 목표 스테이지를 넘긴 뒤 처치하면 기본 보상만 지급한다.
            self.victory_reward = 600 if self.stage <= self.target_max_stage else 300
            self.diamonds += self.victory_reward
            self.state = "VICTORY"
            return

        if self.pending_levelup:
            self.pending_levelup = False
            self.trigger_level_up()
            return

        self.stage += 1
        self.spawn_new_row()
        # spawn_new_row()에서 방어선 침범으로 패배 처리했다면 AIMING으로 덮어쓰지 않는다.
        if self.state != "GAME_OVER":
            self.state = "AIMING"

    def destroy_block(self, b):
        if b in self.blocks:
            self.blocks.remove(b)
            self.theme_sound.play_destroy(self.equipped_theme)
            # 적 1명 처치마다 다이아 1~5개를 무작위 지급한다.
            self.diamonds += random.randint(1, 5)
            exp_map = {"normal": 10, "silver": 20, "gold": 40, "diamond": 70, "boss": 300}
            self.add_exp(exp_map.get(b.type, 10))
            
            rect = b.get_rect()
            theme_particle_color = MAP_THEMES[self.equipped_theme]["particle"]
            for _ in range(12):
                self.particles.append(Particle(rect.centerx, rect.centery, theme_particle_color))

    def handle_ball_collision(self, ball):
        if ball not in self.balls:
            return

        if ball.x - ball.radius <= 0:
            ball.x = ball.radius
            ball.vx *= -1
        elif ball.x + ball.radius >= WIDTH:
            ball.x = WIDTH - ball.radius
            ball.vx *= -1

        if ball.y - ball.radius <= FIELD_TOP:
            ball.y = FIELD_TOP + ball.radius
            ball.vy *= -1

        ball_rect = pygame.Rect(int(ball.x - ball.radius), int(ball.y - ball.radius), ball.radius * 2, ball.radius * 2)
        for block in list(self.blocks):
            if block not in self.blocks:
                continue
            b_rect = block.get_rect()
            if not b_rect.colliderect(ball_rect):
                continue

            cx, cy = ball.x, ball.y
            bx, by = b_rect.centerx, b_rect.centery
            intersect_x = min(ball_rect.right, b_rect.right) - max(ball_rect.left, b_rect.left)
            intersect_y = min(ball_rect.bottom, b_rect.bottom) - max(ball_rect.top, b_rect.top)

            if intersect_x < intersect_y:
                if cx < bx:
                    ball.x = b_rect.left - ball.radius
                else:
                    ball.x = b_rect.right + ball.radius
                ball.vx *= -1
            else:
                if cy < by:
                    ball.y = b_rect.top - ball.radius
                else:
                    ball.y = b_rect.bottom + ball.radius
                ball.vy *= -1

            # 모기공은 벽에 부딪히면 즉시 달라붙어 3초간 흡혈한다.
            if (ball.type in ("MOSQUITO", "MALARIA") and ball.attached_block is None
                    and block is not ball.last_siphoned_block
                    and (ball.type != "MALARIA" or id(block) not in ball.malaria_hit_ids)):
                ball.attached_block = block
                ball.attach_started = pygame.time.get_ticks()
                ball.siphon_damage_applied = 0
                ball.siphon_start_radius = ball.radius
                ball.siphon_vx, ball.siphon_vy = ball.vx, ball.vy
                ball.x, ball.y = b_rect.center
                return

            # 신속공은 발사 후 경과 시간에 비례해 직접 피해가 커진다.
            elapsed = max(0.0, (pygame.time.get_ticks() - ball.created_at) / 1000.0)
            if ball.type == "SPEED":
                speed_level = self.upgrade_levels.get("SPEED", 0)
                attack_power = 1 + speed_level
                base_dmg = max(1, int(attack_power * elapsed))
            elif ball.type in ("NORMAL", "DUPLICATE", "BOUNCE"):
                base_dmg = 1 + (self.upgrade_levels.get(ball.type, 0) if ball.type in ("NORMAL", "DUPLICATE", "BOUNCE") else 0)
            elif ball.type == "ULTIMATE":
                ult_level = self.upgrade_levels.get("ULTIMATE", 0)
                base_dmg = (2 if block.type == "boss" else 1)
                dmg = (14 if block.type == "boss" else 7) + ult_level * 2
                block.dot_ult = 3 + ult_level
                block.dot_ult_dmg = dmg
                for _ in range(9):
                    self.particles.append(Particle(
                        b_rect.centerx + random.randint(-7, 7),
                        b_rect.centery + random.randint(-7, 7),
                        random.choice([(120, 90, 105), (190, 90, 125), (255, 185, 205)])
                    ))
            else:
                base_dmg = 1

            # 부식공은 맞은 벽에 5초간 부식 상태를 부여한다.
            if ball.type == "CORROSION":
                corrosion_level = self.upgrade_levels.get("CORROSION", 0)
                block.corrosion_until = pygame.time.get_ticks() + 5000 + corrosion_level * 1000

            # 처형공: 최대 체력의 5% 미만(강화 시 기준 증가)이면 즉시 파괴.
            if ball.type == "EXECUTION":
                execute_level = self.upgrade_levels.get("EXECUTION", 0)
                execute_threshold = 0.05 + execute_level * 0.01
                if block.hp < block.max_hp * execute_threshold:
                    ex, ey = b_rect.center
                    self.destroy_block(block)
                    for i in range(15):
                        angle = math.tau * i / 15
                        speed = 10
                        self.balls.append(Ball(ex, ey, math.cos(angle) * speed,
                                               math.sin(angle) * speed, "NORMAL"))
                    for _ in range(18):
                        self.particles.append(Particle(ex, ey, (255, 90, 110)))
                    if ball in self.balls:
                        self.balls.remove(ball)
                    return

            # 폭파공은 세 번째 벽 충돌에서 사라지며 주변 3x3 범위에 광역 피해.
            if ball.type == "EXPLOSIVE":
                ball.hit_count += 1
                if ball.hit_count >= 3:
                    self.explosions.append(ExplosionEffect(b_rect.centerx, b_rect.centery))
                    explosive_level = self.upgrade_levels.get("EXPLOSIVE", 0)
                    splash_damage = 5 * (1 + explosive_level)
                    for target in list(self.blocks):
                        if abs(target.col - block.col) <= 1 and abs(target.row - block.row) <= 1:
                            self.damage_block(target, splash_damage)
                    for _ in range(18):
                        angle = random.uniform(0, math.tau)
                        self.particles.append(Particle(
                            b_rect.centerx + math.cos(angle) * 12,
                            b_rect.centery + math.sin(angle) * 12,
                            random.choice([(255, 100, 35), (255, 190, 65), (255, 235, 160)])
                        ))
                    if ball in self.balls:
                        self.balls.remove(ball)
                    return

            self.damage_block(block, base_dmg)

            if ball.type == "DUPLICATE" and not ball.is_clone and not ball.has_split:
                # 원본은 사라지고 같은 속성의 복제공 2개가 서로 다른 각도로 갈라진다.
                ball.has_split = True
                angle = math.atan2(ball.vy, ball.vx)
                speed = max(6.0, math.hypot(ball.vx, ball.vy))
                for offset in (-0.42, 0.42):
                    child_angle = angle + offset
                    self.balls.append(Ball(ball.x, ball.y,
                                           math.cos(child_angle) * speed,
                                           math.sin(child_angle) * speed,
                                           "DUPLICATE", is_clone=True))
                if ball in self.balls:
                    self.balls.remove(ball)
                return

            if ball.type == "ICE":
                ice_level = self.upgrade_levels.get("ICE", 0)
                nearby = sorted(
                    [nb for nb in self.blocks if abs(nb.col - block.col) <= 1 and abs(nb.row - block.row) <= 1],
                    key=lambda nb: abs(nb.col - block.col) + abs(nb.row - block.row)
                )
                frozen_count = 0
                for target in nearby:
                    if target.freeze_immunity == 0 and not target.frozen:
                        target.frozen = True
                        target.freeze_immunity = 1
                        frozen_count += 1
                        target_rect = target.get_rect()
                        for _ in range(5):
                            self.particles.append(Particle(
                                target_rect.centerx + random.randint(-8, 8),
                                target_rect.centery + random.randint(-8, 8), (170, 240, 255)))
                        if frozen_count >= 1 + ice_level:
                            break
            elif ball.type == "FIRE":
                fire_level = self.upgrade_levels.get("FIRE", 0)
                block.dot_fire += 3 + fire_level
                block.dot_fire_dmg = max(block.dot_fire_dmg, 1 + fire_level)
            elif ball.type == "ELEC":
                elec_level = self.upgrade_levels.get("ELEC", 0)
                for target in self.blocks:
                    if abs(target.col - block.col) <= 1 and abs(target.row - block.row) <= 1:
                        target.dot_elec += 2 + elec_level * 2
            elif ball.type == "BOMB":
                self.explosions.append(ExplosionEffect(b_rect.centerx, b_rect.centery))
                for _ in range(12):
                    angle = random.uniform(0, math.tau)
                    self.particles.append(Particle(
                        b_rect.centerx + math.cos(angle) * 8,
                        b_rect.centery + math.sin(angle) * 8,
                        random.choice([(255, 100, 35), (255, 190, 65), (255, 235, 160)])))
                bomb_level = self.upgrade_levels.get("BOMB", 0)
                bomb_range = 1 + bomb_level // 2
                bomb_damage = 5 + bomb_level * 2
                for target in list(self.blocks):
                    if abs(target.col - block.col) <= bomb_range and abs(target.row - block.row) <= bomb_range:
                        self.damage_block(target, bomb_damage)
            elif ball.type in ["CROSS", "LINE", "DIR4"]:
                theme_particle_color = MAP_THEMES[self.equipped_theme]["particle"]
                self.lasers.append(LaserEffect(b_rect.centerx, b_rect.centery, ball.type, theme_particle_color))
                beam_level = self.upgrade_levels.get(ball.type, 0)
                beam_damage = 4 + beam_level * 2
                for target in list(self.blocks):
                    if ball.type in ["CROSS", "DIR4"] and target.col == block.col:
                        self.damage_block(target, beam_damage)
                    if ball.type in ["CROSS", "LINE", "DIR4"] and target.row == block.row:
                        self.damage_block(target, beam_damage)

            if block in self.blocks and block.hp <= 0:
                self.destroy_block(block)
            return

    def update(self):
        if self.state == "TOUCH_START":
            self.touch_alpha_timer += 0.05
            return

        if self.state == "TRANSITION":
            self.transition_alpha += 8
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                self.loading_progress = 0.0
                self.state = "LOADING"
            return

        if self.state == "LOADING":
            self.loading_progress += 0.025
            if self.loading_progress >= 1.0:
                self.loading_progress = 1.0
                self.state = "MAIN_MENU"
            return

        if self.state in ["MAIN_MENU", "STAGE_SELECT", "SHOP", "EVENT", "QUEST", "GACHA"]:
            return

        if self.state == "AWAKENING":
            elapsed = pygame.time.get_ticks() - self.awakening_started_at
            if elapsed >= self.awakening_duration:
                self.state = "AIMING"
                self.stage += 1
                self.spawn_new_row()
            return

        for p in list(self.particles):
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        for l in list(self.lasers):
            l.update()
            if l.life <= 0:
                self.lasers.remove(l)
        for explosion in list(self.explosions):
            explosion.update()
            if explosion.life <= 0:
                self.explosions.remove(explosion)

        if self.state == "FIRING":
            self.spawn_timer += 1
            for item in list(self.spawn_queue):
                b_type, delay = item
                if self.spawn_timer >= delay:
                    speed = 10
                    vx = math.cos(self.aim_angle) * speed
                    vy = math.sin(self.aim_angle) * speed
                    new_ball = Ball(self.launcher_x, self.launcher_y, vx, vy, b_type)
                    self.balls.append(new_ball)
                    self.spawn_queue.remove(item)

            sub_steps = 4
            for ball in list(self.balls):
                if ball not in self.balls:
                    continue
                if ball.type == "MOSQUITO" and ball.attached_block is not None:
                    now = pygame.time.get_ticks()
                    target = ball.attached_block
                    if target not in self.blocks:
                        ball.last_siphoned_block = target
                        ball.attached_block = None
                        ball.vx = ball.siphon_vx * 0.8
                        ball.vy = ball.siphon_vy * 0.8
                        continue
                    elapsed_attach = max(0.0, min(3.0, (now - ball.attach_started) / 1000.0))
                    target_rect = target.get_rect()
                    ball.x, ball.y = target_rect.center
                    mosquito_level = self.upgrade_levels.get("MOSQUITO", 0)
                    # 3초 동안 최대 체력의 30% + 강화 단계당 5%를 흡수한다.
                    base_siphon = 0.30 + mosquito_level * 0.05
                    if ball.type == "MALARIA":
                        base_siphon *= ball.malaria_power
                    total_siphon = max(1, int(target.max_hp * base_siphon))
                    desired_damage = int(total_siphon * (elapsed_attach / 3.0))
                    damage_delta = desired_damage - ball.siphon_damage_applied
                    if damage_delta > 0:
                        ball.siphon_damage_applied += damage_delta
                        self.damage_block(target, damage_delta)
                    # 흡혈할수록 커지고, 완료 후에는 원래 속도보다 20% 느려진다.
                    ball.radius = int(ball.siphon_start_radius + (6 + mosquito_level) * (elapsed_attach / 3.0))
                    if target not in self.blocks or elapsed_attach >= 3.0:
                        ball.last_siphoned_block = target
                        if ball.type == "MALARIA":
                            ball.malaria_hit_ids.add(id(target))
                            ball.malaria_power += 0.20
                            # 흡혈을 마칠 때마다 8% 확률로 알을 남긴다.
                            if random.random() < 0.08:
                                self.mosquito_eggs.append({"x": ball.x, "y": ball.y})
                                for _ in range(8):
                                    self.particles.append(Particle(ball.x, ball.y, (255, 180, 90)))
                            self.continue_malaria_chain(ball)
                        else:
                            ball.attached_block = None
                            ball.vx = ball.siphon_vx * 0.8
                            ball.vy = ball.siphon_vy * 0.8
                    continue

                if ball.type == "SPEED":
                    elapsed = max(0.0, (pygame.time.get_ticks() - ball.created_at) / 1000.0)
                    speed_level = self.upgrade_levels.get("SPEED", 0)
                    new_factor = 1.0 + elapsed * (0.5 + speed_level * 0.1)
                    ratio = new_factor / max(0.001, ball.speed_factor)
                    ball.vx *= ratio
                    ball.vy *= ratio
                    ball.speed_factor = new_factor

                for _ in range(sub_steps):
                    if ball not in self.balls:
                        break
                    ball.x += ball.vx / sub_steps
                    ball.y += ball.vy / sub_steps
                    self.record_laser_trail(ball)
                    self.handle_ball_collision(ball)

                if ball not in self.balls:
                    continue
                if ball.type == "BOUNCE" and ball.y + ball.radius >= FIELD_BOTTOM:
                    if ball.bounce_count < 1:
                        ball.y = FIELD_BOTTOM - ball.radius
                        ball.vy = -abs(ball.vy)
                        ball.bounce_count += 1
                    else:
                        self.balls.remove(ball)
                        self.record_laser_trail(ball, force=True)
                elif ball.y > FIELD_BOTTOM + 20:
                    self.record_laser_trail(ball, force=True)
                    self.balls.remove(ball)

            if len(self.balls) == 0 and len(self.spawn_queue) == 0:
                self.end_turn()

    def draw_theme_ambience(self, surface):
        """현재 테마에 맞는 절차적 배경 장식. 이미지/외부 라이브러리 불필요."""
        key = self.equipped_theme
        data = MAP_THEMES[key]
        accent = data["color"]
        tick = pygame.time.get_ticks() / 1000.0

        if key == "GRASS":
            # 잔잔한 풀잎과 햇빛 입자
            for i in range(18):
                x = (i * 37 + int(tick * 12)) % WIDTH
                y = FIELD_TOP + (i * 53) % max(1, FIELD_BOTTOM - FIELD_TOP)
                pygame.draw.circle(surface, (190, 220, 175), (x, y), 2)
        elif key == "NEON":
            # 사이버 격자와 움직이는 스캔 라인
            for x in range(0, WIDTH, 30):
                pygame.draw.line(surface, (22, 55, 75), (x, FIELD_TOP), (x, FIELD_BOTTOM), 1)
            for y in range(FIELD_TOP, FIELD_BOTTOM, 30):
                pygame.draw.line(surface, (22, 55, 75), (0, y), (WIDTH, y), 1)
            scan_y = FIELD_TOP + int((tick * 75) % (FIELD_BOTTOM - FIELD_TOP))
            pygame.draw.line(surface, (0, 120, 150), (0, scan_y), (WIDTH, scan_y), 2)
        elif key == "MAGIC":
            # 천천히 회전하는 마법진
            cx, cy = WIDTH // 2, (FIELD_TOP + FIELD_BOTTOM) // 2
            radius = 115
            pygame.draw.circle(surface, (75, 42, 105), (cx, cy), radius, 1)
            pygame.draw.circle(surface, (95, 55, 130), (cx, cy), radius - 18, 1)
            for i in range(6):
                a = tick * 0.35 + i * math.tau / 6
                ex = int(cx + math.cos(a) * radius)
                ey = int(cy + math.sin(a) * radius)
                pygame.draw.line(surface, (90, 55, 125), (cx, cy), (ex, ey), 1)
        elif key == "GOLD":
            # 사막의 모래 먼지
            for i in range(30):
                x = (i * 71 + int(tick * (10 + i % 5))) % WIDTH
                y = FIELD_TOP + (i * 47 + int(tick * 7)) % max(1, FIELD_BOTTOM - FIELD_TOP)
                pygame.draw.circle(surface, (125, 91, 42), (x, y), 1 + (i % 2))
        elif key == "SPACE":
            # 별빛과 성운 링
            for i in range(42):
                x = (i * 97 + 13) % WIDTH
                y = FIELD_TOP + (i * 61 + 7) % max(1, FIELD_BOTTOM - FIELD_TOP)
                pulse = 1 + int((math.sin(tick * 2 + i) + 1) * 1.2)
                pygame.draw.circle(surface, (125, 75, 150), (x, y), pulse)
            cx, cy = WIDTH // 2, (FIELD_TOP + FIELD_BOTTOM) // 2
            pygame.draw.circle(surface, (65, 35, 100), (cx, cy), 155, 1)
        elif key == "GLITCH":
            # 불규칙한 디지털 노이즈 라인
            for i in range(12):
                y = FIELD_TOP + (i * 49 + int(tick * 35)) % max(1, FIELD_BOTTOM - FIELD_TOP)
                x = (i * 43 + int(tick * 90)) % WIDTH
                pygame.draw.line(surface, (20, 90, 45), (x, y), (min(WIDTH, x + 25 + i * 2), y), 2)

    def draw_treasure_chest(self, surface, cx, cy, tier, unlocked):
        box_w, box_h = 44, 34
        rect = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
        
        if tier == 1:
            body_col = (150, 160, 175) if unlocked else (110, 120, 135)
            trim_col = (210, 220, 230)
        elif tier == 2:
            body_col = (80, 150, 235) if unlocked else (90, 110, 140)
            trim_col = (255, 215, 80)
        else:
            body_col = (235, 165, 45) if unlocked else (130, 110, 80)
            trim_col = (255, 245, 150)

        pygame.draw.rect(surface, body_col, rect, border_radius=6)
        pygame.draw.rect(surface, trim_col, rect, 2, border_radius=6)
        pygame.draw.line(surface, trim_col, (rect.left, rect.centery - 2), (rect.right, rect.centery - 2), 2)
        pygame.draw.rect(surface, trim_col, (cx - 5, rect.centery - 6, 10, 10), border_radius=2)

    def draw(self):
        current_bg_color = MAP_THEMES[self.equipped_theme]["bg"] if self.state not in ["TOUCH_START", "TRANSITION", "LOADING"] else (240, 244, 250)
        screen.fill(current_bg_color)
        if self.state not in ["TOUCH_START", "TRANSITION", "LOADING", "MAIN_MENU",
                              "STAGE_SELECT", "SHOP", "EVENT", "QUEST", "GACHA"]:
            self.draw_theme_ambience(screen)

        if self.state == "TOUCH_START":
            title_txt = FONT_TITLE.render("단단벽", True, (40, 90, 180))
            sub_txt = FONT_SMALL.render("DanDanBrick Academy", True, (100, 110, 130))
            screen.blit(title_txt, title_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
            screen.blit(sub_txt, sub_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

            alpha_val = int((math.sin(self.touch_alpha_timer * 4) + 1) / 2 * 155) + 100
            touch_surf = FONT_LARGE.render("터치하여 게임을 시작하세요", True, (60, 130, 230))
            touch_surf.set_alpha(alpha_val)
            screen.blit(touch_surf, touch_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))
            pygame.display.flip()
            return

        if self.state == "TRANSITION":
            title_txt = FONT_TITLE.render("단단벽", True, (40, 90, 180))
            screen.blit(title_txt, title_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
            
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((40, 90, 180, self.transition_alpha))
            screen.blit(s, (0, 0))
            pygame.display.flip()
            return

        if self.state == "LOADING":
            screen.fill((25, 35, 55))
            load_title = FONT_LARGE.render("LOADING...", True, (255, 255, 255))
            screen.blit(load_title, load_title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

            bar_w, bar_h = 300, 24
            bar_x, bar_y = WIDTH // 2 - bar_w // 2, HEIGHT // 2 + 10
            pygame.draw.rect(screen, (50, 65, 90), (bar_x, bar_y, bar_w, bar_h), border_radius=12)
            
            current_w = int(bar_w * min(1.0, self.loading_progress))
            if current_w > 0:
                pygame.draw.rect(screen, (60, 140, 240), (bar_x, bar_y, current_w, bar_h), border_radius=12)
            
            pct_txt = FONT_SMALL.render(f"{int(min(1.0, self.loading_progress) * 100)}%", True, (200, 220, 255))
            screen.blit(pct_txt, pct_txt.get_rect(center=(WIDTH // 2, bar_y + bar_h // 2)))
            pygame.display.flip()
            return

        # 메인 화면 및 메뉴들
        if self.state in ["MAIN_MENU", "STAGE_SELECT", "SHOP", "EVENT", "QUEST", "GACHA"]:
            # 상단바
            pygame.draw.rect(screen, (255, 255, 255), (0, 0, WIDTH, HEADER_HEIGHT))
            pygame.draw.line(screen, (210, 220, 235), (0, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT), 2)
            
            stam_txt = FONT_SMALL.render(f"🍙 행동력 {self.stamina}/{self.max_stamina}", True, (60, 130, 230))
            dia_txt = FONT_SMALL.render(f"💎 {self.diamonds} 다이아", True, (40, 90, 180))
            screen.blit(stam_txt, (15, 12))
            screen.blit(dia_txt, (165, 12))

            pygame.draw.rect(screen, (80, 140, 220), self.shop_btn, border_radius=6)
            pygame.draw.rect(screen, (100, 120, 200), self.event_btn, border_radius=6)
            pygame.draw.rect(screen, (220, 140, 50), self.quest_btn, border_radius=6)
            pygame.draw.rect(screen, (180, 80, 220), self.gacha_btn, border_radius=6)

            screen.blit(FONT_SMALL.render("🛒 상점", True, (255, 255, 255)), self.shop_btn.inflate(-16, -10))
            screen.blit(FONT_SMALL.render("🎁 이벤트", True, (255, 255, 255)), self.event_btn.inflate(-14, -10))
            screen.blit(FONT_SMALL.render("📜 퀘스트", True, (255, 255, 255)), self.quest_btn.inflate(-14, -10))
            screen.blit(FONT_SMALL.render("✨ 맵뽑기", True, (255, 255, 255)), self.gacha_btn.inflate(-10, -10))

            # 콘텐츠 영역 프레임
            content_rect = pygame.Rect(20, HEADER_HEIGHT + 15, WIDTH - 40, HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT - 30)
            pygame.draw.rect(screen, (255, 255, 255), content_rect, border_radius=12)
            pygame.draw.rect(screen, (210, 220, 235), content_rect, 2, border_radius=12)

            if self.main_tab == "LOBBY":
                lobby_t = FONT_LARGE.render("단단벽 로비", True, (40, 90, 180))
                lobby_sub = FONT_SMALL.render(f"현재 장착 테마: {MAP_THEMES[self.equipped_theme]['name']}", True, (100, 110, 130))
                screen.blit(lobby_t, (content_rect.x + 25, content_rect.y + 25))
                screen.blit(lobby_sub, (content_rect.x + 25, content_rect.y + 55))

                summary_txt = FONT_SMALL.render(f"전체 진행도: 총 5개 관문 (최대 100 STAGE)", True, (80, 110, 160))
                screen.blit(summary_txt, (content_rect.x + 25, content_rect.y + 85))

                pygame.draw.rect(screen, (60, 130, 230), self.stage_start_btn, border_radius=10)
                start_txt = FONT_LARGE.render("벽돌부수기 시작", True, (255, 255, 255))
                screen.blit(start_txt, start_txt.get_rect(center=self.stage_start_btn.center))

            elif self.main_tab == "INVENTORY":
                inv_t = FONT_LARGE.render("인벤토리 & 테마 장착", True, (40, 90, 180))
                inv_sub = FONT_SMALL.render("원하는 테마를 클릭하여 장착하세요!", True, (100, 110, 130))
                screen.blit(inv_t, (content_rect.x + 25, content_rect.y + 20))
                screen.blit(inv_sub, (content_rect.x + 25, content_rect.y + 45))
                
                y_offset = content_rect.y + 75
                for t_key, t_val in MAP_THEMES.items():
                    owned = t_key in self.owned_themes
                    equipped = self.equipped_theme == t_key
                    status = "[장착중]" if equipped else ("[보유 - 클릭시 장착]" if owned else "[미보유 (뽑기 필요)]")
                    col = (60, 180, 100) if equipped else ((40, 90, 180) if owned else (150, 150, 150))
                    
                    txt = FONT_SMALL.render(f"• {t_val['name']} ({t_val['grade']}) {status}", True, col)
                    screen.blit(txt, (content_rect.x + 25, y_offset))
                    y_offset += 32

            elif self.main_tab == "UPGRADE":
                up_t = FONT_LARGE.render("구체 강화 연구소", True, (40, 90, 180))
                screen.blit(up_t, (content_rect.x + 20, content_rect.y + 15))
                screen.blit(FONT_SMALL.render(f"보유 다이아: 💎 {self.diamonds:,}개", True, (40, 90, 180)),
                            (content_rect.x + 20, content_rect.y + 48))
                screen.blit(FONT_TINY.render("다이아로 강화 가능 · 영구 적용 · 각 구체 최대 Lv.5", True, (100, 110, 130)),
                            (content_rect.x + 20, content_rect.y + 72))

                self.upgrade_btns = []
                row_y = content_rect.y + 96
                for idx, (skill_id, skill_name, description) in enumerate(UPGRADE_INFO):
                    row = pygame.Rect(content_rect.x + 12, row_y + idx * 28, content_rect.width - 24, 26)
                    pygame.draw.rect(screen, (244, 248, 255), row, border_radius=8)
                    pygame.draw.rect(screen, (205, 218, 238), row, 1, border_radius=8)

                    level = self.upgrade_levels.get(skill_id, 0)
                    title = FONT_TINY.render(f"{skill_name}  Lv.{level}/5", True, (45, 75, 125))
                    desc = FONT_TINY.render(description, True, (100, 110, 130))
                    screen.blit(title, (row.x + 8, row.y + 1))
                    screen.blit(desc, (row.x + 8, row.y + 14))

                    btn = pygame.Rect(row.right - 82, row.y + 2, 74, 22)
                    if level >= 5:
                        btn_color, btn_text = (145, 155, 170), "MAX"
                    else:
                        cost = self.upgrade_cost(skill_id)
                        btn_color = (75, 145, 220) if self.diamonds >= cost else (170, 175, 185)
                        btn_text = f"강화 {cost:,}"
                    pygame.draw.rect(screen, btn_color, btn, border_radius=7)
                    btn_label = FONT_TINY.render(btn_text, True, (255, 255, 255))
                    screen.blit(btn_label, btn_label.get_rect(center=btn.center))
                    self.upgrade_btns.append((btn, skill_id))

                if self.upgrade_msg:
                    msg = FONT_TINY.render(self.upgrade_msg, True, (190, 75, 75))
                    screen.blit(msg, (content_rect.x + 18, content_rect.bottom - 15))

            # 하단 탭 네비게이션
            pygame.draw.rect(screen, (255, 255, 255), (0, HEIGHT - FOOTER_HEIGHT, WIDTH, FOOTER_HEIGHT))
            pygame.draw.line(screen, (210, 220, 235), (0, HEIGHT - FOOTER_HEIGHT), (WIDTH, HEIGHT - FOOTER_HEIGHT), 2)

            pygame.draw.rect(screen, (60, 130, 230) if self.main_tab == "INVENTORY" else (220, 225, 235), self.tab_inven_btn, border_radius=8)
            pygame.draw.rect(screen, (60, 130, 230) if self.main_tab == "LOBBY" else (220, 225, 235), self.tab_lobby_btn, border_radius=8)
            pygame.draw.rect(screen, (60, 130, 230) if self.main_tab == "UPGRADE" else (220, 225, 235), self.tab_upgrade_btn, border_radius=8)

            screen.blit(FONT_SMALL.render("인벤토리", True, (255, 255, 255) if self.main_tab == "INVENTORY" else (100, 110, 130)), self.tab_inven_btn.inflate(-20, -10))
            screen.blit(FONT_SMALL.render("로비", True, (255, 255, 255) if self.main_tab == "LOBBY" else (100, 110, 130)), self.tab_lobby_btn.inflate(-20, -10))
            screen.blit(FONT_SMALL.render("강화", True, (255, 255, 255) if self.main_tab == "UPGRADE" else (100, 110, 130)), self.tab_upgrade_btn.inflate(-20, -10))

            # ==========================================
            # 독립된 팝업 창들 (상점, 이벤트, 뽑기, 스테이지 선택)
            # ==========================================
            
            # 1. 상점 팝업 창
            if self.state == "SHOP":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((15, 22, 38, 180))
                screen.blit(overlay, (0, 0))

                shop_box = pygame.Rect(55, HEIGHT // 2 - 190, WIDTH - 110, 380)
                pygame.draw.rect(screen, (255, 255, 255), shop_box, border_radius=14)
                pygame.draw.rect(screen, (40, 90, 180), shop_box, 3, border_radius=14)

                screen.blit(FONT_LARGE.render("🛒 캐시 및 아이템 상점", True, (40, 90, 180)), (shop_box.x + 20, shop_box.y + 20))
                
                # 닫기 버튼
                pygame.draw.rect(screen, (220, 75, 75), self.popup_close_btn, border_radius=8)
                screen.blit(FONT_SMALL.render("닫기", True, (255, 255, 255)), self.popup_close_btn.inflate(-10, -8))

                # 초보자 패키지
                pygame.draw.rect(screen, (255, 240, 210), self.buy_pack_btn, border_radius=10)
                pygame.draw.rect(screen, (240, 180, 60), self.buy_pack_btn, 2, border_radius=10)
                p_title = "초보자 지원 패키지 (구매완료)" if self.beginner_pack_purchased else "🎁 초보자 지원 패키지 (💎 500)"
                screen.blit(FONT_MED.render(p_title, True, (180, 100, 20)), (self.buy_pack_btn.x + 15, self.buy_pack_btn.y + 14))

                # 행동력 충전
                pygame.draw.rect(screen, (235, 245, 255), self.buy_stamina_btn, border_radius=8)
                pygame.draw.rect(screen, (100, 160, 230), self.buy_stamina_btn, 1, border_radius=8)
                screen.blit(FONT_SMALL.render("🍙 행동력 +30 충전 (💎 300)", True, (40, 90, 180)), (self.buy_stamina_btn.x + 15, self.buy_stamina_btn.y + 13))

                if self.shop_msg:
                    screen.blit(FONT_SMALL.render(self.shop_msg, True, (220, 60, 60)), (shop_box.x + 20, shop_box.y + 325))

                # 상품을 클릭했을 때만 수량 선택창을 열고, 휠 입력은 구매에 사용하지 않음
                if self.shop_selected_item:
                    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    shade.fill((10, 18, 32, 175))
                    screen.blit(shade, (0, 0))
                    selector = pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 - 115, 340, 230)
                    pygame.draw.rect(screen, (250, 252, 255), selector, border_radius=14)
                    pygame.draw.rect(screen, (55, 115, 205), selector, 3, border_radius=14)

                    item_info = {
                        "PACK": ("초보자 지원 패키지", 500),
                        "STAMINA": ("행동력 +30 충전", 300),
                    }
                    item_name, unit_price = item_info[self.shop_selected_item]
                    total_price = unit_price * self.shop_quantity
                    screen.blit(FONT_MED.render(item_name, True, (40, 85, 155)),
                                (selector.x + 20, selector.y + 18))

                    qty_text = "수량: 1개 (패키지는 수량 변경 불가)" if self.shop_selected_item == "PACK" else f"구매 수량: {self.shop_quantity}개"
                    screen.blit(FONT_SMALL.render(qty_text, True, (55, 65, 85)),
                                (selector.x + 20, selector.y + 58))

                    cost_text = FONT_MED.render(f"총 가격: 💎 {total_price:,}", True, (180, 105, 25))
                    screen.blit(cost_text, cost_text.get_rect(center=(selector.centerx, selector.y + 91)))

                    if self.shop_selected_item != "PACK":
                        track = self.shop_slider_rect
                        pygame.draw.rect(screen, (215, 225, 240), track, border_radius=7)
                        fill_w = int((track.width - 12) * (self.shop_quantity - 1) / 9)
                        if fill_w > 0:
                            pygame.draw.rect(screen, (65, 145, 235),
                                             (track.x + 6, track.y + 3, fill_w, track.height - 6),
                                             border_radius=5)
                        knob_x = track.x + 6 + fill_w
                        pygame.draw.circle(screen, (40, 105, 205), (knob_x, track.centery), 10)
                        screen.blit(FONT_TINY.render("1개", True, (90, 100, 120)),
                                    (track.left, track.bottom + 5))
                        screen.blit(FONT_TINY.render("10개", True, (90, 100, 120)),
                                    (track.right - 25, track.bottom + 5))

                    pygame.draw.rect(screen, (55, 165, 105), self.shop_confirm_btn, border_radius=8)
                    screen.blit(FONT_SMALL.render("구매하기", True, (255, 255, 255)),
                                self.shop_confirm_btn.inflate(-12, -10))
                    pygame.draw.rect(screen, (145, 155, 170), self.shop_cancel_btn, border_radius=8)
                    screen.blit(FONT_SMALL.render("취소", True, (255, 255, 255)),
                                self.shop_cancel_btn.inflate(-12, -10))

            # 2. 이벤트 팝업 창
            elif self.state == "EVENT":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((15, 22, 38, 180))
                screen.blit(overlay, (0, 0))

                ev_box = pygame.Rect(55, HEIGHT // 2 - 160, WIDTH - 110, 320)
                pygame.draw.rect(screen, (255, 255, 255), ev_box, border_radius=14)
                pygame.draw.rect(screen, (100, 120, 200), ev_box, 3, border_radius=14)

                screen.blit(FONT_LARGE.render("🎁 오픈 기념 이벤트", True, (40, 90, 180)), (ev_box.x + 20, ev_box.y + 20))
                
                # 닫기 버튼
                pygame.draw.rect(screen, (220, 75, 75), self.popup_close_btn, border_radius=8)
                screen.blit(FONT_SMALL.render("닫기", True, (255, 255, 255)), self.popup_close_btn.inflate(-10, -8))

                screen.blit(FONT_SMALL.render("단단벽 정식 오픈 기념 특별 대축제!", True, (100, 110, 130)), (ev_box.x + 20, ev_box.y + 75))
                screen.blit(FONT_SMALL.render("• 보상: 다이아 10,000개 + 행동력 100", True, (60, 130, 230)), (ev_box.x + 20, ev_box.y + 110))
                screen.blit(FONT_SMALL.render("• 이벤트 수령 시 최대 행동력도 150으로 확장!", True, (60, 150, 110)), (ev_box.x + 20, ev_box.y + 140))

                pygame.draw.rect(screen, (60, 180, 100) if not self.event_claimed else (150, 150, 150), self.claim_event_btn, border_radius=10)
                ev_str = "오픈 보상 수령완료" if self.event_claimed else "🎁 오픈 기념 보상 받기"
                screen.blit(FONT_LARGE.render(ev_str, True, (255, 255, 255)), self.claim_event_btn.inflate(-20, -10))

                if self.event_msg:
                    screen.blit(FONT_SMALL.render(self.event_msg, True, (220, 60, 60)), (ev_box.x + 20, ev_box.y + 265))

            # 3. 뽑기 팝업 창
            elif self.state == "GACHA":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((15, 22, 38, 180))
                screen.blit(overlay, (0, 0))

                gacha_box = pygame.Rect(55, HEIGHT // 2 - 180, WIDTH - 110, 360)
                pygame.draw.rect(screen, (255, 255, 255), gacha_box, border_radius=14)
                pygame.draw.rect(screen, (180, 80, 220), gacha_box, 3, border_radius=14)

                screen.blit(FONT_LARGE.render("✨ 맵 테마 뽑기", True, (180, 60, 200)), (gacha_box.x + 20, gacha_box.y + 20))
                
                # 닫기 버튼
                pygame.draw.rect(screen, (220, 75, 75), self.popup_close_btn, border_radius=8)
                screen.blit(FONT_SMALL.render("닫기", True, (255, 255, 255)), self.popup_close_btn.inflate(-10, -8))

                cost_str = "첫 10회 뽑기 무료!" if self.free_gacha_available else "10회 뽑기 (2000 다이아)"
                screen.blit(FONT_MED.render(cost_str, True, (100, 110, 130)), (gacha_box.x + 20, gacha_box.y + 75))
                screen.blit(FONT_TINY.render("등급 확률: 일반 42% / 희귀 27% / 영웅 16% / 전설 9% / 신화 4% / 초월 2%",
                                             True, (130, 130, 150)), (gacha_box.x + 15, gacha_box.y + 105))

                res_t = FONT_MED.render(self.gacha_result_msg, True, (220, 50, 120))
                screen.blit(res_t, (gacha_box.x + 20, gacha_box.y + 130))

                pygame.draw.rect(screen, (180, 80, 220), self.gacha_action_btn, border_radius=10)
                btn_lbl = FONT_LARGE.render("10연차 뽑기 실행", True, (255, 255, 255))
                screen.blit(btn_lbl, btn_lbl.get_rect(center=self.gacha_action_btn.center))

            # 4. 스테이지 선택 팝업 창
            elif self.state == "STAGE_SELECT":
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((15, 22, 38, 195))
                screen.blit(overlay, (0, 0))

                chap = CHAPTERS[self.selected_chapter_idx]
                is_cleared = chap["id"] in self.cleared_chapters

                card_rect = pygame.Rect(65, 155, WIDTH - 130, 325)
                pygame.draw.rect(screen, (28, 38, 65), card_rect, border_radius=14)
                pygame.draw.rect(screen, (225, 185, 85), card_rect, 3, border_radius=14)

                banner_rect = pygame.Rect(WIDTH // 2 - 145, 132, 290, 44)
                pygame.draw.rect(screen, (42, 34, 32), banner_rect, border_radius=10)
                pygame.draw.rect(screen, (235, 195, 95), banner_rect, 2, border_radius=10)
                title_s = FONT_MED.render(chap["name"], True, (255, 235, 160))
                screen.blit(title_s, title_s.get_rect(center=banner_rect.center))

                pygame.draw.rect(screen, (220, 75, 75), self.chap_close_btn, border_radius=8)
                screen.blit(FONT_SMALL.render("닫기", True, (255, 255, 255)), self.chap_close_btn.inflate(-10, -8))

                stage_badge = pygame.Rect(card_rect.centerx - 135, card_rect.top + 35, 270, 32)
                pygame.draw.rect(screen, (42, 56, 92), stage_badge, border_radius=8)
                range_txt = FONT_SMALL.render(f"STAGE {chap['start_stage']} ~ {chap['max_stage']}  (총 {chap['max_stage']}스테이지)", True, (130, 215, 255))
                screen.blit(range_txt, range_txt.get_rect(center=stage_badge.center))

                desc_txt = FONT_TINY.render(chap["desc"], True, (200, 210, 230))
                screen.blit(desc_txt, desc_txt.get_rect(center=(card_rect.centerx, card_rect.top + 85)))

                rew_header = FONT_SMALL.render("— 단계별 클리어 보상 —", True, (245, 205, 100))
                screen.blit(rew_header, rew_header.get_rect(center=(card_rect.centerx, card_rect.top + 118)))

                bar_y = card_rect.top + 205
                bar_x1, bar_x2 = card_rect.left + 65, card_rect.right - 65
                pygame.draw.line(screen, (65, 80, 115), (bar_x1, bar_y), (bar_x2, bar_y), 6)
                if is_cleared:
                    pygame.draw.line(screen, (245, 195, 70), (bar_x1, bar_y), (bar_x2, bar_y), 6)

                box_positions = [bar_x1, card_rect.centerx, bar_x2]
                for idx, bx in enumerate(box_positions):
                    cond_label, reward_val = chap["rewards"][idx]
                    self.draw_treasure_chest(screen, bx, bar_y - 34, idx + 1, is_cleared)
                    node_col = (245, 195, 70) if is_cleared else (90, 105, 140)
                    pygame.draw.circle(screen, node_col, (bx, bar_y), 7)
                    pygame.draw.circle(screen, (255, 255, 255), (bx, bar_y), 7, 1)

                    c_txt = FONT_TINY.render(cond_label, True, (220, 230, 245))
                    r_txt = FONT_SMALL.render(reward_val, True, (255, 220, 100))
                    screen.blit(c_txt, c_txt.get_rect(center=(bx, bar_y + 22)))
                    screen.blit(r_txt, r_txt.get_rect(center=(bx, bar_y + 42)))

                pygame.draw.rect(screen, (45, 60, 95), self.chap_prev_btn, border_radius=8)
                screen.blit(FONT_LARGE.render("<", True, (255, 255, 255)), self.chap_prev_btn.inflate(-18, -32))

                pygame.draw.rect(screen, (45, 60, 95), self.chap_next_btn, border_radius=8)
                screen.blit(FONT_LARGE.render(">", True, (255, 255, 255)), self.chap_next_btn.inflate(-18, -32))

                if self.chapter_status_msg:
                    msg_s = FONT_SMALL.render(self.chapter_status_msg, True, (255, 130, 130))
                    screen.blit(msg_s, msg_s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 115)))

                sweep_col = (120, 145, 185) if is_cleared else (75, 85, 105)
                pygame.draw.rect(screen, sweep_col, self.sweep_btn, border_radius=10)
                screen.blit(FONT_MED.render("빠른 소탕", True, (255, 255, 255)), (self.sweep_btn.centerx - 35, self.sweep_btn.centery - 18))
                screen.blit(FONT_TINY.render("🍙 x5 (클리어시)", True, (230, 240, 255)), (self.sweep_btn.centerx - 45, self.sweep_btn.centery + 4))

                pygame.draw.rect(screen, (235, 175, 55), self.enter_stage_btn, border_radius=10)
                screen.blit(FONT_MED.render("관문으로 진입", True, (45, 30, 10)), (self.enter_stage_btn.centerx - 48, self.enter_stage_btn.centery - 18))
                screen.blit(FONT_SMALL.render("🍙 x5", True, (65, 45, 15)), (self.enter_stage_btn.centerx - 18, self.enter_stage_btn.centery + 4))

            pygame.display.flip()
            return

        # 인게임 플레이 화면
        pygame.draw.rect(screen, (255, 255, 255), (0, 0, WIDTH, HEADER_HEIGHT))
        pygame.draw.line(screen, (210, 220, 235), (0, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT), 2)
        
        lvl_txt = FONT_MED.render(f"LV. {self.level}", True, (50, 110, 220))
        screen.blit(lvl_txt, (15, 10))
        
        exp_ratio = min(1.0, self.exp / self.max_exp)
        pygame.draw.rect(screen, (220, 225, 235), (95, 12, 180, 16), border_radius=8)
        pygame.draw.rect(screen, (60, 180, 100), (95, 12, int(180 * exp_ratio), 16), border_radius=8)
        
        stage_txt = FONT_MED.render(f"STAGE {self.stage} / {self.target_max_stage}", True, (40, 50, 70))
        screen.blit(stage_txt, (15, 42))
        dia_hud = FONT_SMALL.render(f"💎 {self.diamonds:,}", True, (40, 90, 180))
        screen.blit(dia_hud, (300, 14))

        pygame.draw.rect(screen, (230, 80, 80), self.surrender_btn, border_radius=6)
        screen.blit(FONT_SMALL.render("🏳️ 포기하기", True, (255, 255, 255)), (WIDTH - 98, 51))

        pygame.draw.line(screen, (230, 70, 70), (0, DANGER_Y), (WIDTH, DANGER_Y), 2)
        screen.blit(FONT_SMALL.render("⚠️ 최후의 방어선", True, (230, 70, 70)), (WIDTH - 110, DANGER_Y - 18))

        for b in self.blocks:
            b.draw(screen)

        # 레이저공이 남긴 자취는 공이 회수되어도 다음 턴의 벽 이동 전까지 표시된다.
        if self.laser_trails:
            trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for x1, y1, x2, y2 in self.laser_trails:
                pygame.draw.line(trail_surface, (40, 220, 255, 105), (int(x1), int(y1)), (int(x2), int(y2)), 7)
                pygame.draw.line(trail_surface, (235, 255, 255, 220), (int(x1), int(y1)), (int(x2), int(y2)), 2)
            screen.blit(trail_surface, (0, 0))

        # 말라리아 모기공이 낳은 알은 다음 턴 부화 전까지 바닥에 남는다.
        for egg in self.mosquito_eggs:
            ex, ey = int(egg["x"]), int(egg["y"])
            pygame.draw.ellipse(screen, (95, 35, 55), (ex - 7, ey - 5, 14, 10))
            pygame.draw.ellipse(screen, (255, 170, 100), (ex - 5, ey - 4, 10, 7), 2)
            pygame.draw.circle(screen, (255, 225, 160), (ex, ey - 1), 2)

        for ball in self.balls:
            ball.draw(screen)

        for p in self.particles:
            p.draw(screen)
        for l in self.lasers:
            l.draw(screen)
        for explosion in self.explosions:
            explosion.draw(screen)

        if self.state == "AIMING":
            pred_x, pred_y = float(self.launcher_x), float(self.launcher_y)
            speed = 10
            pred_vx = math.cos(self.aim_angle) * speed
            pred_vy = math.sin(self.aim_angle) * speed
            
            max_dist, current_dist, step = 1500, 0, 10
            dots, bounce_count = [], 0
            
            while current_dist < max_dist:
                pred_x += pred_vx * (step / speed)
                pred_y += pred_vy * (step / speed)
                current_dist += step
                
                if pred_x <= 0 or pred_x >= WIDTH:
                    pred_vx *= -1
                    bounce_count += 1
                elif pred_y <= FIELD_TOP:
                    pred_vy *= -1
                    bounce_count += 1
                
                dots.append((int(pred_x), int(pred_y)))
                if bounce_count >= 2 or pred_y >= FIELD_BOTTOM:
                    break
            
            for i, pt in enumerate(dots):
                if i % 2 == 0:
                    pygame.draw.circle(screen, MAP_THEMES[self.equipped_theme]["particle"], pt, 3)

        pygame.draw.circle(screen, (60, 130, 230), (self.launcher_x, self.launcher_y), 12)

        pygame.draw.rect(screen, (255, 255, 255), (0, FIELD_BOTTOM, WIDTH, FOOTER_HEIGHT))
        pygame.draw.line(screen, (210, 220, 235), (0, FIELD_BOTTOM), (WIDTH, FIELD_BOTTOM), 2)
        
        btn_color = (60, 130, 230) if self.state == "FIRING" else (220, 225, 235)
        text_color = (255, 255, 255) if self.state == "FIRING" else (100, 110, 130)
        
        pygame.draw.rect(screen, btn_color, self.skip_btn, border_radius=8)
        screen.blit(FONT_MED.render("[Space] 공 회수 / 턴 스킵", True, text_color), self.skip_btn.inflate(-20, -10))

        if self.state == "SURRENDER_POPUP":
            self.draw_popup("전략적 후퇴", "포기하시겠습니까?\n메인 로비로 돌아갑니다.", ["후퇴하기", "취소"])
        elif self.state == "LEVELUP":
            self.draw_levelup_popup()
        elif self.state == "GAME_OVER":
            self.draw_popup("전투 패배", "방어선이 무너졌습니다...", ["메인으로"])
        elif self.state == "VICTORY":
            self.draw_popup("관문 클리어!", f"목표 스테이지를 정복했습니다!\n클리어 보상 💎{self.victory_reward:,} 지급!", ["메인으로"])
        elif self.state == "AWAKENING":
            self.draw_malaria_awakening()

        pygame.display.flip()

    def draw_malaria_awakening(self):
        """말라리아 모기공 획득 시 재생되는 짧은 각성 연출."""
        elapsed = pygame.time.get_ticks() - self.awakening_started_at
        progress = min(1.0, elapsed / max(1, self.awakening_duration))
        pulse = (math.sin(elapsed / 90.0) + 1.0) / 2.0

        # 전장을 어둡게 덮고 붉은 기운을 강조한다.
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((28, 5, 20, 185))
        screen.blit(shade, (0, 0))

        cx, cy = WIDTH // 2, HEIGHT // 2 - 12
        base_radius = 42 + int(progress * 48)
        for i in range(4):
            radius = base_radius + i * 23 + int(pulse * 9)
            alpha = max(35, 190 - i * 38)
            ring = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 65, 105, alpha), (cx, cy), radius, 3)
            screen.blit(ring, (0, 0))

        # 중앙의 모기공을 상징하는 붉은 구체와 날개 효과.
        orb_radius = 20 + int(pulse * 5)
        pygame.draw.circle(screen, (105, 20, 48), (cx, cy), orb_radius + 7)
        pygame.draw.circle(screen, (235, 55, 95), (cx, cy), orb_radius)
        pygame.draw.circle(screen, (255, 190, 150), (cx - 6, cy - 7), 6)
        pygame.draw.ellipse(screen, (255, 125, 155), (cx - 38, cy - 11, 23, 12))
        pygame.draw.ellipse(screen, (255, 125, 155), (cx + 15, cy - 11, 23, 12))

        title = FONT_TITLE.render("말라리아 모기공 각성!", True, (255, 105, 135))
        screen.blit(title, title.get_rect(center=(cx, cy + 92)))
        subtitle = FONT_MED.render("60% 확률 각성 성공 · 새로운 모기공을 획득했습니다", True, (255, 225, 230))
        screen.blit(subtitle, subtitle.get_rect(center=(cx, cy + 132)))

        # 아래쪽 진행 표시로 연출이 끝나는 시점을 알려준다.
        bar_rect = pygame.Rect(WIDTH // 2 - 105, cy + 165, 210, 7)
        pygame.draw.rect(screen, (90, 35, 55), bar_rect, border_radius=4)
        fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * progress), bar_rect.height)
        pygame.draw.rect(screen, (255, 85, 125), fill_rect, border_radius=4)

    def draw_popup(self, title, msg, buttons):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((20, 30, 50, 120))
        screen.blit(s, (0, 0))

        rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 110, 300, 220)
        pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=12)
        pygame.draw.rect(screen, (200, 210, 225), rect, 2, border_radius=12)

        t_s = FONT_LARGE.render(title, True, (40, 90, 180))
        screen.blit(t_s, t_s.get_rect(center=(rect.centerx, rect.top + 32)))

        lines = msg.split('\n')
        for i, line in enumerate(lines):
            m_s = FONT_SMALL.render(line, True, (40, 50, 70))
            screen.blit(m_s, m_s.get_rect(center=(rect.centerx, rect.top + 78 + i * 22)))

        self.popup_btns = []
        btn_w = 100
        start_x = WIDTH//2 - (len(buttons) * (btn_w + 10)) // 2 + 5
        for i, b_name in enumerate(buttons):
            b_rect = pygame.Rect(start_x + i * (btn_w + 10), rect.bottom - 45, btn_w, 32)
            pygame.draw.rect(screen, (60, 130, 230), b_rect, border_radius=6)
            b_s = FONT_SMALL.render(b_name, True, (255, 255, 255))
            screen.blit(b_s, b_s.get_rect(center=b_rect.center))
            self.popup_btns.append((b_rect, b_name))

    def draw_levelup_popup(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((20, 30, 50, 120))
        screen.blit(s, (0, 0))

        box = pygame.Rect(WIDTH//2 - 170, HEIGHT//2 - 180, 340, 360)
        pygame.draw.rect(screen, (255, 255, 255), box, border_radius=12)
        pygame.draw.rect(screen, (60, 130, 230), box, 2, border_radius=12)

        screen.blit(FONT_LARGE.render("LEVEL UP!", True, (40, 90, 180)), (box.centerx - 65, box.top + 15))

        self.skill_btns = []
        for i, sk in enumerate(self.skill_choices):
            card = pygame.Rect(box.left + 15, box.top + 60 + i * 95, 310, 80)
            pygame.draw.rect(screen, (245, 248, 252), card, border_radius=8)
            pygame.draw.rect(screen, (200, 210, 225), card, 1, border_radius=8)

            screen.blit(FONT_MED.render(sk["name"], True, (40, 90, 180)), (card.left + 10, card.top + 10))
            screen.blit(FONT_SMALL.render(sk["desc"], True, (40, 50, 70)), (card.left + 10, card.top + 38))
            if sk["id"] == "MOSQUITO":
                chance_txt = FONT_SMALL.render("60% 확률로 말라리아 모기공 각성!", True, (205, 55, 85))
                screen.blit(chance_txt, (card.left + 10, card.top + 57))
            self.skill_btns.append((card, sk))

def main():
    game = Game()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game.state == "FIRING":
                        game.recall_balls()

            if event.type == pygame.MOUSEWHEEL:
                # 상점에서 마우스 휠로 상품이 구매되거나 수량이 바뀌지 않도록 무시
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                # 구형 Pygame의 휠 입력(button 4/5)도 클릭 처리하지 않는다.
                if getattr(event, "button", 0) in (4, 5):
                    continue
                mx, my = event.pos

                if game.state == "TOUCH_START":
                    game.state = "TRANSITION"
                    continue

                # 공통 팝업 창들의 닫기(X) 버튼 처리
                if game.state in ["SHOP", "EVENT", "GACHA", "STAGE_SELECT"]:
                    if game.popup_close_btn.collidepoint(mx, my) or (game.state == "STAGE_SELECT" and game.chap_close_btn.collidepoint(mx, my)):
                        game.state = "MAIN_MENU"
                        game.shop_msg = ""
                        game.shop_selected_item = None
                        game.shop_slider_dragging = False
                        game.event_msg = ""
                        game.chapter_status_msg = ""
                        continue

                # 상점 팝업 내부 인터랙션
                if game.state == "SHOP":
                    if game.shop_selected_item:
                        # 상품 선택창이 열린 동안에는 배경 상품 클릭을 차단
                        if game.shop_slider_rect.collidepoint(mx, my) and game.shop_selected_item != "PACK":
                            game.shop_slider_dragging = True
                            ratio = max(0.0, min(1.0, (mx - game.shop_slider_rect.x) / game.shop_slider_rect.width))
                            game.shop_quantity = max(1, min(10, 1 + round(ratio * 9)))
                        elif game.shop_confirm_btn.collidepoint(mx, my):
                            item = game.shop_selected_item
                            qty = 1 if item == "PACK" else game.shop_quantity
                            price = {"PACK": 500, "STAMINA": 300}[item] * qty

                            if item == "PACK" and game.beginner_pack_purchased:
                                game.shop_msg = "이미 구매한 패키지입니다."
                            elif game.diamonds < price:
                                game.shop_msg = f"다이아가 부족합니다! 필요 💎 {price:,}"
                            else:
                                game.diamonds -= price
                                if item == "PACK":
                                    game.beginner_pack_purchased = True
                                    game.stamina = min(game.max_stamina, game.stamina + 50)
                                    game.shop_msg = "초보자 패키지 구매 성공! 행동력 +50 획득!"
                                elif item == "STAMINA":
                                    gained = min(game.max_stamina - game.stamina, 30 * qty)
                                    game.stamina += gained
                                    game.shop_msg = f"행동력 충전 완료! +{gained} (💎 {price:,} 사용)"
                            game.shop_selected_item = None
                            game.shop_slider_dragging = False
                        elif game.shop_cancel_btn.collidepoint(mx, my):
                            game.shop_selected_item = None
                            game.shop_slider_dragging = False
                        continue

                    if game.buy_pack_btn.collidepoint(mx, my):
                        game.shop_selected_item = "PACK"
                        game.shop_quantity = 1
                        game.shop_msg = ""
                        continue
                    if game.buy_stamina_btn.collidepoint(mx, my):
                        game.shop_selected_item = "STAMINA"
                        game.shop_quantity = 1
                        game.shop_msg = ""
                        continue

                # 이벤트 팝업 내부 인터랙션
                if game.state == "EVENT":
                    if game.claim_event_btn.collidepoint(mx, my):
                        if game.event_claimed:
                            game.event_msg = "이미 보상을 수령했습니다."
                        else:
                            game.event_claimed = True
                            game.diamonds += 10000
                            game.max_stamina = max(game.max_stamina, 150)
                            game.stamina = min(game.max_stamina, game.stamina + 100)
                            game.event_msg = "보상 수령 완료! (💎 10,000 / 행동력 +100)"
                        continue

                # 뽑기 팝업 내부 인터랙션
                if game.state == "GACHA":
                    if game.gacha_action_btn.collidepoint(mx, my):
                        if game.free_gacha_available:
                            game.free_gacha_available = False
                            reward_key = random.choices(
                                list(MAP_THEMES.keys()),
                                weights=[42, 27, 16, 9, 4, 2], k=1
                            )[0]
                            if reward_key not in game.owned_themes:
                                game.owned_themes.append(reward_key)
                            game.gacha_result_msg = f"[무료뽑기] '{MAP_THEMES[reward_key]['name']}' 획득!"
                        else:
                            if game.diamonds >= 2000:
                                game.diamonds -= 2000
                                reward_key = random.choices(
                                list(MAP_THEMES.keys()),
                                weights=[42, 27, 16, 9, 4, 2], k=1
                            )[0]
                                if reward_key not in game.owned_themes:
                                    game.owned_themes.append(reward_key)
                                game.gacha_result_msg = f"'{MAP_THEMES[reward_key]['name']}' ({MAP_THEMES[reward_key]['grade']}) 획득!"
                            else:
                                game.gacha_result_msg = "다이아가 부족합니다!"
                        continue

                # 스테이지 선택 팝업 내부 인터랙션
                if game.state == "STAGE_SELECT":
                    if game.chap_prev_btn.collidepoint(mx, my):
                        game.selected_chapter_idx = (game.selected_chapter_idx - 1) % len(CHAPTERS)
                        game.chapter_status_msg = ""
                        continue
                    if game.chap_next_btn.collidepoint(mx, my):
                        game.selected_chapter_idx = (game.selected_chapter_idx + 1) % len(CHAPTERS)
                        game.chapter_status_msg = ""
                        continue

                    chap = CHAPTERS[game.selected_chapter_idx]
                    if game.sweep_btn.collidepoint(mx, my):
                        if chap["id"] not in game.cleared_chapters:
                            game.chapter_status_msg = "먼저 관문을 클리어해야 빠른 소탕이 가능합니다!"
                        elif game.stamina < 5:
                            game.chapter_status_msg = "행동력(🍙)이 부족합니다!"
                        else:
                            game.stamina -= 5
                            game.diamonds += 200
                            game.chapter_status_msg = "빠른 소탕 완료! 💎 200 다이아 획득!"
                        continue

                    if game.enter_stage_btn.collidepoint(mx, my):
                        if game.stamina < 5:
                            game.chapter_status_msg = "행동력(🍙)이 부족합니다!"
                        else:
                            game.stamina -= 5
                            game.chapter_status_msg = ""
                            game.start_chapter(chap)
                        continue
                    continue

                if game.state in ["MAIN_MENU"]:
                    if game.shop_btn.collidepoint(mx, my):
                        game.state = "SHOP"
                        game.shop_msg = ""
                        continue
                    if game.event_btn.collidepoint(mx, my):
                        game.state = "EVENT"
                        game.event_msg = ""
                        continue
                    if game.quest_btn.collidepoint(mx, my):
                        game.state = "QUEST"
                        continue
                    if game.gacha_btn.collidepoint(mx, my):
                        game.state = "GACHA"
                        game.gacha_result_msg = ""
                        continue

                    if game.tab_inven_btn.collidepoint(mx, my):
                        game.main_tab = "INVENTORY"
                        continue
                    if game.tab_lobby_btn.collidepoint(mx, my):
                        game.main_tab = "LOBBY"
                        continue
                    if game.tab_upgrade_btn.collidepoint(mx, my):
                        game.main_tab = "UPGRADE"
                        continue

                    if game.main_tab == "UPGRADE":
                        for upgrade_rect, skill_id in game.upgrade_btns:
                            if upgrade_rect.collidepoint(mx, my):
                                game.purchase_upgrade(skill_id)
                                break
                        continue

                    if game.main_tab == "INVENTORY":
                        y_offset = HEADER_HEIGHT + 75
                        for t_key in MAP_THEMES.keys():
                            t_rect = pygame.Rect(45, y_offset, WIDTH - 90, 28)
                            if t_rect.collidepoint(mx, my):
                                if t_key in game.owned_themes:
                                    game.equipped_theme = t_key
                            y_offset += 32

                    if game.main_tab == "LOBBY":
                        if game.stage_start_btn.collidepoint(mx, my):
                            game.state = "STAGE_SELECT"
                            game.chapter_status_msg = ""
                            continue
                    
                    continue

                if game.state == "SURRENDER_POPUP":
                    for b_rect, b_name in game.popup_btns:
                        if b_rect.collidepoint(mx, my):
                            if b_name == "후퇴하기":
                                game.state = "MAIN_MENU"
                                game.main_tab = "LOBBY"
                            else:
                                game.state = "AIMING"
                    continue

                elif game.state == "LEVELUP":
                    for card, sk in game.skill_btns:
                        if card.collidepoint(mx, my):
                            game.select_skill(sk)
                    continue

                elif game.state == "AWAKENING":
                    # 각성 연출 중에는 다른 조작이 입력되지 않도록 한다.
                    continue

                elif game.state in ["GAME_OVER", "VICTORY"]:
                    for b_rect, b_name in game.popup_btns:
                        if b_rect.collidepoint(mx, my):
                            game.state = "MAIN_MENU"
                            game.main_tab = "LOBBY"
                    continue

                if game.surrender_btn.collidepoint(mx, my):
                    game.state = "SURRENDER_POPUP"
                    continue

                if game.skip_btn.collidepoint(mx, my):
                    game.recall_balls()
                    continue

                if game.state == "AIMING" and FIELD_TOP < my < FIELD_BOTTOM:
                    game.is_aiming = True

            elif event.type == pygame.MOUSEMOTION:
                if game.state == "SHOP" and game.shop_selected_item and game.shop_slider_dragging:
                    mx, my = event.pos
                    ratio = max(0.0, min(1.0, (mx - game.shop_slider_rect.x) / game.shop_slider_rect.width))
                    game.shop_quantity = max(1, min(10, 1 + round(ratio * 9)))
                if game.is_aiming:
                    mx, my = event.pos
                    dx = mx - game.launcher_x
                    dy = my - game.launcher_y
                    angle = math.atan2(dy, dx)
                    if angle < -math.pi + 0.1:
                        angle = -math.pi + 0.1
                    elif angle > -0.1:
                        angle = -0.1
                    game.aim_angle = angle

            elif event.type == pygame.MOUSEBUTTONUP:
                game.shop_slider_dragging = False
                if game.is_aiming:
                    game.is_aiming = False
                    game.fire_balls()

        game.update()
        game.draw()
        clock.tick(FPS)

if __name__ == "__main__":
    main()