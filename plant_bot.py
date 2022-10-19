# You can set the level at line number '300' 
# when initializing the PatternGen object.
# To hide the program comment out line at 421 line no.
# if some error occurred try to run the program again.
import random
import json
import string
import copy
from itertools import chain
from browser import document, html, window as win, bind, timer, ajax, console
from browser.session_storage import storage

SHOW_PROGRAM = False

class PatternGen:
    def __init__(self, level):
        self.level, self.direc_map, self.direc_map_rev, self.path_len, self.ctx, self.ground_paras = self.get_level_data(level)

        self.robot_start_coord, self.current_dir = self.get_start_point()
        self.major_func_list = [self.get_random_cmds, self.get_random_for_block, self.get_random_for_block]#, self.get_random_if_else_block]
        self.start_dir = self.current_dir.strip()
        self.str_list = []
        self.path_list = []
        self.local_path_list = [self.robot_start_coord]
        self.last_direction = []
        self.local_direction = []

        self.intersection_threshold = 0
        self.pattern = []

    def get_level_data(self, level):
        LEVEL = level
        PATH_LEN = (10*(2**LEVEL))
        DIREC_MAP = {1:"east", 2:"west", 3:"north", 4:"south"}
        DIREC_MAP_REV = {'east':1, 'west':2, 'north':3, 'south':4}

        if LEVEL in [1, 2]:
            main_canvas_width = 500
            main_canvas_height = 500
        elif LEVEL in [3, 4]:
            main_canvas_width = 800
            main_canvas_height = 800
        elif LEVEL in [5, 6]:
            main_canvas_width = 1200
            main_canvas_height = 1200

        CTX = None
        GROUND_PARAS = {
            "start_x" : 0,
            "start_y" : 0,
            "ground_w" : LEVEL*10,
            "ground_h" : LEVEL*10,
            "stage_w" : main_canvas_width/(LEVEL*10),
            "stage_h" : main_canvas_height/(LEVEL*10),
            "gap" : 0
        }
        return LEVEL, DIREC_MAP, DIREC_MAP_REV, PATH_LEN, CTX, GROUND_PARAS

    def get_start_point(self):
        max_point = (self.ground_paras['ground_h']-1, self.ground_paras['ground_w']-1)
        points = []
        boundry_points = []

        def get_dir(point = (0, 0)):
            if point[0] == 0 and point[1] <= max_point[1]:
                return random.choice(['east', 'north', 'south'])
            elif point[0] <= max_point[0] and point[1] == 0:
                return random.choice(['west', 'east', 'south'])
            elif point[0] == max_point[0] and point[1] <= max_point[1]:
                return random.choice(['west', 'north', 'south'])
            elif point[0] <= max_point[1] and point[1] == max_point[0]:
                return random.choice(['east', 'north', 'west'])

        for col in range(max_point[1]+1):
            for row in range(max_point[0]+1):
                points.append((row, col))
                if col == 0 or row == 0 or col == max_point[1] or row == max_point[0]:
                    boundry_points.append((row, col))
        start_point = random.choice(list(set(boundry_points)))
        start_dir = get_dir(point = start_point)
        return list(start_point), start_dir

    def next_direc(self, rotation_type = "cw"):
        if rotation_type == "cw":
            sequence = "1423"
        elif rotation_type == "ccw":
            sequence = "1324"
        index = sequence.index(str(self.direc_map_rev[self.current_dir]))
        new_index = index+1
        if new_index == 4:
            new_index = 0
        return int(sequence[new_index])

    def fwd(self):
        next_point = [0, 0]
        if self.current_dir == 'east':
            next_point[0] = self.local_path_list[-1][0]+1
            next_point[1] = self.local_path_list[-1][1]
        elif self.current_dir == 'west':
            next_point[0] = self.local_path_list[-1][0]-1
            next_point[1] = self.local_path_list[-1][1]
        elif self.current_dir == 'north':
            next_point[0] = self.local_path_list[-1][0]
            next_point[1] = self.local_path_list[-1][1]-1
        elif self.current_dir == 'south':
            next_point[0] = self.local_path_list[-1][0]
            next_point[1] = self.local_path_list[-1][1]+1
        return next_point
    
    def r_cw(self):
        """Set 'self.current_dir' instance variable/state"""
        self.current_dir = self.direc_map[self.next_direc(rotation_type="cw")]
    
    def r_ccw(self):
        """Set 'self.current_dir' instance variable/state"""
        self.current_dir = self.direc_map[self.next_direc(rotation_type="ccw")]
    
    def plant(self):
        """Append -1 to 2nd index of the current last point in the path_list"""
        self.local_path_list = list(map(list, self.local_path_list))
        self.local_path_list[-1].append("red")

    def good_cmds(self, command_list):
        command_list = command_list[:-1]
        if not "r_cw()" in command_list and not "r_ccw()" in command_list:
            return False
        elif "r_cw()\n\tr_ccw()" in "\n\t".join(command_list) or "r_ccw()\n\tr_cw()" in "\n\t".join(command_list) or "r_cw()\n\tr_cw()\n\tr_cw()" in "\n\t".join(command_list) or "r_ccw()\n\tr_ccw()\n\tr_ccw()" in "\n\t".join(command_list):
            return False
        elif not "fwd()" in command_list:
            return False
        return True

    def get_random_cmd_list(self, num):
        command_options = ['fwd()', 'r_cw()', 'r_ccw()', 'fwd()']
        command_list = []
        while not self.good_cmds(command_list):
            command_list = []
            for x in range(num-1):
                command_list.append(random.choice(command_options))
            command_list.append("plant()")
        return command_list

    def get_command_list_to_cmd_func_list(self, itern, cmd_list):
        command_func_list = []
        for y in range(itern):
            for command in cmd_list:
                if command == "fwd()":
                    command_func_list.append(self.fwd)
                elif command == "r_cw()":
                    command_func_list.append(self.r_cw)
                elif command == "r_ccw()":
                    command_func_list.append(self.r_ccw)
                elif command == "plant()":
                    command_func_list.append(self.plant)
        return command_func_list

    def get_random_for_block(self, num_of_commands_in_it = 3):
        alphabet_list = set()
        alpha = random.choice(string.ascii_lowercase)
        while alpha in alphabet_list:
            alpha = random.choice(string.ascii_lowercase)
        iteration = random.randint(2, 3)

        for_str = "for {alpha} in range({iteration}):".format(alpha = alpha, iteration = iteration)
        command_list = self.get_random_cmd_list(num_of_commands_in_it)
        for_str += "\n\t"+"\n\t".join(command_list)
        command_func_list = self.get_command_list_to_cmd_func_list(iteration, command_list)
        return (for_str, command_func_list)

    def get_random_cmds(self, num = 3):
        command_list = self.get_random_cmd_list(num)
        command_str = "\n"+"\n".join(command_list)+"\n"
        command_func_list = self.get_command_list_to_cmd_func_list(1, command_list)
        return (command_str, command_func_list)

    def is_pattern_ok(self):
        """Check if the current_path_list is equal to or greater than path_len"""
        flattened_path_list = list(chain.from_iterable(self.path_list)) # make self.path_list flat (A list containing coordinates)
        new_flat_path = set(map(lambda a: (a[0], a[1]), flattened_path_list)) # make a set of points discarding more than one same points
        return len(new_flat_path) >= self.path_len

    def sub_cmd_list_gen(self):
        """generate cmd list which includes a list"""
        run_list = []
        for _ in range(10):
            run_list.append(random.choice(self.major_func_list))
        sub_cmd_list = []
        sub_cmd_str = []
        for func in run_list:
            command_str, command_list = func(random.randint(4, 6))
            sub_cmd_list.append(command_list)
            sub_cmd_str.append(command_str)
        return sub_cmd_list, sub_cmd_str
    
    def point_linearity_threshold(self, point):
        point = tuple(point)
        if point in tuple(map(tuple, map(lambda item: (item[0], item[1]), self.local_path_list))) or point in tuple(map(lambda item: (item[0], item[1]), tuple(map(tuple, chain.from_iterable(self.path_list))))):
            return False
        return True

    def validate_this_point(self, next_point):
        max_point = (self.ground_paras['ground_w']-1, self.ground_paras['ground_h']-1)
        if next_point[0] >= 0 and next_point[0] <= max_point[0] and next_point[1] >= 0 and next_point[1] <= max_point[1] and self.point_linearity_threshold(next_point):
            return True
        return False

    def valid_arr(self, cmd_arr):
        local_direction_state = self.current_dir
        flag = False
        if self.path_list.__len__() != 0:
            flag = True
            self.local_path_list = [self.path_list[-1][-1]]
            self.current_dir = self.local_direction[-1]
        else:
            self.local_path_list = [self.robot_start_coord]
            self.current_dir = self.start_dir
        for cmd_index in range(len(cmd_arr)):
            next_point = cmd_arr[cmd_index]()
            if next_point is not None:
                if self.validate_this_point(next_point):
                    self.local_path_list.append(next_point)
                else:
                    self.current_dir = local_direction_state
                    return False, None
        return True, (self.local_path_list[1:] if flag else self.local_path_list)

    def path_resolver(self):
        """It will use backtracking algo to resolve the futher possible paths"""
        if self.is_pattern_ok():
            self.path_list = list(chain.from_iterable(self.path_list))
            return True

        sub_cmd_list, sub_cmd_str = self.sub_cmd_list_gen()
        for cmd_arr in zip(sub_cmd_list, sub_cmd_str):
            is_valid, corresponding_path_list = self.valid_arr(cmd_arr[0])
            if is_valid:
                self.last_direction = self.current_dir
                self.local_direction.append(self.current_dir)
                self.path_list.append(corresponding_path_list)
                self.str_list.append(cmd_arr[1])

                if self.path_resolver():
                    return True
        return False
    
    def pattern_mapper(self, custom_path_list = None):
        ground_w = self.ground_paras['ground_w']
        ground_h = self.ground_paras['ground_h']
        pattern = []
        for y in range(ground_h):
            tmp_pat = []
            for x in range(ground_w):
                tmp_pat.append(0)
            pattern.append(tmp_pat)

        if custom_path_list is not None:
            path_list_data = custom_path_list
        else:
            path_list_data = self.path_list
        
        if isinstance(self.path_list[0][0], list):
            path_list_data = list(chain.from_iterable(self.path_list))

        for value in path_list_data:
            if len(value) == 2:
                pattern[value[1]][value[0]] = 1
            elif len(value) > 2 and value[2] == "red":
                pattern[value[1]][value[0]] = 2

        if custom_path_list is None:
            self.pattern = pattern
        try:
            path_list_x_y_dir = list(map(lambda a: (a[0], a[1]) if len(a) == 2 else (a[0], a[1], 'red'), self.path_list))
        except:
            path_list_x_y_dir = list(map(lambda a: (a[0], a[1]) if len(a) == 2 else (a[0], a[1], 'red'), list(chain.from_iterable(self.path_list))))

        if custom_path_list is None:
            return pattern, path_list_x_y_dir, self.str_list
        else:
            return pattern, path_list_x_y_dir, None
    
    def print_board(self):
        print("\n")
        for y in range(self.pattern.__len__()):
            for x in range(self.pattern[0].__len__()):
                if self.pattern[y][x] != 0:
                    print((x,y), end="\t")
                else:
                    print(self.pattern[y][x], end="\t")
            print()

    def create_pattern(self):
        util.path_resolver()
        while util.path_list.__len__() == 0:
            util.path_resolver()
        pattern, path, str_list = util.pattern_mapper()
        # util.print_board()
        data = {
            "program" : "\n".join(str_list),
            "path_list" : path,
            "pattern" : pattern,
            "start_coord" : [self.robot_start_coord[0], self.robot_start_coord[1], self.start_dir],
            "level":self.level
        }
        # print(data)
        return data

util = PatternGen(1) #  <- SET THE LEVEL HERE (ALLOWED levels 1, 2, 3)

try:
    document['get-pattern'].remove()
except:
    pass

document.body.appendChild(html.SCRIPT(src="https://plant-bot-bucket.s3.ap-south-1.amazonaws.com/plant_bot_patterns.js", id = 'get-pattern'))

def make_game_body(canv_width = 500, canv_height = 500):
    clientWidth = document.documentElement.clientWidth
    try:
        document['container'].remove()
    except:
        print("Error")
    
    # adding buttons
    information = """\
Note:
    Write "fwd()" to move forward in the direction where head of pointer is pointing.
    Write "r_cw()" to rotate on place in clockwise direction.
    Write "r_ccw()" to rotate on place in counter clockwise direction.<br>
    Write "plant()" to plant on the box to make it green and get a point.<br>
    
    1. click on run button to create a new game.
    2. click start button to start the animation after writing down code
       in sub editor.
    3. click stop to stop the animation any time.
    4. click reset button to go to starting conditions.
    
    In case of any error, Reload the URL "ctrl+l then enter"....
    """
    print(information)
    
    # game_div (column)
    #   - game_menu (row)
    #       - game_button 1
    #       - game_button 2..
    #   - game_playground (row)
    #       - game_editor
    #       - game_screen
    game_div = html.DIV(id='container', style={
        'display':'flex',
        'flex-direction' : 'column',
        'margin-top' : "3%",
        'justify-content' : 'flex-start',
        'align-items' : 'flex-start',
        'width' : "100%"
    })

    game_menu = html.DIV(id='title_row', style={
        'display':'flex',
        'flex-direction' : 'row',
        'justify-content' : 'flex-start',
        'width' : "50%",
        'gap' : "20px",
        "margin-bottom" : "1%",
        'align-items' : 'center'
    })
    
    button_style = {
        "width" : "20%",
        "height" : "40px"
    }

    start_button = html.BUTTON("Start", id = "start_interval", style = button_style)
    stop_button = html.BUTTON("Stop",id = "stop_interval", style = button_style)
    # new_game_button = html.BUTTON("New game", id = "new_game")
    reset_button = html.BUTTON("Reset", id = "game_reset", style = button_style)
    score_meter = html.DIV("Total Score: ", style = {'font-size':'20px', "float":"left"})
    score_meter <= html.SPAN("0", id = "score_number")

    # game_menu.appendChild(new_game_button)
    game_menu.appendChild(start_button)
    game_menu.appendChild(stop_button)
    game_menu.appendChild(reset_button)
    # game_menu.appendChild(show_info_button)
    game_menu.appendChild(score_meter)
    
    
    game_playground = html.DIV(id='editor_row', style={
        'display':'flex',
        'flex-direction' : 'row',
        'justify-content': 'space-between',
        'align-items' : 'center',
        'width' : "100%",
        'height' : "100%"
    })
    
    # adding a sub-editor for bry-bot game
    sub_editor_div = html.DIV(id = "bry-bot-editor", style={
        "width" : "100%",
        "height" : "100%"
    })
    sub_editor_div <= html.TEXTAREA(id = "sub-text-area", style = {
        'width':"100%", 
        "height":"100%", 
        'font-size':"20px"
        
    })
    game_playground <= sub_editor_div
    
    # adding a main div in which a canvas reside
    main_div = html.DIV(id="main_div")
    main_canvas = html.CANVAS(id = "main_canvas", width = f"{canv_width}px", height = f"{canv_height}px", style = {
        'border':"1px solid #000000"
        
    })
    main_div <= main_canvas

    game_playground <= main_div
    
    game_div.appendChild(game_menu)
    game_div.appendChild(game_playground)
    document.body.style.display = "block"
    document.body.appendChild(game_div)

    # info_style = {
    #     "position": "absolute",
    #     "width" : "510px",
    #     "height": "700px",
    #     "top": str(int(document['container'].style.height[:-2])+100)+"px",
    #     "left": "1200px",
    #     "z-index": "3",
    #     "font-size" : "18px",
    #     "display" : "none"
    # }
    # info = html.P(information, id = "game_info", style = info_style)
    # document.body.appendChild(info)

def get_level_data():
    def read_level_and_pattern():
        level_selected = win.prompt("Choose between level 1, 2 and 3", "Enter level number")
        try:
            return random.choice(win.patternObject9689[f'level_{level_selected.strip()}'])
        except:
            raise Exception("Pattern file loading error, Try to 'Run' the program again.")
    
    # level n -> (10*(2**3))/2
    # data = read_level_and_pattern()
    data = util.create_pattern()
    pattern = data['pattern']
    path_list = data['path_list']
    start_coord = data['start_coord']
    program = data['program']
    if SHOW_PROGRAM:
        print(program)
    LEVEL = data['level']
    
    PATH_LEN = (10*(2**LEVEL))/2
    DIREC_MAP = {1:"east", 2:"west", 3:"north", 4:"south"}
    
    if LEVEL in [1, 2]:
        make_game_body(canv_width = 500, canv_height = 500)
    elif LEVEL in [3, 4]:
        make_game_body(canv_width = 800, canv_height = 800)
    elif LEVEL in [5, 6]:
        make_game_body(canv_width = 1200, canv_height = 1200)

    CTX = document.getElementById('main_canvas').getContext("2d")
    GROUND_PARAS = {
        "start_x" : 0,
        "start_y" : 0,
        "ground_w" : LEVEL*10,
        "ground_h" : LEVEL*10,
        "stage_w" : document['main_canvas'].width/(LEVEL*10),
        "stage_h" : document['main_canvas'].height/(LEVEL*10),
        "gap" : 0
    }
    return LEVEL, DIREC_MAP, PATH_LEN, CTX, GROUND_PARAS, pattern, path_list, start_coord


class Utilities:
    def __init__(self, level, path_len, ground_paras):
        self.ground_paras = ground_paras
        self.path_len = path_len
        self.score = None
        self.robot_start_coord = None
        self.planted_boxes = []
        self.red_box_count = None
        self.path_list = []
        self.level = level

    def sleep(self, ms):
        time = win.Date.new().getTime()
        start_time = time+ms
        while time <= start_time:
            time = win.Date.new().getTime()

    def local_storage(self, function = 'set', key_name = "none", data = None):
        if isinstance(key_name, str):
            match function:
                case "set":
                    storage[key_name] = json.dumps({"data":data})
                    return f"{key_name} setted"
                case "get":
                    return json.loads(storage[key_name])['data']
                case "delete":
                    del storage[key_name]
                    return f"{key_name} deleted"
                case "contains":
                    return storage.__contains__(key_name)
        else:
            try:
                local_storage(function, str(key_name), data)
            except:
                raise "Key name should be a string"
    
    def get_int_coord(self, coord_str):
        return list(map(int, coord_str.split(",")))

    def get_str_coord(self, coord_int):
        return ",".join([str(coord_int[0]), str(coord_int[1])])
    
    def get_next_random_possible_coord(self, coord_int, ground_w, ground_h):
        south_coord = self.get_str_coord( [coord_int[0], (coord_int[1]+1 if (coord_int[1]+1)<ground_h else "nan")] )
        north_coord = self.get_str_coord( [coord_int[0], (coord_int[1]-1 if (coord_int[1]-1)>=0 else "nan")] )
        east_coord = self.get_str_coord( [(coord_int[0]+1 if (coord_int[0]+1)<ground_w else "nan"), coord_int[1]] )
        west_coord = self.get_str_coord( [(coord_int[0]-1 if (coord_int[0]-1)>=0 else "nan"), coord_int[1]] )
        tmp_list = []
        for coord in [east_coord, west_coord, north_coord, south_coord]:
            if not "nan" in coord:
                tmp_list.append(self.get_int_coord(coord))
        return random.choice(tmp_list), tmp_list
        
    def pattern_mapper(self, path_list):
        ground_w = self.ground_paras['ground_w']
        ground_h = self.ground_paras['ground_h']
        pattern = []
        for y in range(ground_h):
            tmp_pat = []
            for x in range(ground_w):
                if [x, y, 'red'] in path_list:
                    tmp_pat.append(2)
                elif [x, y] in path_list:
                    tmp_pat.append(1)
                else:
                    tmp_pat.append(0)
            pattern.append(tmp_pat)
        return pattern
    
    def get_random_coord(self):
        ground_w = self.ground_paras['ground_w']
        ground_h = self.ground_paras['ground_h']
        boundry_coords = []
        all_coords = []
        for y in range(ground_h):
            for x in range(ground_w):
                if x == 0 or y == 0 or y == (ground_h-1) or x == (ground_w-1):
                    boundry_coords.append(",".join([str(x), str(y)]))
                all_coords.append(",".join([str(x), str(y)]))
        random_start_coord = random.choice(boundry_coords)
        return self.get_int_coord(random_start_coord)

    def path_solution(self, initial_point = [0, 5], initial_direc = 1):
        ground_w = self.ground_paras['ground_w']
        ground_h = self.ground_paras['ground_h']
        command_options = ['fwd()', 'r_cw()', 'r_ccw()', 'plant()']

        def next_direc(current_dir = None, rotation_type = "cw"):
            if rotation_type == "cw":
                sequence = "1423"
            elif rotation_type == "ccw":
                sequence = "1324"
            index = sequence.index(str(current_dir))
            new_index = index + 1
            if new_index == 4:
                new_index = 0
            return int(sequence[new_index])

        def get_random_alphabet():
            return random.choice(string.ascii_lowercase)

        def check_bad_commands(loop):
            new_str = loop.split(":")[1].replace("\n", "").replace("\t", "")
            if "r_cw()r_ccw()" in new_str or "r_ccw()r_cw()" in new_str or "r_cw()r_cw()" in new_str or "r_ccw()r_ccw()" in new_str:
                return False
            return True

        def get_solution_program():
            no_of_for_loops = random.randint(self.level+1, self.level+2)
            starting_command = random.choice(command_options)
            sub_cmd_options = ["fwd()", "fwd()", "fwd()", "fwd()", 'r_cw()', 'r_ccw()']
            for_loop_block = []
            alphabet_used = []
            i = 0
            while i <= no_of_for_loops:
                no_of_commands = random.randint(2, 5)
                random_alpha = get_random_alphabet()
                while(random_alpha in alphabet_used):
                    random_alpha = get_random_alphabet()
                loop = "for {0} in range({1}):\n".format(random_alpha, no_of_commands)
                for y in range(no_of_commands):
                    random_cmd = random.choice(sub_cmd_options)
                    loop += "\t" + random_cmd + "\n"
                loop += "\tplant()"
                if check_bad_commands(loop):
                    for_loop_block.append(loop)
                    i += 1
            return starting_command + "\n" + "\n".join(for_loop_block)

        def linearity_checker(path_list):
            str_path_list = list(map(lambda a: ",".join(list(map(str, a))), path_list))
            set_of_path_list = set(str_path_list)
            blue_path_list = list(map(lambda a: a[:-1] if "red" in a else a, path_list))
            set_blue_path_list = set(list(map(lambda a: ",".join(list(map(str, a))), blue_path_list)))
            if str_path_list.__len__() == set_of_path_list.__len__() and blue_path_list.__len__() == set_blue_path_list.__len__():
                return True
            return False

        def get_coords_acc_to_solution(initial_point = [5, 5], initial_direc = 1):
            DIREC_MAP = {1:"east", 2:"west", 3:"north", 4:"south"}
            cmd_points = [initial_point]
            current_dir = initial_direc
            program_dependency_str = """\
def next_direc(current_dir = None, rotation_type = "cw"):
    if rotation_type == "cw":
        sequence = "1423"
    elif rotation_type == "ccw":
        sequence = "1324"
    index = sequence.index(str(current_dir))
    new_index = index+1
    if new_index == 4:
        new_index = 0
    return int(sequence[new_index])

def fwd():
    global current_dir
    last_point = cmd_points[-1]
    if current_dir == 1:
        x = last_point[0] + 1
        y = last_point[1]
        cmd_points.append([x, y])
    elif current_dir == 2:
        x = last_point[0] - 1
        y = last_point[1]
        cmd_points.append([x, y])
    elif current_dir == 3:
        x = last_point[0]
        y = last_point[1] - 1
        cmd_points.append([x, y])
    elif current_dir == 4:
        x = last_point[0]
        y = last_point[1] + 1
        cmd_points.append([x, y])
    
def r_cw():
    global current_dir
    current_dir = next_direc(current_dir = current_dir, rotation_type = "cw")

def r_ccw():
    global current_dir
    current_dir = next_direc(current_dir = current_dir, rotation_type = "ccw")

def plant():
    cmd_points[-1].append("red")\n\n"""

            program = get_solution_program()
            exec(program_dependency_str+program)
            sorted_cmd_list_x = sorted(cmd_points, key = lambda a: a[0], reverse = True)
            sorted_cmd_list_y = sorted(cmd_points, key = lambda a: a[1], reverse = True)

            if linearity_checker(cmd_points) and sorted_cmd_list_x[0][0] < ground_w and sorted_cmd_list_x[-1][0] >= 0 and sorted_cmd_list_y[0][1] < ground_h and sorted_cmd_list_y[-1][1] >= 0:
                self.path_list = cmd_points
                return cmd_points, True, program
            return cmd_points, False

        return get_coords_acc_to_solution(initial_point = initial_point, initial_direc = initial_direc)

    def verify_game_moves(self, current_gx = None, current_gy = None, path_list = None):
        red_box_coord = list(filter(lambda a: 'red' in a, path_list))
        red_box_only_coord = list(map(lambda a: [a[0], a[1]], red_box_coord))
        
        if [current_gx, current_gy] in red_box_only_coord and not [current_gx, current_gy] in self.planted_boxes:
            document.getElementById('score_number').innerHTML = int(str(document.getElementById('score_number').innerHTML).strip())+1
            self.planted_boxes.append([current_gx, current_gy])
            return True
        else:
            document.getElementById('score_number').innerHTML = int(str(document.getElementById('score_number').innerHTML).strip())-1
            return False
    

    
    def path_generater(self, path_length = None):
        ground_w = self.ground_paras['ground_w']
        ground_h = self.ground_paras['ground_h']
        boundry_coords = []
        all_coords = []
        for y in range(ground_h):
            for x in range(ground_w):
                if x == 0 or y == 0 or y == (ground_h-1) or x == (ground_w-1):
                    boundry_coords.append(",".join([str(x), str(y)]))
                all_coords.append(",".join([str(x), str(y)]))
        random_start_coord = random.choice(all_coords)
        self.robot_start_coord = self.get_int_coord(random_start_coord)
        self.local_storage('set', 'start_coord', self.robot_start_coord)
        random_start_dir = random.choice([1, 2, 3, 4])
        path_list = []
        path_list.append(self.robot_start_coord)
        for z in range(path_length):
            path_list.append(self.get_next_random_possible_coord(path_list[-1], ground_w, ground_h)[0])
        return self.pattern_mapper(path_list)

    def get_pattern(self):
        if self.local_storage('contains', 'pattern'):
            pattern = self.local_storage('get', 'pattern')
        else:
            pattern = self.path_generater(self.path_len)
            self.local_storage('set', 'pattern', pattern)
        return pattern


class GameObject:
    DIREC_MAP = {1:"east", 2:"west", 3:"north", 4:"south"}
    CURRENT_DIR = 1
    CURRENT_GX = 0
    CURRENT_GY = 0
    show_points_on_canvas = True
    
    def __init__(self, ctx, pattern, util, ground_paras, path_list):
        self.pattern = pattern
        self.ctx = ctx
        self.util = util
        self.ground_paras = ground_paras
        self.path_list = path_list

        self.cmd_list = []
        self.index = 0
        self._timer = None
        self.coordinate_dict = {}
        self.no_of_lines_of_code = None

        self.game_object = document['main_canvas']
        self.ctx = self.game_object.getContext("2d")
        self.start_x = ground_paras['start_x']
        self.start_y = ground_paras['start_y']
        self.stage_w = ground_paras['stage_w']
        self.stage_h = ground_paras['stage_h']
        self.ground_w = ground_paras['ground_w']
        self.ground_h = ground_paras['ground_h']

    def make_ground(self, pattern, ctx, start_x = 0, start_y = 0, ground_w = 3, ground_h = 3, stage_w = 10, stage_h = 10, gap = 1):
        coord_x = start_x
        coord_y = start_y
        for y in range(ground_h):
            for x in range(ground_w):
                ctx.fillStyle = "#6A6C69"
                if pattern[y][x] == 1:
                    ctx.fillStyle = "#87CEEB"
                elif pattern[y][x] == 2:
                    ctx.fillStyle = "#f2766d"
                elif pattern[y][x] == 3:
                    ctx.fillStyle = "#c2fa8e"
                elif pattern[y][x] == 4:
                    ctx.fillStyle = "#88ad65"
                ctx.fillRect(coord_x, coord_y, stage_w, stage_h)
                self.coordinate_dict.update({",".join([str(x), str(y)]):[coord_x, coord_y]})
                
                if self.show_points_on_canvas:
                    ctx.fillStyle = "#000000"
                    ctx.textAlign = 'center'
                    ctx.textBaseline = "middle"
                    ctx.font = "{0}px serif".format(round((stage_w-2)/3))
                    ctx.fillText(f"({x},{y})", coord_x + (stage_w*(50/100)),coord_y+(stage_w*(50/100)))
                coord_x += stage_w + gap
            coord_x = start_x
            coord_y += stage_h + gap
    
    def get_command_list(self):
        def fwd():
            self.cmd_list.append(self.forward)
        def r_cw():
            self.cmd_list.append(self.rotate_clockwise)
        def r_ccw():
            self.cmd_list.append(self.rotate_anti_clockwise)
        def plant():
            self.cmd_list.append(self.plant)
        
        game_script = document.getElementById("sub-text-area").value
        self.no_of_lines_of_code = game_script.split("\n").__len__()
        #print("locals():", locals(), "| globals():", globals())
        #exec("print(dir())", locals(), locals())
        exec(game_script, locals(), locals())
    
    def animate_ground(self):
        # print("animation_index:", self.index)
        self.make_ground(self.pattern, self.ctx, **self.ground_paras)
        if self.index >= self.cmd_list.__len__():
            self.index = 0
            end_coord = [self.CURRENT_GX, self.CURRENT_GY, self.DIREC_MAP[self.CURRENT_DIR]]
            stop_interval(end_coord = end_coord)
        else:
            eval('self.cmd_list[self.index]()')
            self.index += 1
    
    def arrow_location(self, start_x, start_y, direction = "east"):
        self.head_vertex_x = start_x + self.stage_w*(90/100)
        self.head_vertex_y = start_y + self.stage_h*(50/100)
        self.tail_vertex_one_x = self.head_vertex_x - self.stage_w*(80/100)
        self.tail_vertex_one_y = self.head_vertex_y - self.stage_h*(20/100)
        self.tail_vertex_two_x = self.tail_vertex_one_x
        self.tail_vertex_two_y = self.head_vertex_y + self.stage_h*(20/100)
        self.arrow_object(self.head_vertex_x, self.head_vertex_y, direction = direction)

    def robot(self, hx, hy, t1x, t1y, t2x, t2y):
        robot = win.Path2D.new()
        robot.moveTo(hx, hy)
        robot.lineTo(t1x, t1y)
        robot.lineTo(t2x, t2y)
        return robot

    def arrow_object(self, head_vertex_x = None, head_vertex_y = None, direction = "east"):
        down_head_x = head_vertex_x - self.stage_w*(40/100)
        down_head_y = self.tail_vertex_two_y + self.stage_h*(20/100)
        tail_two_x = self.tail_vertex_one_x + self.stage_w*(20/100)
        tail_two_y = self.tail_vertex_one_y - self.stage_h*(20/100)
        tail_one_x = self.tail_vertex_one_x + self.stage_w*(60/100)
        tail_one_y = self.tail_vertex_one_y - self.stage_h*(20/100)
        self.ctx.beginPath()
        match direction:
            case 'east':
                self.CURRENT_DIR = 1
                self.ctx.fillStyle = "#000000"
                self.ctx.fill(self.robot(head_vertex_x, head_vertex_y, \
                self.tail_vertex_one_x, self.tail_vertex_one_y, \
                self.tail_vertex_two_x, self.tail_vertex_two_y))
            case 'west':
                self.CURRENT_DIR = 2
                self.ctx.fillStyle = "#000000"
                self.ctx.fill(self.robot(self.tail_vertex_one_x, head_vertex_y,\
                head_vertex_x, self.tail_vertex_one_y, \
                head_vertex_x, self.tail_vertex_two_y))
            case 'north':
                self.CURRENT_DIR = 3
                self.ctx.fillStyle = "#000000"
                self.ctx.fill(self.robot(down_head_x, tail_two_y,\
                tail_two_x, down_head_y,\
                tail_one_x, down_head_y))
            case 'south':
                self.CURRENT_DIR = 4
                self.ctx.fillStyle = "#000000"
                self.ctx.fill(self.robot(down_head_x, down_head_y,\
                tail_one_x, tail_one_y,\
                tail_two_x, tail_two_y))

    def move_to(self, g_x = 0, g_y = 0, direction = "east"):
        if g_x < 0 or g_x >= self.ground_w:
            g_x = g_x+1 if g_x < 0 else g_x-1
        if g_y < 0 or g_y >= self.ground_h:
            g_y = g_y+1 if g_y < 0 else g_y-1
        x, y = self.coordinate_dict[",".join([str(g_x), str(g_y)])]
        self.arrow_location(x, y, direction = direction)
        self.CURRENT_GX = g_x
        self.CURRENT_GY = g_y
        
        # if int(document.getElementById('score_number').innerHTML) > list(filter(lambda a: 'red' in a, util.path_list)).__len__():
        #     win.alert("Fantastic, you have completed this level.")

    def next_direc(self, current_dir = None, rotation_type = "cw"):
        if rotation_type == "cw":
            sequence = "1423"
        elif rotation_type == "ccw":
            sequence = "1324"
        index = sequence.index(str(current_dir))
        new_index = index+1
        if new_index == 4:
            new_index = 0
        return int(sequence[new_index])
    
    def forward(self):
        if self.CURRENT_DIR == 1:
            self.move_to(self.CURRENT_GX+1, self.CURRENT_GY, direction = "east")
        elif self.CURRENT_DIR == 2:
            self.move_to(self.CURRENT_GX-1, self.CURRENT_GY, direction = "west")
        elif self.CURRENT_DIR == 3:
            self.move_to(self.CURRENT_GX, self.CURRENT_GY-1, direction = "north")
        elif self.CURRENT_DIR == 4:
            self.move_to(self.CURRENT_GX, self.CURRENT_GY+1, direction = "south")
    
    def rotate_clockwise(self):
        self.CURRENT_DIR = self.next_direc(current_dir = self.CURRENT_DIR, rotation_type = "cw")
        self.move_to(self.CURRENT_GX, self.CURRENT_GY, direction = self.DIREC_MAP[self.CURRENT_DIR])
    
    def rotate_anti_clockwise(self):
        self.CURRENT_DIR = self.next_direc(current_dir = self.CURRENT_DIR, rotation_type = "ccw")
        self.move_to(self.CURRENT_GX, self.CURRENT_GY, direction = self.DIREC_MAP[self.CURRENT_DIR])
    
    def plant(self):
        if self.util.verify_game_moves(self.CURRENT_GX, self.CURRENT_GY, self.path_list):
            self.pattern[self.CURRENT_GY][self.CURRENT_GX] = 3
        else:
            self.pattern[self.CURRENT_GY][self.CURRENT_GX] = 4
            
            


level, direc_map, path_len, ctx, ground_paras, pattern, path_list, start_coord = get_level_data()
reset_pattern = copy.deepcopy(pattern)
util = Utilities(level, path_len, ground_paras)
util.robot_start_coord = start_coord
my_robot = GameObject(ctx, pattern, util, ground_paras, path_list)


def reset(end_coord = None):
    # print("Reset Hit with pattern", pattern, " and ground_paras ", ground_paras, " and ctx ", ctx, " and start_coord ", start_coord, " and end_coord ", end_coord)
    my_robot.make_ground(pattern, ctx, **ground_paras)
    if end_coord:
        my_robot.move_to(end_coord[0], end_coord[1], direction = end_coord[2])
    else:
        my_robot.move_to(start_coord[0], start_coord[1], direction = start_coord[2])

reset()


@bind("#start_interval", 'click')
def start_interval(event = None):
    my_robot.cmd_list = []
    my_robot.get_command_list()
    my_robot._timer = timer.set_interval(my_robot.animate_ground, 500)
    document['start_interval'].style.display = "none"

@bind("#stop_interval", 'click')
def stop_interval(event = None, end_coord = None):
    timer.clear_interval(my_robot._timer)
    if end_coord:
        reset(end_coord)
    else:
        reset()

# @bind("#new_game", 'click')
# def new_game(event = None):
#     print("new game")
#     # util.local_storage('delete', 'pattern')
#     # util.local_storage('delete', 'start_coord')
#     # util.local_storage('delete', 'path_list')
#     # util.local_storage('delete', 'program')


@bind("#game_reset", 'click')
def game_reset(event = None):
    global pattern
    pattern = copy.deepcopy(reset_pattern)

    my_robot.pattern = pattern
    my_robot.ctx = ctx
    my_robot.util = util
    my_robot.ground_paras = ground_paras
    
    my_robot.cmd_list = []
    my_robot.index = 0
    # my_robot._timer = None
    # my_robot.coordinate_dict = {}
    # my_robot.no_of_lines_of_code = None
    # my_robot.game_object = document['main_canvas']
    # my_robot.ctx = my_robot.game_object.getContext("2d")
    # my_robot.start_x = ground_paras['start_x']
    # my_robot.start_y = ground_paras['start_y']
    # my_robot.stage_w = ground_paras['stage_w']
    # my_robot.stage_h = ground_paras['stage_h']
    # my_robot.ground_w = ground_paras['ground_w']
    # my_robot.ground_h = ground_paras['ground_h']
    
    util.ground_paras = ground_paras
    util.path_len = path_len
    util.score = None
    util.robot_start_coord = start_coord
    util.planted_boxes = []
    document['score_number'].innerHTML = int(0)
    document['start_interval'].style.display = "inline"
    reset()




# if not util.local_storage('contains', 'pattern'):
#     while True:
#         random_dir = random.choice([1, 2, 3, 4])
#         path_list, satisfied, program = util.path_solution(initial_point = util.get_random_coord(), initial_direc = random_dir)
#         if satisfied:
#             pattern = util.pattern_mapper(path_list)
#             util.local_storage('set', 'path_list', path_list)
#             util.local_storage('set', 'pattern', pattern)
#             util.local_storage('set', 'program', program)
#             util.robot_start_coord = [path_list[0][0], path_list[0][1], direc_map[random_dir]]
#             print("$"*50)
#             print("start_coord:", util.robot_start_coord)
#             print("$"*50)
#             util.local_storage('set', 'start_coord', util.robot_start_coord)
#             break
#         print("Generating and analyzing good patterns....")
# else:
#     pattern = util.local_storage('get', 'pattern')
#     path_list = util.local_storage('get', 'path_list')
#     program = util.local_storage('get', 'program')

# game_data = {
#     "pattern" : [[0, 0, 0, 0, 0, 0, 0, 0, 2, 2], [1, 1, 1, 2, 1, 1, 2, 1, 1, 2], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
#     "path_list" : [[0, 1], [1, 1], [2, 1], [3, 1, 'red'], [4, 1], [5, 1], [6, 1, 'red'], [7, 1], [8, 1], [9, 1, 'red'], [9, 0, 'red'], [8, 0, 'red']],
#     "start_coord" : [0, 1, 'east'],
#     "program" : 'r_cw()\nfor p in range(3):\n\tfwd()\n\tfwd()\n\tfwd()\n\tplant()\nfor c in range(2):\n\tr_ccw()\n\tfwd()\n\tplant()',
#     "level" : 1
# }

# game_data = {'program': 'plant()\nfor f in range(3):\n\tfwd()\n\tfwd()\n\tr_cw()\n\tplant()\nfor u in range(3):\n\tr_ccw()\n\tfwd()\n\tfwd()\n\tplant()\nfor p in range(2):\n\tfwd()\n\tfwd()\n\tplant()', 'path_list': [[3, 0, 'red'], [4, 0], [5, 0, 'red'], [5, 1], [5, 2, 'red'], [4, 2], [3, 2, 'red'], [2, 2], [1, 2, 'red'], [1, 3], [1, 4, 'red'], [2, 4], [3, 4, 'red'], [4, 4], [5, 4, 'red'], [6, 4], [7, 4, 'red']], 'pattern': [[0, 0, 0, 2, 1, 2, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0], [0, 2, 1, 2, 1, 2, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 2, 1, 2, 1, 2, 1, 2, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], 'start_coord': [3, 0, 'east'], 'level': 1}
# game_data = {'program': 'r_cw()\nfor v in range(2):\n\tr_ccw()\n\tfwd()\n\tplant()\nfor k in range(2):\n\tr_cw()\n\tfwd()\n\tplant()\nfor v in range(2):\n\tfwd()\n\tfwd()\n\tplant()', 'path_list': [[8, 0], [8, 1, 'red'], [9, 1, 'red'], [9, 2, 'red'], [8, 2, 'red'], [7, 2], [6, 2, 'red'], [5, 2], [4, 2, 'red']], 'pattern': [[0, 0, 0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 0, 0, 2, 2], [0, 0, 0, 0, 2, 1, 2, 1, 2, 2], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], 'start_coord': [8, 0, 'south'], 'level': 1}
# game_data = {'program': 'plant()\nfor n in range(2):\n\tfwd()\n\tfwd()\n\tplant()\nfor c in range(2):\n\tfwd()\n\tfwd()\n\tplant()\nfor o in range(2):\n\tr_cw()\n\tfwd()\n\tplant()', 'path_list': [[0, 7, 'red'], [1, 7], [2, 7, 'red'], [3, 7], [4, 7, 'red'], [5, 7], [6, 7, 'red'], [7, 7], [8, 7, 'red'], [8, 8, 'red'], [7, 8, 'red']], 'pattern': [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [2, 1, 2, 1, 2, 1, 2, 1, 2, 0], [0, 0, 0, 0, 0, 0, 0, 2, 2, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]], 'start_coord': [0, 7, 'east'], 'level': 1}
# pattern = game_data['pattern']
# path_list = game_data['path_list']
# start_coord = game_data['start_coord']
# level = game_data['level']