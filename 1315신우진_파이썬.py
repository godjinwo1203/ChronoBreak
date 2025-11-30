import importlib
import subprocess
import sys

def install_and_import(package):
    try:
        importlib.import_module(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_and_import("ursina")

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.trail_renderer import TrailRenderer
from ursina.shaders import matcap_shader
from random import *
from math import *

app = Ursina()
window.fullscreen = True

unit_size = 36
map_parent = Entity()

corridor_list = [
    None, 
    'jiksun_bokdo.obj', 
    '90do_bokdo_R.obj', 
    '90do_bokdo_L.obj', 
    'samguri_bokdo.obj', 
    'sipja_bokdo.obj'
]

room_candidates = [
    'huanpung_bang.obj',
    'server_bang.obj',
    'gukri_bang.obj',
    'computer_bang.obj'
]

map_1 = [
    [0, 0, ('b', 0), 0, ('b', 0), 0, 0],
    [0, ('b', 90), (2, 180), (1, 90), (2, 270), ('b', 90), 0],
    [0, 0, (1, 0), 0, (1, 0), 0, 0],
    [('b', 90), (1, 90), (5, 0), (1, 90), (5, 0), (1, 90), ('b', 90)],
    [0, 0, (1, 0), 0, (1, 0), 0, 0],
    [0, ('b', 90), (2, 90), (4, 180), (2, 0), ('b', 90), 0],
    [0, 0, 0, ('s', 180), 0, 0, 0]
]

player = FirstPersonController()
player.gravity = 1
player.cursor.visible = True
player.scale = (2,2,2)
player.speed = 10
player.y = 5
player.collider = BoxCollider(player, center=Vec3(0,1,0), size=Vec3(2,3,2))

player_hp = 100
player_max_hp = 100
last_hit_time = 0
hp_regen_timer = 0

card = Entity(parent=camera, model='card_key.obj', collider='mesh', scale=(0.2,0.2,0.2),
              position=(0.6,-0.5,1.5), rotation=(5,0,-90), enabled=False)

gun = Entity(parent=camera, model='gun.obj', scale=Vec3(0.2,0.2,0.2),
              position=Vec3(0.55,-0.85,1.5), rotation=(-5,-10,0),
              color=color.white, shader=matcap_shader, texture='metal_matcap_gun.jpg', enabled=False)
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
skill_gauge = 10
is_skill_depleted = False
skill_recovery_timer = 0
player_hand = 1

ui_parent=Entity(parent=camera.ui)
bullet_ui = Text(text=str(tanchang_num_p)+' / '+str(bullet_num_p), scale=2, position=(-0.75, -0.4))
hp_ui = Text(text='HP: ' + str(player_hp), scale=2, position=(-0.75, -0.3), color=color.red)

skill_bg_ui = Entity(parent=ui_parent, model='quad', color=color.gray, scale=(0.35, 0.05), position=(-0.7, 0.45), origin=(-.5, .5))
skill_fill_ui = Entity(parent=ui_parent, model='quad', color=color.gold, scale=(0.35, 0.05), position=(-0.7, 0.45), origin=(-.5, .5))
skill_bg_ui.z=0
skill_fill_ui.z=-0.1

# [추가] 엘리베이터 클래스
'''
class Elevator(Entity):
    def __init__(self, position, rotation_y=0):
        super().__init__(position=position, rotation_y=rotation_y)
        
        # 1. 구조물 생성 (바닥, 벽, 천장)
        # 바닥 (플레이어가 밟고 올라가야 하므로 collider 필수)
        self.floor = Entity(parent=self, model='cube', scale=(15, 1, 15), color=color.dark_gray, collider='box', texture='white_cube')
        # 천장
        self.ceiling = Entity(parent=self, model='cube', scale=(15, 1, 15), position=(0, 10, 0), color=color.dark_gray, texture='white_cube')
        # 벽 (3면)
        self.wall_back = Entity(parent=self, model='cube', scale=(15, 10, 1), position=(0, 5, 7.5), color=color.gray, collider='box', texture='brick')
        self.wall_left = Entity(parent=self, model='cube', scale=(1, 10, 15), position=(-7.5, 5, 0), color=color.gray, collider='box', texture='brick')
        self.wall_right = Entity(parent=self, model='cube', scale=(1, 10, 15), position=(7.5, 5, 0), color=color.gray, collider='box', texture='brick')
        
        # 문 (앞쪽) - 애니메이션을 위해 좌우로 나눔
        self.door_l = Entity(parent=self, model='cube', scale=(7.5, 10, 1), position=(-3.75, 5, -7.5), color=color.light_gray, collider='box', texture='brick')
        self.door_r = Entity(parent=self, model='cube', scale=(7.5, 10, 1), position=(3.75, 5, -7.5), color=color.light_gray, collider='box', texture='brick')
        
        self.is_operating = False
        self.is_open = False

    def ascend(self):
        # 엘리베이터 상승 애니메이션 (바닥 및 자식 엔티티들 모두 올라감)
        # 플레이어는 바닥 collider 위에 서 있으면 물리 엔진에 의해 같이 올라감
        self.animate_y(self.y + 20, duration=5, curve=curve.in_out_quad)
        print("Elevator going up!")

    def close_door_and_go(self):
        # 문 닫기
        self.door_l.animate_position((-3.75, 5, -7.5), duration=1, curve=curve.in_out_quad)
        self.door_r.animate_position((3.75, 5, -7.5), duration=1, curve=curve.in_out_quad)
        # 문 닫히고 나서 상승 (1초 뒤)
        invoke(self.ascend, delay=1.5)

    def check_trigger(self):
        global player_hand
        
        # 3번(카드키) 들고, 거리 가깝고, F 누르고, 작동 중이 아닐 때
        if player_hand == 3 and not self.is_operating:
            if distance(self.position, player.position) <= 20 and held_keys['f']:
                self.is_operating = True
                
                # 1. 문 열기
                # 왼쪽 문은 왼쪽으로, 오른쪽 문은 오른쪽으로 슬라이드
                self.door_l.animate_position((-7, 5, -7.5), duration=1, curve=curve.out_quad)
                self.door_r.animate_position((7, 5, -7.5), duration=1, curve=curve.out_quad)
                
                # 2. 3초 뒤 닫고 출발
                invoke(self.close_door_and_go, delay=3)

    def update(self):
        self.check_trigger()
'''
class Door(Entity):
    def __init__(self, position, rotation_y=0):
        super().__init__(
            model='door.obj',
            texture='brick',
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
            if distance(self.position, player.position) <= 40 and held_keys['f']:
                if not self.is_open:
                    self.is_open = True
                    target_pos = self.position + self.left * 40 
                    self.animate_position(target_pos, duration=0.5, curve=curve.out_quad)
                    invoke(self.close_door, delay=5)

    def update(self):
        self.check_open()

class Gun(Entity):
    def __init__(self, parent):
        super().__init__(name='gun')
        self.gun = Entity(parent=parent, model='gun.obj', position=Vec3(0,0.2,0), scale=Vec3(0.4,0.4,0.2), color=color.gray, rotation=(-90,0,0))
        self.muzzle = Entity(parent=self.gun, position=Vec3(0,gun.scale_y/2+0.05,0))

class Enemy(Entity):
    def __init__(self, position, hp=150):
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
        self.body = Entity(parent=self, name='body', model='cube', color=color.red, collider='box', scale=(1.5,3,1), y=1.5)
        self.body.owner = self
        self.head = Entity(parent=scene, name='head', model='sphere', color=color.orange, scale=(1,1,1), collider='box')
        self.head.position = self.body.world_position + Vec3(0, 2, 0)
        self.head.owner = self
        self.right_arm = Entity(parent=self.body, name='right_arm', model='cube', color=color.orange, scale=(1,1,1), collider='box', rotation=(90,0,0))
        self.right_arm.world_scale = Vec3(0.5,1.5,0.5)
        self.right_arm.world_position = position + (self.body.scale_x/2+self.right_arm.world_scale_x/2, self.body.scale_y/2 + 0.5, 0) + (0,0.5,0.5)
        self.right_arm.owner = self
        self.left_arm = Entity(parent=self.body, name='left_arm', model='cube', color=color.orange, scale=(1,1,1), collider='box')
        self.left_arm.world_scale = Vec3(0.5,1.5,0.5)
        self.left_arm.world_position = position + (-self.body.scale_x/2-self.left_arm.world_scale_x/2, self.body.scale_y/2 + 0.5, 0)
        self.left_arm.owner = self
        self.gun = Gun(parent=self.right_arm)
    
    def summon_bullet(self):
        pos = self.gun.muzzle.world_position
        target_pos = player.position + Vec3(0, 1.5, 0)
        vec_to_player = target_pos - pos
        
        # [수정 1] 총알이 아래로 처박히지 않게 수평(y=0) 유지
        # 하지만 총구 높이와 플레이어 높이가 다를 수 있으므로 방향 벡터만 평평하게 보정
        vec_to_player.y = 0  # 높이 차이 무시하고 수평 발사
        
        dir = vec_to_player.normalized()
        bullets_e.append(BulletE(position=pos, direction=dir))

    def look_player(self):
        player_head = player.world_position + Vec3(0, 1.7, 0)
        self.head.position = self.body.world_position + Vec3(0, 2, 0)
        self.head.look_at(player_head)
        target_rot = self.head.rotation 
        self.head.rotation = lerp(self.head.rotation, target_rot, 6 * time.dt)
        dir = player.world_position - self.body.world_position
        dir.y = 0
        if dir.length() > 0.001:
            target_yaw = math.degrees(math.atan2(dir.x, dir.z))
            current_yaw = self.body.rotation_y
            diff = (target_yaw - current_yaw + 180) % 360 - 180
            new_yaw = current_yaw + diff * (2 * time.dt)
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
            print("Enemy Death!")
            destroy(self)
            return True
        else: return False

    def drop_rooting(self):
        rootings.append(Entity(model='tanchang.obj', position=self.world_position+(0,0.5,0), color=color.dark_gray, scale=(0.3,0.3,0.3)))
    
    def update(self):
        if self.death_enemy(): return
        if self.is_reloading:
            self.reload_timer += time.dt
            if self.reload_timer >= self.reload_time:
                self.current_ammo = self.max_ammo
                self.is_reloading = False
                self.reload_timer = 0
            return
        dist = distance(self.body.world_position, player.world_position)
        if dist < 120:
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
        self.trail = TrailRenderer(parent=self, size=(0.1,0.1), length=7, alpha=0.2, enabled=False)
        self.trail.ready=False
        invoke(self.set_trail, delay=0.05)

    def set_trail(self):
        if self: self.trail.ready=True

    def check_hit(self):
        hit = self.intersects()
        if not hit.hit or hit.entity is None: return
        if hit.entity.name in ('head', 'body'):
            enemy = getattr(hit.entity, 'owner', None)
            if enemy:
                damage = 20 if hit.entity.name == 'head' else 10
                enemy.hp -= damage
                print(f"{hit.entity.name} hit! Enemy HP: {enemy.hp}")
            destroy(self)
        elif hit.entity.name != 'Player': 
            destroy(self)

    def update(self):
        if not self or not self.enabled: return
        super().update()
        if self.trail.ready:
            if self.trail.enabled!=isSkilling:
                try: self.trail.enabled=isSkilling
                except Exception: pass

class BulletE(Bullet):
    def __init__(self, position, direction):
        super().__init__(position=position, direction= direction, owner='Enemy', speed=80)
        self.world_scale=(0.2,0.2,0.3)
        self.trail = TrailRenderer(parent=self, size=(0.1,0.1), length=7, alpha=0.2, enabled=False)
        self.trail.ready=False
        invoke(self.set_trail, delay=0.05)

    def set_trail(self):
        if self: self.trail.ready=True

    def check_hit(self):
        global player_hp, last_hit_time
        hit = self.intersects()
        if not hit.hit or hit.entity is None: return
        
        if hit.entity == player:
            player_hp -= 10
            last_hit_time = time.time()
            print(f"Player Hit! HP: {player_hp}")
            if player_hp <= 0:
                print("GAME OVER")
                application.pause()
            destroy(self)
        elif hit.entity.name == 'body': 
            player_hp -= 10
            last_hit_time = time.time()
            print(f"Player Hit! HP: {player_hp}")
            if player_hp <= 0:
                print("GAME OVER")
                application.pause()
            destroy(self)

    def update(self):
        super().update()
        if self.trail.ready:
            if self.trail.enabled!=isSkilling:
                try: self.trail.enabled=isSkilling
                except Exception: pass

def spawn_door(x, z, rotation):
    Door(position=(x, 3, z), rotation_y=rotation) # [수정 3] 문 높이 Y=3으로 설정

def spawn_corridor(x, z, type_idx, rotation):
    if type_idx >= len(corridor_list) or corridor_list[type_idx] is None: return
    model_name = corridor_list[type_idx]
    
    if type_idx != 1:
        count = randint(0, 2)
        for _ in range(count):
            offset_x = uniform(-5, 5)
            offset_z = uniform(-5, 5)
            enemies.append(Enemy(position=(x + offset_x, 1, z + offset_z)))

    Entity(parent=map_parent, model=model_name, texture='brick', scale=1, position=(x, 0, z), rotation_y=rotation, collider='mesh')

def spawn_room(x, z, room_type, rotation):
    model_name = 'cube'
    if room_type == 's':
        model_name = 'start_bang.obj'
        player.position = Vec3(x, 5, z)
    elif room_type == 'e':
        model_name = 'start_bang.obj' 
        # [추가] 엔딩 방(e)이면 엘리베이터 생성
        #Elevator(position=(x, 0, z), rotation_y=rotation)
    elif room_type == 'b':
        model_name = choice(room_candidates)
        count = randint(1, 3)
        for _ in range(count):
            offset_x = uniform(-5, 5)
            offset_z = uniform(-5, 5)
            enemies.append(Enemy(position=(x + offset_x, 1, z + offset_z)))

    Entity(parent=map_parent, model=model_name, texture='brick', scale=1, position=(x, -1, z), rotation_y=rotation, collider='mesh')

def generate_map(template):
    global map_parent
    destroy(map_parent)
    map_parent = Entity()
    print("맵 생성 시작...")
    
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
    print("생성 완료!")

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
    global shoot_in_reload, tanchang_num_p, player_hand, player_hp, hp_regen_timer, skill_recovery_timer, is_skill_depleted
    time_slice_shoot += time.dt

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
            skill_fill_ui.scale_x = skill_gauge * 0.035
            if skill_gauge <= 0:
                skill_gauge = 0
                isSkilling = False
                is_skill_depleted = True
                skill_fill_ui.z = 0.1
                Chronobreak_down()
    
    if is_skill_depleted:
        skill_recovery_timer += time.dt
        skill_fill_ui.scale_x = (skill_recovery_timer / 10) * 0.35
        if skill_recovery_timer >= 10:
            skill_gauge = 10
            is_skill_depleted = False
            skill_fill_ui.scale_x = 0.35
            skill_recovery_timer = 0

    if player_hand == 3:
        pass 
        
    if rootings != []:
        if held_keys['f']:
            for r in rootings:
                if distance(player.position, r.position) < 3:
                    print("탄창 획득")
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
        if hp_regen_timer >= 2:
            player_hp += 20
            if player_hp > player_max_hp: player_hp = player_max_hp
            hp_regen_timer = 0
    else:
        hp_regen_timer = 0

    bullet_ui.text=str(tanchang_num_p)+' / '+str(bullet_num_p)
    hp_ui.text = 'HP: ' + str(player_hp)

generate_map(map_1)

DirectionalLight(y=10, z=10, shadows=True, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(100,100,100,100))

app.run()