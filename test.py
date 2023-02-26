import cv2
import mediapipe as mp
import math
import time
import pygame
import random
import os

FPS = 120
WIDTH = 1000
HEIGHT = 700

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# 難度調整
rock_quantity = 0
speed_y_upper = 0
speed_y_lower = 0
upgrading_time = 0
# difficulty = 0

# 遊戲初始化&創建視窗
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("星際戰艦生存戰")
clock = pygame.time.Clock()

# 載入圖片
background_img = pygame.image.load(os.path.join("img", "background.jpg")).convert()
player_img = pygame.image.load(os.path.join("img", "universeship.png")).convert()
# player_img = pygame.image.load(os.path.join("img", "player.png")).convert()
player_mini_img = pygame.transform.scale(player_img, (25, 19))
player_mini_img.set_colorkey(BLACK)
pygame.display.set_icon(player_mini_img)
bullet_img = pygame.image.load(os.path.join("img", "bullet.png")).convert()
rock_imgs = []
for i in range(6):
    rock_imgs.append(pygame.image.load(os.path.join("img", f"rock{i}.png")).convert())
    # rock_imgs.append(pygame.transform.scale(rock_original_imgs, (random.randint(50,150), random.randint(38,114))))

explosion_animation = {'Large_Explosion': [], "Small_Explosion": [], 'Player': []}

for i in range(9):
    explosion_img = pygame.image.load(os.path.join("img", f"expl{i}.png"))
    explosion_img.set_colorkey(BLACK)
    explosion_animation['Large_Explosion'].append(pygame.transform.scale(explosion_img, (75, 75)))
    explosion_animation['Small_Explosion'].append(pygame.transform.scale(explosion_img, (30, 30)))
    player_expl_img = pygame.image.load(os.path.join("img", f"player_expl{i}.png")).convert()
    player_expl_img.set_colorkey(BLACK)
    explosion_animation['Player'].append(player_expl_img)

power_imgs = {'shield': pygame.image.load(os.path.join("img", "shield.png")).convert(),
              'gun': pygame.image.load(os.path.join("img", "gun.png")).convert()}

# 載入音樂、音效
shoot_sound = pygame.mixer.Sound(os.path.join("sound", "shoot.wav"))
gun_sound = pygame.mixer.Sound(os.path.join("sound", "pow1.wav"))
shield_sound = pygame.mixer.Sound(os.path.join("sound", "pow0.wav"))
die_sound = pygame.mixer.Sound(os.path.join("sound", "rumble.ogg"))
explosion_sounds = [
    pygame.mixer.Sound(os.path.join("sound", "expl0.wav")),
    pygame.mixer.Sound(os.path.join("sound", "expl1.wav"))
]
pygame.mixer.music.load(os.path.join("sound", "background.ogg"))
pygame.mixer.music.set_volume(0.3)
font_name = os.path.join("font.ttf")

# OpenCV Declarations
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

# 全域變數
x2 = 0
y2 = 0
x_wrist2 = 0
y_wrist2 = 0
length2 = 0
slope = 0
shoot = False
y_shoot_upper = 0
y_shoot_lower = 0
shoot_time = 0
gun_time = 0
now = 0
shoot_now = 0


# 中文&英文文字顯示
def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, False, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.centerx = x
    text_rect.top = y
    surf.blit(text_surface, text_rect)


def new_rock():
    rock = Rock()
    all_sprites.add(rock)
    rocks.add(rock)


def draw_health(surf, hp, x, y):
    if hp < 0:
        hp = 0

    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (hp / 100) * BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)


def draw_lives(surf, lives, img, x, y):
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + 30 * i
        img_rect.y = y
        surf.blit(img, img_rect)


# 開始畫面
def draw_init():
    font = pygame.font.SysFont("Arial", 48)
    screen.blit(background_img, (0, 0))
    draw_text(screen, "星際戰艦生存戰!", 64, WIDTH / 2, HEIGHT / 4)
    draw_text(screen, '操作方式', 48, WIDTH / 2, HEIGHT * 25 / 64)
    draw_text(screen, '← →移動飛船 空白鍵發射子彈', 25, WIDTH / 2, HEIGHT * 16 / 32)
    draw_text(screen, '雙手作虛擬方向盤移動飛船 大拇指控制子彈發射', 25, WIDTH / 2, HEIGHT * 18 / 32)
    draw_text(screen, '請選擇難度開始遊戲', 25, WIDTH / 2, HEIGHT * 20 / 32)
    # draw_text(screen, '按任意鍵開始遊戲!', 18, WIDTH / 2, HEIGHT * 3 / 4)

    # 難度按鈕顯示
    text_easy = font.render("  easy  ", True, WHITE)
    text_easy_rect = text_easy.get_rect(center=(WIDTH / 4, HEIGHT * 3 / 4))
    # text_easy.set_alpha(100)
    text_normal = font.render("  normal  ", True, WHITE)
    text_normal_rect = text_normal.get_rect(center=(WIDTH / 2, HEIGHT * 3 / 4))
    text_hard = font.render("  hard  ", True, WHITE)
    text_hard_rect = text_hard.get_rect(center=(WIDTH * 3 / 4, HEIGHT * 3 / 4))
    pygame.display.update()

    waiting = True
    button_clicked = False

    global rock_quantity
    global speed_y_upper
    global speed_y_lower
    global upgrading_time
    global shoot_interval
    global percentage

    # 待機畫面迴圈
    while waiting:
        clock.tick(FPS)

        # 取得輸入
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                return True

            elif event.type == pygame.KEYUP:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if text_easy_rect.collidepoint(event.pos):
                    button_clicked = True
                    rock_quantity = 8
                    speed_y_upper = 3
                    speed_y_lower = 1
                    upgrading_time = 10000
                    shoot_interval = 200
                    percentage = 0.6

                elif text_normal_rect.collidepoint(event.pos):
                    button_clicked = True
                    rock_quantity = 14
                    speed_y_upper = 6
                    speed_y_lower = 2
                    upgrading_time = 5000
                    shoot_interval = 400
                    percentage = 0.85

                elif text_hard_rect.collidepoint(event.pos):
                    button_clicked = True
                    rock_quantity = 20
                    speed_y_upper = 10
                    speed_y_lower = 6
                    upgrading_time = 2500
                    shoot_interval = 1000
                    percentage = 0.9

                else:
                    button_clicked = False

        pygame.draw.rect(screen, (106, 90, 205), text_easy_rect, border_radius=15)
        screen.blit(text_easy, text_easy_rect)
        pygame.draw.rect(screen, (106, 90, 205), text_normal_rect, border_radius=15)
        screen.blit(text_normal, text_normal_rect)
        pygame.draw.rect(screen, (106, 90, 205), text_hard_rect, border_radius=15)
        screen.blit(text_hard, text_hard_rect)

        if button_clicked:
            waiting = False

        pygame.display.update()


# 玩家物件宣告
class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # self.image = pygame.transform.scale(player_img, (50, 38))
        self.image = pygame.transform.scale(player_img, (100, 76))
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.radius = 35
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.x = 200
        self.rect.y = 200
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 100
        self.health = 100
        self.lives = 3
        self.hidden = False
        self.hide_time = 0
        self.gun = 1
        self.gun_time = 0
        self.shoot_time = 0
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        now = pygame.time.get_ticks()
        if self.gun > 1 and now - self.gun_time > upgrading_time:
            self.gun -= 1
            self.gun_time = now

        if self.hidden and now - self.hide_time > 1300:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.bottom = HEIGHT - 10

        key_pressed = pygame.key.get_pressed()

        if key_pressed[pygame.K_SPACE] and now - self.shoot_time > shoot_interval:
            player.shoot()
            self.gun_time = now

        # 以斜率判斷右轉
        if slope < 0:
            if slope * 10 > -20:
                self.rect.x -= slope * 10

        # 以斜率判斷左轉
        if slope > 0:
            if slope * 10 < 20:
                self.rect.x -= slope * 10

        if key_pressed[pygame.K_RIGHT]:
            self.rect.x += 6
        if key_pressed[pygame.K_LEFT]:
            self.rect.x -= 6
        if key_pressed[pygame.K_DOWN]:
            self.rect.y += 6
        if key_pressed[pygame.K_UP]:
            self.rect.y -= 6

        # if key_pressed[pygame.K_SPACE]:
        #     player.shoot()
        if not self.hidden:
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH
            if self.rect.bottom > HEIGHT:
                self.rect.bottom = HEIGHT
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.top < 0:
                self.rect.top = 0

    def shoot(self):
        if not self.hidden:
            if self.gun == 1:
                bullet = Bullet(self.rect.centerx, self.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)
                shoot_sound.play()

            elif self.gun == 2:
                bullet1 = Bullet(self.rect.left + 30, self.rect.centery-30)
                bullet2 = Bullet(self.rect.right - 30, self.rect.centery-30)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                bullets.add(bullet1)
                bullets.add(bullet2)
                shoot_sound.play()

            elif self.gun >= 3:
                bullet1 = Bullet(self.rect.left + 10, self.rect.centery)
                bullet2 = Bullet(self.rect.centerx, self.rect.top)
                bullet3 = Bullet(self.rect.right - 10, self.rect.centery)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                all_sprites.add(bullet3)
                bullets.add(bullet1)
                bullets.add(bullet2)
                bullets.add(bullet3)
                shoot_sound.play()
        self.shoot_time = pygame.time.get_ticks()

    def hide(self):
        self.hidden = True
        self.hide_time = pygame.time.get_ticks()
        self.rect.center = (WIDTH / 2, HEIGHT + 500)

    def gunup(self):
        self.gun += 1
        self.gun_time = pygame.time.get_ticks()


# 石頭物件宣告
class Rock(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image_origin = random.choice(rock_imgs)
        self.image_origin = pygame.transform.scale(self.image_origin, (random.randint(50, 200), random.randint(38, 152)))
        self.image_origin.set_colorkey(BLACK)
        self.image = self.image_origin.copy()
        self.rect = self.image.get_rect()
        self.radius = self.rect.width * 0.65 / 2
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedx = random.randrange(-5, 5)
        self.speedy = random.randrange(speed_y_lower, speed_y_upper)
        self.total_degree = 0
        self.rotate_degree = random.randrange(-4, 4)
        self.mask = pygame.mask.from_surface(self.image)

    def rotate(self):
        self.total_degree += self.rotate_degree
        self.total_degree = self.total_degree % 360
        self.image = pygame.transform.rotate(self.image_origin, self.total_degree)
        center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = center

    def update(self):
        self.rotate()
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
            self.rect.x = random.randrange(0, WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedx = random.randrange(-3, 3)
            self.speedy = random.randrange(2, 10)


# 子彈物件宣告
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = bullet_img
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()


# 爆炸動畫
class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = explosion_animation[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(explosion_animation[self.size]):
                self.kill()
            else:
                self.image = explosion_animation[self.size][self.frame]
                center = self.rect.center
                self.rect = self.image.get_rect()
                self.rect.center = center


# 回血和加強攻擊
class Power(pygame.sprite.Sprite):
    def __init__(self, center):
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(['shield', 'gun'])
        self.image = power_imgs[self.type]
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 8

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()


# 根據兩點的座標，計算角度
def vector_2d_angle(v1, v2):
    # 座標
    v1_x = v1[0]
    v1_y = v1[1]
    v2_x = v2[0]
    v2_y = v2[1]

    # 向量內積求角度
    try:
        angle_ = math.degrees(math.acos(
            (v1_x * v2_x + v1_y * v2_y) / (((v1_x ** 2 + v1_y ** 2) ** 0.5) * ((v2_x ** 2 + v2_y ** 2) ** 0.5))))
    except:
        angle_ = 180
    return angle_


# 根據傳入的 21 個節點座標，得到該手指的角度
def hand_angle(hand_):
    angle_list = []

    # thumb 大拇指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0]) - int(hand_[2][0])), (int(hand_[0][1]) - int(hand_[2][1]))),
        ((int(hand_[3][0]) - int(hand_[4][0])), (int(hand_[3][1]) - int(hand_[4][1])))
        )

    # 判斷手心手背
    # if (round((int(hand_[0][0]) - int(hand_[2][0])), 0)) < 0:
    #     print("現在辨識為手背")
    # else:
    #     print("現在辨識為手心")

    angle_list.append(angle_)

    # index 食指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0]) - int(hand_[6][0])), (int(hand_[0][1]) - int(hand_[6][1]))),
        ((int(hand_[7][0]) - int(hand_[8][0])), (int(hand_[7][1]) - int(hand_[8][1])))
    )
    angle_list.append(angle_)

    # middle 中指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0]) - int(hand_[10][0])), (int(hand_[0][1]) - int(hand_[10][1]))),
        ((int(hand_[11][0]) - int(hand_[12][0])), (int(hand_[11][1]) - int(hand_[12][1])))
    )
    angle_list.append(angle_)

    # ring 無名指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0]) - int(hand_[14][0])), (int(hand_[0][1]) - int(hand_[14][1]))),
        ((int(hand_[15][0]) - int(hand_[16][0])), (int(hand_[15][1]) - int(hand_[16][1])))
    )
    angle_list.append(angle_)

    # pink 小拇指角度
    angle_ = vector_2d_angle(
        ((int(hand_[0][0]) - int(hand_[18][0])), (int(hand_[0][1]) - int(hand_[18][1]))),
        ((int(hand_[19][0]) - int(hand_[20][0])), (int(hand_[19][1]) - int(hand_[20][1])))
    )
    angle_list.append(angle_)

    # 輸出手指間角度列表
    for num in range(0, 5):
        angle_list[num] = round(angle_list[num], 2)

    print("手指間角度: " + str(angle_list))
    return angle_list


# 根據手指角度的串列內容，返回對應的手勢名稱
def hand_pos(fingers_angle):
    f1 = fingers_angle[0]  # 大拇指角度
    f2 = fingers_angle[1]  # 食指角度
    f3 = fingers_angle[2]  # 中指角度
    f4 = fingers_angle[3]  # 無名指角度
    f5 = fingers_angle[4]  # 小拇指角度
    # print(finger_angle)
    # 小於 90 表示手指伸直，大於等於 90 表示手指捲縮
    if f1 < 90 and f2 >= 90 and f3 >= 90 and f4 >= 90 and f5 >= 90:
        return 'good'
    elif f1 >= 90 and f2 >= 90 and f3 < 90 and f4 >= 90 and f5 >= 90:
        return 'fuck!!!'
    elif f1 < 90 and f2 < 90 and f3 >= 90 and f4 >= 90 and f5 < 90:
        return 'ROCK!'
    elif f1 >= 90 and f2 >= 90 and f3 >= 90 and f4 >= 90 and f5 >= 90:
        return '0'
    elif f1 >= 90 and f2 >= 90 and f3 >= 90 and f4 >= 90 and f5 < 90:
        return 'pink'
    elif f1 >= 90 and f2 < 90 and f3 >= 90 and f4 >= 90 and f5 >= 90:
        return '1'
    elif f1 >= 90 and f2 < 90 and f3 < 90 and f4 >= 90 and f5 >= 90:
        return '2'
    elif f1 >= 90 and f2 >= 90 and f3 < 90 and f4 < 90 and f5 < 90:
        return 'ok'
    elif f1 < 90 and f2 >= 90 and f3 < 90 and f4 < 90 and f5 < 90:
        return 'ok'
    elif f1 >= 90 and f2 < 90 and f3 < 90 and f4 < 90 and f5 > 90:
        return '3'
    elif f1 >= 90 and f2 < 90 and f3 < 90 and f4 < 90 and f5 < 90:
        return '4'
    elif f1 < 90 and f2 < 90 and f3 < 90 and f4 < 90 and f5 < 90:
        return '5'
    elif f1 < 90 and f2 >= 90 and f3 >= 90 and f4 >= 90 and f5 < 90:
        return '6'
    elif f1 < 90 and f2 < 90 and f3 >= 90 and f4 >= 90 and f5 >= 90:
        return '7'
    elif f1 < 90 and f2 < 90 and f3 < 90 and f4 >= 90 and f5 >= 90:
        return '8'
    elif f1 < 90 and f2 < 90 and f3 < 90 and f4 < 90 and f5 >= 90:
        return '9'
    else:
        return ''


cap = cv2.VideoCapture(0)  # 讀取攝影機
fontFace = cv2.FONT_HERSHEY_SIMPLEX  # 印出文字的字型
lineType = cv2.LINE_AA  # 印出文字的邊框
pTime = 0  # 開始時間初始化
cTime = 0  # 目前時間初始化

pygame.mixer.music.play(-1)

show_init = True
running = True

with mp_hands.Hands(
        max_num_hands=2,  # 偵測手掌數量
        model_complexity=1,  # 模型複雜度
        min_detection_confidence=0.7,  # 最小偵測自信度
        min_tracking_confidence=0.7) as hands:  # 最小追蹤自信度

    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    w, h = 640, 480  # 影像尺寸 width:640, height:480
    # 遊戲迴圈
    while running and cap.isOpened():
        ret, img = cap.read()
        img = cv2.resize(img, (w, h))  # 縮小尺寸，加快處理效率

        if show_init:
            close = draw_init()
            if close:
                break
            show_init = False

            all_sprites = pygame.sprite.Group()
            rocks = pygame.sprite.Group()
            bullets = pygame.sprite.Group()
            powers = pygame.sprite.Group()
            player = Player()
            all_sprites.add(player)

            for i in range(rock_quantity):
                new_rock()

            score = 0

        clock.tick(FPS)  # Frames per second

        # 影像翻轉
        img = cv2.flip(img, 1)

        img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 轉換成 RGB 色彩
        results = hands.process(img2)  # 偵測手勢

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                finger_points = []  # 記錄手指節點座標的串列

                for i in hand_landmarks.landmark:
                    # 將 21 個節點換算成座標，記錄到 finger_points
                    x = i.x * w
                    y = i.y * h
                    x1 = hand_landmarks.landmark[4].x * w  # 取得大拇指末端 x 座標
                    y1 = hand_landmarks.landmark[4].y * h  # 取得大拇指末端 y 座標
                    x_wrist1 = hand_landmarks.landmark[0].x * w  # 取得手掌末端 x 座標
                    y_wrist1 = hand_landmarks.landmark[0].y * h  # 取得手掌末端 y 座標
                    z_wrist1 = hand_landmarks.landmark[0].z
                    finger_points.append((x, y))

                    y_shoot_upper = hand_landmarks.landmark[4].y * h
                    y_shoot_lower = hand_landmarks.landmark[6].y * h

                    if y_shoot_lower - y_shoot_upper > 30:
                        shoot = True
                        shoot_time = pygame.time.get_ticks()
                    else:
                        shoot = False
                    now = pygame.time.get_ticks()
                    key_pressed = pygame.key.get_pressed()

                    if abs(now - shoot_time) > shoot_interval:
                        player.shoot()
                        shoot_time = now
                    # print(y_shoot_lower - y_shoot_upper)
                    # print(shoot_time - now)
                # 計算斜率並輸出
                try:
                    m = round(((y1 - y2) / (x1 - x2) * (-1)), 2)
                except:
                    pass
                slope = m
                print("斜率: " + str(m))
                x1_output = round(x1, 0)
                y1_output = round(y1, 0)
                print("大拇指末端座標: " + str(x1_output) + ", " + str(y1_output))
                print("z軸相對座標: " + str(z_wrist1))

                # 計算手掌間距離並輸出
                length1 = math.sqrt((abs(x_wrist1 - x_wrist2) * abs(x_wrist1 - x_wrist2)) + (
                            abs(y_wrist1 - y_wrist2) * abs(y_wrist1 - y_wrist2)))
                length1_output = round(length1, 2)
                print("手掌間距離: " + str(length1_output))

                # 計算雙手手掌間距離和前一次數據差值並輸出
                length_gap = round((length1 - length2), 2)
                print("雙手手掌間距離和前一次數據差值: " + str(length_gap))
                x2 = x1
                y2 = y1
                x_wrist2 = x_wrist1
                y_wrist2 = y_wrist1
                length2 = length1

                # 以斜率判斷轉彎方向
                if m > 0:
                    cv2.putText(img, "Turn Left", (30, 120), fontFace, 2, (255, 255, 255), 10, lineType)
                else:
                    cv2.putText(img, "Turn Right", (30, 120), fontFace, 2, (255, 255, 255), 10, lineType)

                if finger_points:
                    finger_angle = hand_angle(finger_points)  # 計算手指角度，回傳長度為 5 的串列
                    # print(finger_angle)  # 印出角度
                    text = hand_pos(finger_angle)  # 取得手勢所回傳的內容
                    # cv2.putText(img, text, (30, 120), fontFace, 5, (255, 255, 255), 10, lineType)  # 印出文字

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 將節點和骨架繪製到影像中
                mp_drawing.draw_landmarks(
                    img,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

        # 將幀率顯示在影像上
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, str(int(fps)), (600, 30), fontFace, 1, (0, 255, 0), 2, lineType)

        cv2.imshow('finger_recognition', img)

        # 按下esc結束程式
        if cv2.waitKey(1) & 0xFF == 27:
            break

        # 取得輸入
        key_pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # elif event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_SPACE:
            #         player.shoot()

        # 更新遊戲
        all_sprites.update()
        # 判斷石頭 子彈相撞
        hits = pygame.sprite.groupcollide(rocks, bullets, True, True)
        for hit in hits:
            random.choice(explosion_sounds).play()
            score += int(hit.radius)
            explosion = Explosion(hit.rect.center, 'Large_Explosion')
            all_sprites.add(explosion)

            if random.random() > percentage:
                power = Power(hit.rect.center)
                all_sprites.add(power)
                powers.add(power)
            new_rock()
        # 判斷石頭 飛船相撞
        hits = pygame.sprite.collide_mask(player, rock)
        for hit in hits:
            new_rock()
            explosion = Explosion(hit.rect.center, 'Small_Explosion')
            all_sprites.add(explosion)
            player.health -= hit.radius

            if player.health <= 0:
                death_expl = Explosion(player.rect.center, 'Player')
                all_sprites.add(death_expl)
                die_sound.play()
                player.lives -= 1

                if player.lives > 0:
                    player.health = 100
                player.hide()

        # 判斷寶物 飛船相撞
        hits = pygame.sprite.spritecollideany(player, powers, pygame.sprite.collide_mask)
        for hit in hits:
            if hit.type == 'shield':
                player.health += 20

                if player.health > 100:
                    player.health = 100
                shield_sound.play()

            elif hit.type == 'gun':
                player.gunup()
                gun_sound.play()
        slope = 0

        if player.lives == 0 and not (death_expl.alive()):
            show_init = True

        # 畫面顯示
        # screen.fill(BLACK)
        screen.blit(background_img, (0, 0))
        all_sprites.draw(screen)
        draw_text(screen, str(score), 18, WIDTH / 2, 10)
        draw_health(screen, player.health, 25, 17)
        draw_text(screen, "HP", 14, 12, 11)
        draw_lives(screen, player.lives, player_mini_img, WIDTH - 110, 15)
        pygame.display.update()

pygame.quit()
cap.release()
cv2.destroyAllWindows()
