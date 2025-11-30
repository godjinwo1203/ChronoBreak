from ursina import *
from random import choice

app = Ursina()

unit_size = 8.5

map_parent = Entity()

corridor_list = [
    None,                       # 0번: 비움
    'jiksun_bokdo.obj',         # 1번: 직선
    '90do_bokdo_R.obj',         # 2번: 꺾임 (오른쪽)
    '90do_bokdo_L.obj',         # 3번: 꺾임 (왼쪽)
    'samguri_bokdo.obj',        # 4번: T자
    'sipja_bokdo.obj'           # 5번: 십자
]

room_candidates = [
    'huanpung_bang.obj',
    'server_bang.obj',
    'gukri_bang',
    'computer_bang.obj'
]

level_template = [
    [0,         ('b', 0),    0,         0,         0,         0,         0],
    [0,         (3, 90),     (1, 90),    (3, 180),  ('b', 0),  0,         0],
    [0,         (1, 0),     0,         (1, 0),   0,         0,         0],
    [('b', 0),  (3, 0),      (3, 180),  (4, 0),    ('b', 0),  0,         0],
    [0,         0,           (1, 0),   (2, 0),    (1, 90),    (2, 270),  0],
    [0,         ('s', 90),    (3, 0),    (3, 180),  (1, 90),    (4, 0),    ('b', 0)],
    [0,         0,           0,         (1, 0),   0,         (1, 0),   0],
    [0,         0,           ('b', 0),  (4, 0),    (1, 90),    (3, 0),    ('b', 0)],
    [0,         0,           0,         ('b', 0),  0,         0,         0]
]

# --- [추가됨] 문 생성 함수 ---
def spawn_door(x, z, rotation):
    Entity(
        parent=map_parent,
        model='door.obj',      # 문 모델 (없으면 cube로 테스트)
        texture='brick',
        scale=0.2,             # 다른 모델들과 스케일 맞춤
        position=(x, 0, z),
        rotation_y=rotation,   # 가로/세로 방향에 따라 회전
        collider='mesh'        # 혹은 'box'
    )

def spawn_corridor(x, z, type_idx, rotation):
    if type_idx >= len(corridor_list) or corridor_list[type_idx] is None:
        return

    model_name = corridor_list[type_idx]
    
    Entity(
        parent=map_parent,
        model=model_name,
        texture='brick',
        scale=0.2,
        position=(x, 0, z),
        rotation_y=rotation,
        collider='mesh'
    )

def spawn_room(x, z, room_type, rotation):
    model_name = 'cube'
    
    if room_type == 's':
        model_name = 'start_bang.obj'
        camera.position = (x, 40, z - 20)
        camera.look_at((x, 0, z))
        
    elif room_type == 'e':
        model_name = 'start_bang.obj' # end_bang이 없어서 임시로 start 사용
        
    elif room_type == 'b':
        model_name = choice(room_candidates)

    Entity(
        parent=map_parent,
        model=model_name,
        texture='brick', 
        scale=0.2,
        position=(x, 0, z),
        rotation_y=rotation,
        collider='mesh'
    )

# --- [수정됨] 맵 생성 + 문 배치 로직 ---
def generate_map():
    global map_parent
    destroy(map_parent)
    map_parent = Entity()
    
    print("맵 생성 시작...")
    
    # 맵 전체 크기 확인
    rows = len(level_template)
    cols = len(level_template[0])

    for z_idx, row in enumerate(level_template):
        for x_idx, item in enumerate(row):
            
            real_x = x_idx * unit_size
            real_z = -z_idx * unit_size
            
            # 1. 빈 공간(0)이면 건너뜀
            if item == 0:
                continue

            # --- [기존 로직] 타일(복도/방) 생성 ---
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

            # --- [추가 로직] 문(Door) 생성 ---
            # 원리: 현재 타일이 있고, 오른쪽/아래쪽 타일도 있다면 그 사이(중간지점)에 문을 설치
            
            # (1) 오른쪽(x+1) 확인 -> 가로로 연결됨 -> 세로 문(90도 회전) 설치
            if x_idx + 1 < cols: # 인덱스 범위 체크
                right_item = row[x_idx + 1]
                if right_item != 0: # 오른쪽 칸도 빈칸이 아니라면
                    # 위치: 현재 타일과 오른쪽 타일의 중간 지점
                    door_x = real_x + (unit_size / 2)
                    spawn_door(door_x, real_z, 90)

            # (2) 아래쪽(z+1) 확인 -> 세로로 연결됨 -> 가로 문(0도 회전) 설치
            if z_idx + 1 < rows: # 인덱스 범위 체크
                bottom_item = level_template[z_idx + 1][x_idx]
                if bottom_item != 0: # 아래쪽 칸도 빈칸이 아니라면
                    # 위치: 현재 타일과 아래쪽 타일의 중간 지점
                    door_z = real_z - (unit_size / 2)
                    spawn_door(real_x, door_z, 0)

    print("생성 완료!")

DirectionalLight(y=10, z=10, shadows=True, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(100,100,100,100))

EditorCamera()

def input(key):
    if key == 'space':
        generate_map()

generate_map()

Text(text='[SPACE]: Generate Map with Doors', position=(-0.85, 0.45), scale=1.5)
app.run()