from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import matcap_shader
from random import *
from math import *

app = Ursina()

# [변경 2] 요청하신 텍스처를 미리 로드합니다.
my_texture = "brick"

window.fullscreen = True
window.color = color.black

unit_size = 36
map_parent = Entity()

game_state = 'menu' 
menu_index = 0
start_spawn_pos = Vec3(0, 10, 0)
# 엔딩 박스 참조를 위한 전역 변수
ending_box_entity = None 

corridor_list = [None, 'jiksun_bokdo.obj', '90do_bokdo_R.obj', '90do_bokdo_L.obj', 'samguri_bokdo.obj', 'sipja_bokdo.obj']
room_candidates = ['huanpung_bang.obj', 'server_bang.obj', 'gukri_bang.obj']

map = [
    [0, 0, ('b', 0), 0, ('e', 180), 0, 0],
    [0, ('b', 90), (5, 0), (1, 90), (5, 0), ('b', 90), 0],
    [0, 0, (1, 0), 0, (1, 0), 0, 0],
    [('b', 90), (1, 90), (5, 0), (1, 90), (5, 0), (1, 90), ('b', 90)],
    [0, 0, (1, 0), 0, (1, 0), 0, 0],
    [0, ('b', 90), (2, 90), (4, 180), (2, 0), ('b', 90), 0],
    [0, 0, 0, ('s', 180), 0, 0, 0]
]

player = FirstPersonController()
player.gravity = 1
player.scale = (2,2,2)
player.speed = 10
player.y = 5
player.collider = BoxCollider(player, center=Vec3(0,1,0), size=Vec3(2,3,2))
player.enabled = False 

player_hp = 200
player_max_hp = 200
last_hit_time = 0
hp_regen_timer = 0

game_time_limit = 300 
current_game_time = 300

card = Entity(parent=camera, model='card_key.obj', scale=(0.2,0.2,0.2), position=(0.6,-0.5,1.5), rotation=(5,0,-90), color=color.cyan, enabled=False)
gun = Entity(parent=camera, model='gun.obj', scale=Vec3(0.2,0.2,0.2), position=Vec3(0.55,-0.85,1.5), rotation=(-5,-10,0), color=color.white, shader=matcap_shader, texture='metal_matcap_gun.jpg', enabled=False)
gun.muzzle = Entity(parent=gun, position=Vec3(-2.2,3.8,gun.scale_z/2+1), rotation=(-5,-10,0))
gun.original_position = gun.position
gun.original_rotation = gun.rotation

shoot_cooldown = 0.2
time_slice_shoot = shoot_cooldown
bullets_p=[]
bullets_e=[]
rootings=[]
enemies = []

valorant_recoil_pattern = [
    (0.2, 0),(0.4, 0), (0.6, 0.05), (0.7, -0.05), (0.8, 0), (0.8, 0), (0.6, 0.1),
    (0.3, 0.5), (0.1, 1.0), (0.05, 1.5), (0, 1.8), (0, 2.0),
    (0, -0.5), (0, -1.5), (0, -2.0), (0, -2.2), (0, -2.2), (0, -2.0),
    (0, 0.5), (0, 0.75), (0, 1), (0, -0.5), (0, -0.75),
    (0, -1), (0, -0.5), (0, -0.75), (0, -1), (0, 0.5)
]

base_spread = 0.002       
move_spread_factor = 0.05
spray_spread_factor = 0.005
recoil_index = 0
accumulated_recoil = Vec2(0,0)
last_shoot_time = 0

reload_time = 3.0
reload_timer = 0.0
isReloading = False
bullet_num_p = 30
shoot_in_reload = False
tanchang_num_p = 5

isSkilling = False
skill_gauge = 5
is_skill_depleted = False
skill_recovery_timer = 0
player_hand = 1

ui_parent=Entity(parent=camera.ui)
bullet_ui = Text(text='', scale=2, position=(-0.75, -0.4), enabled=False)
hp_ui = Text(text='', scale=2, position=(-0.75, -0.3), color=color.red, enabled=False)
timer_ui = Text(text='', scale=2, position=(-0.7, 0.35), color=color.black, enabled=False)

skill_bg_ui = Entity(parent=ui_parent, model='quad', color=color.gray, scale=(0.35, 0.05), position=(-0.7, 0.45), origin=(-.5, .5), enabled=False)
skill_fill_ui = Entity(parent=ui_parent, model='quad', color=color.gold, scale=(0.35, 0.05), position=(-0.7, 0.45), origin=(-.5, .5), enabled=False)
skill_bg_ui.z=0.1
skill_fill_ui.z=-0.1

# [추가 1] 상호작용 UI (화면 중앙 하단)
interaction_ui = Text(
    text='', 
    scale=2, 
    origin=(0, 0), 
    position=(0, -0.3), 
    color=color.white,
    enabled=False
)

# --- UI 그룹 ---
start_menu = Entity(parent=camera.ui, enabled=True)
game_over_menu = Entity(parent=camera.ui, enabled=False)
game_clear_menu = Entity(parent=camera.ui, enabled=False) 

menu_bg = Entity(parent=start_menu, model='quad', color=color.rgba(0, 0, 0, 0.85), scale=(2, 2), z=1)
title_logo = Entity(parent=start_menu, model='quad', texture='ChronoBreak_Logo.png', scale=(0.4, 0.4), position=(-0.4, 0.25), color=color.white, z=0)
title_shadow = Text(parent=start_menu, text='ChronoBreak', scale=4, origin=(0,0), position=(0.205, 0.245), color=color.black, z=0.1)
title_text = Text(parent=start_menu, text='ChronoBreak', scale=4, origin=(0,0), position=(0.2, 0.25), color=color.cyan, z=0)

btn_group = Entity(parent=start_menu, position=(0, -0.1))
selection_arrow = Text(parent=btn_group, text='>', scale=2, origin=(0,0), color=color.yellow, position=(-0.3, 0))
start_btn_text = Text(parent=btn_group, text='GAME START', scale=2, origin=(0,0), position=(0, 0), color=color.white) 
exit_btn_text = Text(parent=btn_group, text='EXIT', scale=1.5, origin=(0,0), position=(0, -0.15), color=color.gray)

over_bg = Entity(parent=game_over_menu, model='quad', color=color.rgba(0, 0, 0, 0.9), scale=(2, 2), z=1)
over_text = Text(parent=game_over_menu, text='GAME OVER', scale=4, origin=(0,0), position=(0,0.2), color=color.red)
retry_btn_text = Text(parent=game_over_menu, text='RETRY', scale=2, origin=(0,0), position=(0, -0.1), color=color.white) 
over_exit_btn_text = Text(parent=game_over_menu, text='EXIT', scale=1.5, origin=(0,0), position=(0, -0.25), color=color.gray)
over_arrow = Text(parent=game_over_menu, text='>', scale=2, origin=(0,0), color=color.yellow, position=(-0.2, -0.1))

clear_bg = Entity(parent=game_clear_menu, model='quad', color=color.rgba(0, 0, 0, 0.9), scale=(2, 2), z=1)
clear_text = Text(parent=game_clear_menu, text='ESCAPE SUCCEED', scale=4, origin=(0,0), position=(0,0.2), color=color.cyan)
clear_retry_btn_text = Text(parent=game_clear_menu, text='REPLAY', scale=2, origin=(0,0), position=(0, -0.1), color=color.white) 
clear_exit_btn_text = Text(parent=game_clear_menu, text='EXIT', scale=1.5, origin=(0,0), position=(0, -0.25), color=color.gray)
clear_arrow = Text(parent=game_clear_menu, text='>', scale=2, origin=(0,0), color=color.yellow, position=(-0.2, -0.1))

def update_menu_ui():
    global menu_index
    if game_state == 'menu':
        if menu_index == 0:
            selection_arrow.position = (-0.35, 0)
            start_btn_text.color = color.yellow
            start_btn_text.scale = 2.2
            exit_btn_text.color = color.gray
            exit_btn_text.scale = 1.5
        else:
            selection_arrow.position = (-0.25, -0.15)
            start_btn_text.color = color.gray
            start_btn_text.scale = 1.5
            exit_btn_text.color = color.yellow
            exit_btn_text.scale = 2.2
    elif game_state == 'game_over':
        if menu_index == 0:
            over_arrow.position = (-0.2, -0.1)
            retry_btn_text.color = color.yellow
            retry_btn_text.scale = 2.2
            over_exit_btn_text.color = color.gray
            over_exit_btn_text.scale = 1.5
        else:
            over_arrow.position = (-0.15, -0.25)
            retry_btn_text.color = color.gray
            retry_btn_text.scale = 1.5
            over_exit_btn_text.color = color.yellow
            over_exit_btn_text.scale = 2.2
    elif game_state == 'game_clear':
        if menu_index == 0:
            clear_arrow.position = (-0.2, -0.1)
            clear_retry_btn_text.color = color.yellow
            clear_retry_btn_text.scale = 2.2
            clear_exit_btn_text.color = color.gray
            clear_exit_btn_text.scale = 1.5
        else:
            clear_arrow.position = (-0.15, -0.25)
            clear_retry_btn_text.color = color.gray
            clear_retry_btn_text.scale = 1.5
            clear_exit_btn_text.color = color.yellow
            clear_exit_btn_text.scale = 2.2

# [추가 2] 컷씬 종료 후 조작 활성화 함수
def enable_player_control():
    player.speed = 10
    player.mouse_sensitivity = Vec2(40, 40) # 기본 감도 복구

def start_game():
    global game_state, player_hp, bullet_num_p, tanchang_num_p, skill_gauge, player_hand, current_game_time
    game_state = 'playing'
    
    start_menu.enabled = False
    game_over_menu.enabled = False
    game_clear_menu.enabled = False
    
    player_hp = 200 
    bullet_num_p = 30
    tanchang_num_p = 5
    skill_gauge = 5
    current_game_time = game_time_limit
    
    player_hand = 1
    gun.enabled = False
    card.enabled = False
    
    bullet_ui.enabled = True
    hp_ui.enabled = True
    timer_ui.enabled = True
    skill_bg_ui.enabled = True
    skill_fill_ui.enabled = True
    
    player.enabled = True
    player.position = start_spawn_pos 
    
    mouse.locked = True
    mouse.visible = False
    
    # [추가 2] 오프닝 컷씬 로직
    # 1. 조작 불가능하게 설정
    player.speed = 0
    player.mouse_sensitivity = Vec2(0, 0)
    
    # 2. 시선을 아래로 내림
    camera.rotation_x = 60 
    
    # 3. 2.5초 동안 부드럽게 정면(0)으로 고개 들기
    camera.animate_rotation_x(0, duration=2.5, curve=curve.in_out_quad)
    
    # 4. 2.5초 뒤 조작 활성화
    invoke(enable_player_control, delay=2.5)

def restart_game():
    global enemies, bullets_p, bullets_e, rootings, ending_box_entity
    for e in enemies: destroy(e)
    for b in bullets_p: destroy(b)
    for b in bullets_e: destroy(b)
    for r in rootings: destroy(r)
    
    # 엔딩 박스도 삭제하고 다시 생성해야 함 (참조 잃음 방지)
    if ending_box_entity:
        destroy(ending_box_entity)
        ending_box_entity = None

    enemies = []
    bullets_p = []
    bullets_e = []
    rootings = []
    
    generate_map(map)
    start_game()

def quit_game():
    application.quit()

def show_game_over():
    global game_state, menu_index
    game_state = 'game_over'
    menu_index = 0
    update_menu_ui()
    player.enabled = False
    mouse.locked = False
    mouse.visible = False 
    gun.enabled = False
    card.enabled = False
    game_over_menu.enabled = True
    interaction_ui.enabled = False # 게임오버 시 상호작용 텍스트 숨김

def show_game_clear():
    global game_state, menu_index
    game_state = 'game_clear'
    menu_index = 0
    update_menu_ui()
    player.enabled = False
    mouse.locked = False
    mouse.visible = False
    gun.enabled = False
    card.enabled = False
    game_clear_menu.enabled = True
    interaction_ui.enabled = False

def input(key):
    global menu_index
    if game_state == 'menu':
        if key == 'up arrow':
            menu_index = 0
            update_menu_ui()
        elif key == 'down arrow':
            menu_index = 1
            update_menu_ui()
        elif key == 'enter':
            if menu_index == 0: start_game()
            else: quit_game()
    elif game_state == 'game_over':
        if key == 'up arrow':
            menu_index = 0
            update_menu_ui()
        elif key == 'down arrow':
            menu_index = 1
            update_menu_ui()
        elif key == 'enter':
            if menu_index == 0: restart_game()
            else: quit_game()
    elif game_state == 'game_clear':
        if key == 'up arrow':
            menu_index = 0
            update_menu_ui()
        elif key == 'down arrow':
            menu_index = 1
            update_menu_ui()
        elif key == 'enter':
            if menu_index == 0: restart_game()
            else: quit_game()

class EndingBox(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube', 
            texture='white_cube',
            color=color.yellow,
            alpha=0.7,
            scale=(2, 2, 2),
            position=position,
            collider='box'
        )
        
    def update(self):
        if game_state == 'playing':
            if distance(self.position, player.position) <= 10 and held_keys['f']:
                show_game_clear()

class Gate(Entity):
    def __init__(self, position, rotation_y=0):
        super().__init__(
            model='gate.obj', 
            texture=my_texture, # [변경 3] 게이트 텍스처 변경
            scale=1,
            position=position, 
            rotation_y=rotation_y, 
            collider='box'
        )
        self.original_y = position[1]
        self.is_open = False

    def close_gate(self):
        self.animate_y(self.original_y, duration=0.5, curve=curve.in_out_quad)
        self.is_open = False

    def check_open(self):
        global player_hand
        if player_hand == 3:
            if distance(self.position, player.position) <= 10 and held_keys['f']:
                if not self.is_open:
                    self.is_open = True
                    target_y = self.original_y + 10 
                    self.animate_y(target_y, duration=1, curve=curve.out_quad)
                    invoke(self.close_gate, delay=5)

    def update(self):
        if game_state == 'playing': self.check_open()

class Door(Entity):
    def __init__(self, position, rotation_y=0):
        super().__init__(
            model='door.obj', 
            texture=my_texture, # [변경 4] 문 텍스처 변경
            scale=1,
            position=position, 
            rotation_y=rotation_y, 
            collider='box'
        )
        self.original_position = position
        self.is_open = False

    def close_door(self):
        self.animate_position(self.original_position, duration=0.5, curve=curve.in_out_quad)
        self.is_open = False

    def check_open(self):
        global player_hand
        if player_hand == 3:
            if distance(self.position, player.position) <= 10 and held_keys['f']:
                if not self.is_open:
                    self.is_open = True
                    target_pos = self.position + self.left * 40 
                    self.animate_position(target_pos, duration=0.5, curve=curve.out_quad)
                    invoke(self.close_door, delay=5)

    def update(self):
        if game_state == 'playing': self.check_open()

class Gun(Entity):
    def __init__(self, parent):
        super().__init__(name='gun')
        self.gun = Entity(parent=parent, model='gun.obj', position=Vec3(0,0.2,0), scale=Vec3(0.4,0.4,0.2), color=color.gray, rotation=(-90,0,0))
        self.muzzle = Entity(parent=self.gun, position=Vec3(0,gun.scale_y/2+0.05,0))

class Enemy(Entity):
    def __init__(self, position, hp=100): 
        super().__init__(position=Vec3(*position), name='enemy_root')
        self.hp = hp
        self.shoot_cooldown = 0.7 
        self.shoot_timer = 0.0
        self.speed = 3.5
        self.min_dist = 15
        self.combat_range = 25
        self.max_ammo = 20
        self.current_ammo = self.max_ammo
        self.reload_time = 5.0
        self.reload_timer = 0.0
        self.is_reloading = False
        self.has_seen_player = False
        self.first_sight_timer = 0.0
        self.first_sight_delay = 1.0 

        self.body = Entity(parent=self, name='body', model='cube', color=color.dark_gray, collider='box', scale=(1.5,3,1), y=1.5)
        self.body.owner = self
        self.head = Entity(parent=scene, name='head', model='sphere', color=color.red, scale=(1,1,1), collider='box')
        self.head.position = self.body.world_position + Vec3(0, 2, 0)
        self.head.owner = self
        self.right_arm = Entity(parent=self.body, name='right_arm', model='cube', color=color.gray, scale=(1,1,1), collider='box', rotation=(90,0,0))
        self.right_arm.world_scale = Vec3(0.5,1.5,0.5)
        self.right_arm.world_position = position + (self.body.scale_x/2+self.right_arm.world_scale_x/2, self.body.scale_y/2 + 0.5, 0) + (0,0.5,0.5)
        self.right_arm.owner = self
        self.left_arm = Entity(parent=self.body, name='left_arm', model='cube', color=color.gray, scale=(1,1,1), collider='box')
        self.left_arm.world_scale = Vec3(0.5,1.5,0.5)
        self.left_arm.world_position = position + (-self.body.scale_x/2-self.left_arm.world_scale_x/2, self.body.scale_y/2 + 0.5, 0)
        self.left_arm.owner = self
        self.gun = Gun(parent=self.right_arm)
    
    def summon_bullet(self):
        pos = self.gun.muzzle.world_position
        current_angle = self.head.world_rotation_y
        target_angle = current_angle - 10
        rad = math.radians(target_angle)
        dir_x = math.sin(rad)
        dir_z = math.cos(rad)
        direction = Vec3(dir_x, 0, dir_z).normalized()
        bullets_e.append(BulletE(position=pos, direction=direction))

    def look_player(self):
        player_head = player.world_position + Vec3(0, 1.7, 0)
        self.head.position = self.body.world_position + Vec3(0, 2, 0)
        self.head.look_at(player_head)
        target_rot = self.head.rotation 
        self.head.rotation = lerp(self.head.rotation, target_rot, 9 * time.dt)
        dir = player.world_position - self.body.world_position
        dir.y = 0
        if dir.length() > 0.001:
            target_yaw = math.degrees(math.atan2(dir.x, dir.z))
            current_yaw = self.body.rotation_y
            diff = (target_yaw - current_yaw + 180) % 360 - 180
            new_yaw = current_yaw + diff * (3 * time.dt)
            self.body.rotation_y = new_yaw

    def move_enemy(self):
        dist = distance(self.position, player.position)
        dir_player = player.position - self.position
        dir_player.y = 0
        dir_player = dir_player.normalized()
        move_vec = Vec3(0,0,0)
        if dist <= self.min_dist or self.current_ammo == 0: 
            move_vec = -dir_player
        elif dist < self.combat_range:
            move_vec = Vec3(0,0,0)
        else:
            move_vec = dir_player
        
        if move_vec.length() > 0:
            origin = self.position + Vec3(0, 1.5, 0)
            right_vec = Vec3(move_vec.z, 0, -move_vec.x).normalized()
            body_width = 1.0 
            check_dist = 2.0
            ignore_list = (self, player, self.body, self.head, self.right_arm, self.left_arm, self.gun)
            hit_mid = raycast(origin, move_vec, distance=check_dist, ignore=ignore_list)
            hit_left = raycast(origin - right_vec * body_width, move_vec, distance=check_dist, ignore=ignore_list)
            hit_right = raycast(origin + right_vec * body_width, move_vec, distance=check_dist, ignore=ignore_list)
            if hit_mid.hit or hit_left.hit or hit_right.hit:
                move_vec = Vec3(0,0,0)

        self.position += move_vec * self.speed * time.dt
        ground_check = raycast(self.position + Vec3(0,1,0), Vec3(0,-1,0), distance=1.6, ignore=(self, player, self.body))
        if not ground_check.hit:
            self.y -= 10 * time.dt        
    
    def death_enemy(self):
        if self.hp <= 0:
            self.drop_rooting()
            if self.head: destroy(self.head)
            if self.gun: destroy(self.gun)
            destroy(self)
            return True
        else: return False

    def drop_rooting(self):
        rootings.append(Entity(model='tanchang.obj', position=self.world_position+(0,0.5,0), color=color.dark_gray, scale=(0.3,0.3,0.3)))
    
    def update(self):
        if game_state != 'playing': return
        if self.death_enemy(): return
        
        dist = distance(self.position, player.position)
        if dist > 40:
            self.has_seen_player = False
            self.first_sight_timer = 0
            return

        if not self.has_seen_player:
            self.has_seen_player = True
            self.first_sight_timer = 0
            return 
        
        if self.first_sight_timer < self.first_sight_delay:
            self.first_sight_timer += time.dt
            self.look_player() 
            return

        if self.is_reloading:
            self.reload_timer += time.dt
            if self.reload_timer >= self.reload_time:
                self.current_ammo = self.max_ammo
                self.is_reloading = False
                self.reload_timer = 0
            return
        
        self.look_player()
        self.move_enemy()
        self.shoot_timer += time.dt
        
        if dist < 100 and self.shoot_timer >= self.shoot_cooldown:
            if self.current_ammo > 0:
                shoot_origin = self.gun.muzzle.world_position
                target_point = player.position + Vec3(0, 1.5, 0)
                vec_to_player = target_point - shoot_origin
                check_dist = vec_to_player.length()
                direction = vec_to_player.normalized()
                
                hit_info = raycast(shoot_origin, direction, distance=check_dist, ignore=(self, self.body, self.head, self.gun, self.right_arm, self.left_arm, self.gun.gun, self.gun.muzzle))
                
                if not hit_info.hit or hit_info.entity == player:
                    self.summon_bullet()
                    self.current_ammo -= 1
                    self.shoot_timer = 0
            else:
                self.is_reloading = True
     
class Bullet(Entity):
    def __init__(self, position, direction, speed=80, life_time=5.5, owner=None):
        super().__init__(model='bullet.obj', scale=(0.2,0.2,0.3),
                         color=color.gold, position=position, collider='box', texture='white_cube')
        self.direction = direction
        self.speed = speed
        self.life_time = life_time
        self.age = 0
        self.owner = owner
        self.look_at(self.position + self.direction)
        self.rotation_x +=90
    
    def move(self):
        self.position += self.direction * self.speed * time.dt

    @classmethod
    def check_hit(self): pass
        
    def update(self):
        if game_state != 'playing': return
        self.age += time.dt
        self.move()
        self.check_hit()
        if self.age > self.life_time: destroy(self)
        
class BulletP(Bullet):
    def __init__(self, position, direction):
        super().__init__(position=position, direction=direction, owner='Player')
        self.model = None 
        self.visual = Entity(parent=self, model='bullet.obj', color=color.gold, rotation=(-90,180,0))
        self.look_at(self.position + self.direction)

    def check_hit(self):
        hit = self.intersects()
        if not hit.hit or hit.entity is None: return
        if hit.entity.name in ('head', 'body'):
            enemy = getattr(hit.entity, 'owner', None)
            if enemy:
                damage = 30 if hit.entity.name == 'head' else 10
                enemy.hp -= damage
            destroy(self)
        elif hit.entity.name != 'Player': 
            destroy(self)

    def update(self):
        if not self or not self.enabled: return
        super().update()

class BulletE(Bullet):
    def __init__(self, position, direction):
        super().__init__(position=position, direction= direction, owner='Enemy', speed=80)
        self.world_scale=(0.2,0.2,0.3)

    def check_hit(self):
        global player_hp, last_hit_time
        hit = self.intersects()
        if not hit.hit or hit.entity is None: return
        
        if hit.entity == player:
            player_hp -= 10
            last_hit_time = time.time()
            if player_hp <= 0:
                show_game_over()
            destroy(self)
        elif hit.entity.name == 'body': 
            player_hp -= 10
            last_hit_time = time.time()
            if player_hp <= 0:
                show_game_over()
            destroy(self)

    def update(self):
        super().update()

def spawn_door(x, z, rotation):
    Door(position=(x, 3, z), rotation_y=rotation)

def spawn_corridor(x, z, type_idx, rotation):
    if type_idx >= len(corridor_list) or corridor_list[type_idx] is None: return
    model_name = corridor_list[type_idx]
    
    if type_idx in [4, 5]:
        count = randint(1, 3)
        for _ in range(count):
            offset_x = uniform(-5, 5)
            offset_z = uniform(-5, 5)
            enemies.append(Enemy(position=(x + offset_x, 1, z + offset_z)))

    Entity(
        parent=map_parent, 
        model=model_name, 
        texture=my_texture, # [변경 5] 복도 텍스처 변경
        scale=1, 
        position=(x, 0, z), 
        rotation_y=rotation, 
        collider='mesh'
    )

def spawn_room(x, z, room_type, rotation):
    global start_spawn_pos, ending_box_entity
    model_name = 'cube'
    spawn_y = -1
    
    if room_type == 's':
        model_name = 'start_bang.obj'
        spawn_y = 0 
        start_spawn_pos = Vec3(x - 5, 5, z - 5)
        
    elif room_type == 'e':
        model_name = 'end_bang.obj' 
        spawn_y = 0
        Gate(position=(x, 0, z), rotation_y=rotation)
        # [수정 2] 엔딩 박스 x 12
        ending_box_entity = EndingBox(position=(x + 12, 4, z + 30))
        
        count = randint(1, 3)
        for _ in range(count):
            offset_x = uniform(-5, 5)
            offset_z = uniform(-5, 5)
            enemies.append(Enemy(position=(x + offset_x, 1, z + offset_z)))

    elif room_type == 'b':
        model_name = choice(room_candidates)
        count = randint(1, 3)
        for _ in range(count):
            offset_x = uniform(-5, 5)
            offset_z = uniform(-5, 5)
            enemies.append(Enemy(position=(x + offset_x, 1, z + offset_z)))

    Entity(
        parent=map_parent, 
        model=model_name, 
        texture=my_texture, # [변경 6] 방 텍스처 변경
        scale=1, 
        position=(x, spawn_y, z), 
        rotation_y=rotation, 
        collider='mesh'
    )

def generate_map(template):
    global map_parent
    destroy(map_parent)
    map_parent = Entity()
    
    rows = len(template)
    cols = len(template[0])
    
    offset_right_x = 0   
    offset_right_z = 0   
    
    offset_bottom_x = 0 
    offset_bottom_z = 0 

    for z_idx, row in enumerate(template):
        for x_idx, item in enumerate(row):
            real_x = x_idx * unit_size
            real_z = -z_idx * unit_size
            
            if item == 0: continue

            code = None
            rot = 0
            if isinstance(item, tuple):
                code = item[0]
                rot = item[1]
            else:
                code = item
                rot = 0

            if isinstance(code, int):
                spawn_corridor(real_x, real_z, code, rot)
            elif isinstance(code, str):
                spawn_room(real_x, real_z, code, rot)

            if x_idx + 1 < cols:
                right_item = row[x_idx + 1]
                if right_item != 0:
                    door_x = real_x + (unit_size / 2) + offset_right_x
                    door_z = real_z + offset_right_z
                    spawn_door(door_x, door_z, 90)

            if z_idx + 1 < rows:
                bottom_item = template[z_idx + 1][x_idx]
                if bottom_item != 0:
                    door_x = real_x + offset_bottom_x
                    door_z = real_z - (unit_size / 2) + offset_bottom_z
                    spawn_door(door_x, door_z, 0)

def summon_bullet_P():
    global bullet_num_p, recoil_index, last_shoot_time
    gun.position -= Vec3(0, 0, 0.05) 
    gun.rotation_x -= 1
    gun.rotation_z += uniform(-0.4,0.4)
    gun.x = gun.original_position.x + uniform(-0.01, 0.01)

    for i in range(15):
        spark = Entity(parent=gun.muzzle, model='cube', color=color.orange, scale=0.05, position=(0, 0, 0), always_on_top=True, unlit=True)
        direction = Vec3(uniform(-0.5, 0.5), uniform(-0.5, 0.5), uniform(1.0, 2.0)).normalized()
        spark.look_at(spark.position + direction)
        spark.animate_position(spark.position + direction * 0.5, duration=0.1, curve=curve.out_expo)
        destroy(spark, delay=0.15)
    
    is_moving = held_keys['w'] or held_keys['s'] or held_keys['a'] or held_keys['d']
    spread = base_spread
    if is_moving: spread += move_spread_factor
    spread += min(recoil_index * spray_spread_factor, 0.1)
    random_spread = Vec3(uniform(-spread, spread), uniform(-spread, spread), 0)
    final_dir = (camera.forward + random_spread).normalized()
    pos = gun.muzzle.world_position
    bullets_p.append(BulletP(position=pos, direction=final_dir))
    bullet_num_p -= 1
    last_shoot_time = time.time()
    if recoil_index < len(valorant_recoil_pattern) - 1: recoil_index += 1

def animate_gun():
    gun.position = lerp(gun.position, gun.original_position, 15 * time.dt)
    target_rotation = gun.original_rotation
    recoil_offset = Vec3(-accumulated_recoil.x, accumulated_recoil.y, 0)
    final_target = target_rotation + recoil_offset
    gun.rotation = lerp(gun.rotation, final_target, 20 * time.dt)

def handle_recoil():
    global accumulated_recoil, recoil_index
    time_since_shot = time.time() - last_shoot_time
    if time_since_shot < 0.15: 
        idx = min(recoil_index, len(valorant_recoil_pattern)-1)
        pattern = valorant_recoil_pattern[idx]
        target_pitch = pattern[0]
        target_yaw   = pattern[1]
        recoil_force = 12 * time.dt 
        kick_up = lerp(0, target_pitch, recoil_force)
        kick_side = lerp(0, target_yaw, recoil_force)
        camera.rotation_x -= kick_up
        player.rotation_y += kick_side
        accumulated_recoil.x += kick_up
        if accumulated_recoil.x > 30: accumulated_recoil.x = 30
    elif time_since_shot > 0.3: 
        if recoil_index > 0: recoil_index = 0
        if abs(accumulated_recoil.x) > 0.001:
            smooth_factor = 8 * time.dt
            recover_x = accumulated_recoil.x * smooth_factor
            camera.rotation_x += recover_x
            accumulated_recoil.x -= recover_x
        else:
            accumulated_recoil.x = 0

def reload_gun():
    global bullet_num_p, tanchang_num_p
    bullet_num_p = 30
    tanchang_num_p -= 1

def Chronobreak():
    for e in bullets_e: e.speed = 2
    for b in bullets_p: b.speed = 2
    for enemy in enemies: enemy.speed=0.1

def Chronobreak_down():
    for b in bullets_p: b.speed = 80
    for e in bullets_e: e.speed = 80
    for enemy in enemies: enemy.speed=3.5

def update():
    global time_slice_shoot, reload_timer, isReloading, skill_gauge, isSkilling, accumulated_recoil
    global shoot_in_reload, tanchang_num_p, player_hand, player_hp, hp_regen_timer, skill_recovery_timer, is_skill_depleted, current_game_time
    time_slice_shoot += time.dt

    if game_state != 'playing': return

    current_game_time -= time.dt
    if current_game_time <= 0:
        show_game_over()
    
    minutes = int(current_game_time // 60)
    seconds = int(current_game_time % 60)
    timer_ui.text = f'{minutes:02}:{seconds:02}'
    
    if current_game_time < 60:
        timer_ui.color = color.red
    else:
        timer_ui.color = color.black

    if held_keys['1']:
        player_hand=1
        gun.enabled=False
        card.enabled=False
        player.speed=10
    elif held_keys['2']:
        player_hand=2
        gun.enabled=True
        card.enabled=False
        player.speed=7
    elif held_keys['3']:
        player_hand=3
        gun.enabled=False
        card.enabled=True
        player.speed=9

    if player_hand == 2:
        if held_keys['left mouse'] and time_slice_shoot >= shoot_cooldown and bullet_num_p > 0:
            summon_bullet_P()
            time_slice_shoot = 0
            if isReloading==True: shoot_in_reload=True

        if accumulated_recoil.x > 0:
            if mouse.velocity[1] < 0:
                recoil_reduction = abs(mouse.velocity[1]) * 4096 * time.dt
                accumulated_recoil.x -= recoil_reduction
                if accumulated_recoil.x < 0: accumulated_recoil.x = 0

        handle_recoil()
        animate_gun()

        if held_keys['r'] and isReloading == False and tanchang_num_p >= 1: isReloading = True
        elif tanchang_num_p < 1: pass 
        if isReloading:
            if shoot_in_reload:
                isReloading=False
                reload_timer=0.0
                shoot_in_reload=False
            reload_timer += time.dt
            if reload_timer >= reload_time:
                reload_gun()
                isReloading = False
                reload_timer = 0.0
        
    if not is_skill_depleted and held_keys['q'] and isSkilling == False and skill_gauge > 0: 
        isSkilling = True
        
    if isSkilling:
        if skill_gauge > 0:
            Chronobreak()
            skill_gauge -= time.dt
            skill_gauge = round(skill_gauge, 2)
            if skill_gauge <= 0:
                skill_gauge = 0
                isSkilling = False
                is_skill_depleted = True
                Chronobreak_down()
    
    if is_skill_depleted:
        skill_recovery_timer += time.dt
        if skill_recovery_timer >= 5:
            skill_gauge = 5
            is_skill_depleted = False
            skill_recovery_timer = 0

    skill_fill_ui.scale_x = (skill_gauge / 5.0) * 0.35

    interaction_ui.text = ''
    interaction_ui.enabled = False

    if rootings:
        closest_ammo = min(rootings, key=lambda r: distance(player.position, r.position))
        if distance(player.position, closest_ammo.position) < 3:
            interaction_ui.text = 'pick up magazine [F]'
            interaction_ui.enabled = True

    if ending_box_entity and distance(player.position, ending_box_entity.position) <= 10:
        interaction_ui.text = 'escape [F]'
        interaction_ui.enabled = True

    if player_hand == 3:
        pass 
        
    if rootings != []:
        if held_keys['f']:
            for r in rootings:
                if distance(player.position, r.position) < 3:

                    tanchang_num_p += 1
                    destroy(r)
    for r in rootings:
        if not r or not hasattr(r, 'position'): rootings.remove(r)

    for b in bullets_p:
        if not b or not hasattr(b, 'position'): bullets_p.remove(b)

    for e in enemies:
        if not e or not hasattr(e, 'position'): enemies.remove(e)
    
    if player_hp < player_max_hp and time.time() - last_hit_time > 2:
        hp_regen_timer += time.dt
        if hp_regen_timer >= 1: 
            player_hp += 10     
            if player_hp > player_max_hp: player_hp = player_max_hp
            hp_regen_timer = 0
    else:
        hp_regen_timer = 0

    bullet_ui.text=str(tanchang_num_p)+' / '+str(bullet_num_p)
    hp_ui.text = 'HP: ' + str(player_hp)

generate_map(map)

DirectionalLight(y=10, z=10, shadows=True, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(100,100,100,100))

mouse.visible = True
mouse.locked = False

app.run()
