import bottle
import json
import os
import random
import sys

from model.point import Point
from model.snake import Snake
from model.board import Board
from controller.murgatroid_controller import MurgatroidController

EMPTY = u'empty'
FOOD = u'food'
BODY = u'body'
HEAD = u'head'
MURGATROID = u'murgatroid'


UP = u'up'
RIGHT = u'right'
DOWN = u'down'
LEFT = u'left'


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    board_width = data['width']
    board_height = data['height']

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    # TODO: Do things with data

    return {
        'color': '#00FF00',
        'taunt': '{} ({}x{})'.format(game_id, board_width, board_height),
        'head_url': head_url,
        'name': 'murgatroid'
    }


def look_ahead(head_x, head_y, board, bounds):
    directions = []
    safe_states = (EMPTY, FOOD)

    if head_x + 1 <= bounds['right'] and board[head_x+1][head_y] in safe_states:
        directions.append(RIGHT)

    if head_x - 1 >= bounds['left'] and board[head_x-1][head_y] in safe_states:
        directions.append(LEFT)

    if head_y + 1 <= bounds['down'] and board[head_x][head_y+1] in safe_states:
        directions.append(DOWN)

    if head_y - 1 >= bounds['up'] and board[head_x][head_y-1] in safe_states:
        directions.append(UP)

    return directions


def move_edge(murgatroid, bounds):
    coords = murgatroid['coords']
    head_x, head_y = coords[0][0], coords[0][1]

    # If not on an edge, start moving towards one
    if not any([head_x in (bounds['left'], bounds['right']), head_y in (bounds['up'], bounds['down'])]):
        edge_distances = [
            (UP, head_y - bounds['up']),
            (RIGHT, bounds['right'] - head_x),
            (DOWN, bounds['down'] - head_y),
            (LEFT, head_x - bounds['left'])
        ]
        dist_min = sys.maxint
        # min_index = -1

        # Find the closest edge's index
        for i, d in enumerate(edge_distances):
            if d[1] < dist_min:
                dist_min = edge_distances[i][1]
                index = i

        direction = edge_distances[index][0]

    elif head_y == bounds['up'] and bounds['left'] <= head_x <= bounds['right'] - 1:
        direction = RIGHT
    elif head_x == bounds['right'] and bounds['up'] <= head_y <= bounds['down'] - 1:
        direction = DOWN
    elif head_y == bounds['down'] and bounds['left'] + 1 <= head_x <= bounds['right']:
        direction = LEFT
    else:
        direction = UP

    return direction


def get_possible_directions(murgatroid, board, bounds):
    coords = murgatroid['coords']
    head_x, head_y = coords[0][0], coords[0][1]

    look_ahead1 = look_ahead(head_x, head_y, board, bounds)

    directions = []

    for direction in look_ahead1:
        if direction == UP:
            look_aheadUP = look_ahead(head_x, head_y-1, board, bounds)
            if len(look_aheadUP) > 0:
                directions.append((UP, board[head_x][head_y-1] == FOOD))
        elif direction == DOWN:
            look_aheadDOWN = look_ahead(head_x, head_y+1, board, bounds)
            if len(look_aheadDOWN) > 0:
                directions.append((DOWN, board[head_x][head_y+1] == FOOD))
        elif direction == LEFT:
            look_aheadLEFT = look_ahead(head_x-1, head_y, board, bounds)
            if len(look_aheadLEFT) > 0:
                directions.append((LEFT, board[head_x-1][head_y] == FOOD))
        elif direction == RIGHT:
            look_aheadRIGHT = look_ahead(head_x+1, head_y, board, bounds)
            if len(look_aheadRIGHT) > 0:
                directions.append((RIGHT, board[head_x+1][head_y] == FOOD))

    return directions


@bottle.post('/move')
def move():
    data = bottle.request.json
    board = Board.from_json(data)
    murgatroid_controller = MurgatroidController(board)

    directions_map = murgatroid_controller.get_possible_directions()
    if not directions_map:
        board.use_safe_bounds = False
        directions_map = murgatroid_controller.get_possible_directions()
        if not directions_map:
            # Commit suicide honorably so as not to give any victories to
            # the other inferior snakes!
            return json.dumps({
                'move': murgatroid_controller.seppuku(),
                'taunt': 'You will always remember this as the day you almost caught Captain Jack Sparrow!'
            })

    edge_direction = move_edge(murgatroid, bounds)

    food = [x for x, food in directions if food]

    if food:
        return json.dumps({
            'move': random.choice(food),
            'taunt': 'Sssssssssssssaucy'
        })
    else:
        directions = [x for x, _ in directions]
        return json.dumps({
            'move': edge_direction if edge_direction in directions else random.choice(directions),
            'taunt': 'MURGATROIIIIIID'
        })


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
