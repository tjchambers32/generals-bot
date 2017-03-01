'''
	@ Travis Chambers
	March 2016
	Generals.io Automated Client - https://github.com/tjchambers32/generals-bot
	Path Collect Bot: Collects troops along a path, and attacks outward using path.
'''

import logging
import random

from base import bot_base

# Show all logging
logging.basicConfig(level=logging.DEBUG)

######################### Move Making #########################

_bot = None
_map = None
def make_move(currentBot, currentMap):
	global _bot, _map
	_bot = currentBot
	_map = currentMap

	# Path Updates
	find_collect_path()

	# Make Move
	if (_map.turn % 10 == 0):
		if not move_collect_to_path():
			if not make_primary_move():
				move_outward()
	elif (_map.turn % 2 == 0):
		if not make_primary_move():
			if not move_outward():
				move_collect_to_path()
	else:
		if not move_outward():
			if not move_collect_to_path():
				make_primary_move()
	return

def place_move(source, dest):
	moveHalf = False
	if (_map.turn > 150 and (source in _map.generals or source in _map.cities)):
		moveHalf = random.choice([False, False, False, True])
		if (_map.turn - source.turn_captured) < 8:
			moveHalf = True
	
	_bot.place_move(source, dest, move_half=moveHalf)

######################### Primary Move Making #########################

def make_primary_move():
		update_primary_target()
		if (len(_path) > 1):
			return move_primary_path_forward()
		elif (_target != None):
			new_primary_path()
		return False

######################### Primary Targeting #########################

_target = None
_path = []
_path_position = 0
def update_primary_target():
	global _target, _path, _path_position
	if (_target != None):
		_target = _map.grid[_target.y][_target.x] # Update Target Tile State
	newTarget = _bot.find_primary_target(_target)
	if _target != newTarget:
		_target = newTarget
		new_primary_path(restoreOldPosition=True)

######################### Primary Path #########################

def move_primary_path_forward():
	global _path_position
	try:
		source = _path[_path_position]
	except IndexError:
		#logging.debug("Invalid Current Path Position")
		return new_primary_path()

	if (source.tile != _map.player_index or source.army < 2): # Out of Army, Restart Path
		#logging.debug("Path Error: Out of Army (%d,%d)" % (source.tile, source.army))
		return new_primary_path()

	try:
		dest = _path[_path_position+1] # Determine Destination
		if (dest.tile == _map.player_index or source.army > (dest.army+1)):
			place_move(source, dest)
		else:
			#logging.debug("Path Error: Out of Army To Attack (%d,%d,%d,%d)" % (dest.x,dest.y,source.army,dest.army))
			return new_primary_path()
	except IndexError:
		#logging.debug("Path Error: Target Destination Out Of List Bounds")
		return new_primary_path(restoreOldPosition=True)

	_path_position += 1
	return True

def new_primary_path(restoreOldPosition=False):
	global _bot, _path, _path_position, _target

	# Store Old Tile
	old_tile = None
	if (_path_position > 0 and len(_path) > 0): # Store old path position
		old_tile = _path[_path_position]
	_path_position = 0
	
	# Determine Source and Path
	source = _bot.find_city()
	_path = _bot.find_path(source=source, dest=_target) # Find new path to target
	_bot._path = _path

	# Restore Old Tile
	if (restoreOldPosition and old_tile != None):
		for i, tile in enumerate(_path):
			if (tile.x, tile.y) == (old_tile.x, old_tile.y):
				_path_position = i
				return True
	
	return False

######################### Move Outward #########################

def move_outward():
	for x in bot_base._shuffle(range(_map.cols)): # Check Each Square
		for y in bot_base._shuffle(range(_map.rows)):
			source = _map.grid[y][x]

			if (source.tile == _map.player_index and source.army >= 2 and source not in _path): # Find One With Armies
				for dy, dx in _bot.toward_dest_moves(source, dest=_target):
					if (_bot.validPosition(x+dx,y+dy)):
						dest = _map.grid[y+dy][x+dx]
						if ((dest.tile != _map.player_index and source.army > (dest.army+1)) or dest in _path): # Capture Somewhere New
							place_move(source, dest)
							return True
	return False

######################### Collect To Path #########################

_collect_path = []
def find_collect_path():
	global _collect_path

	# Find Largest Tile
	source = _bot.find_largest_tile(notInPath=_path, includeGeneral=0.33)
	if (source == None or source.army < 4):
		_collect_path = []
		_bot._collect_path = []
		return False

	# Determine Target Tile
	dest = None
	if (source.army > 40):
		#dest = _bot.find_city(notOfType=_map.player_index, findLargest=False)
		dest = _bot.find_closest_target(source)
	if (dest == None):
		dest = _bot.find_closest_in_path(source, _path)

	# Determine Path
	_collect_path = _bot.find_path(source=source, dest=dest)
	_bot._collect_path = _collect_path

def move_collect_to_path():
	global _collect_path

	try:
		source = _collect_path[0]
		dest = _collect_path[1]
	except IndexError:
		return False

	if (source.tile == _map.player_index and (dest.tile == _map.player_index or source.army > dest.army+1)):
		place_move(source,dest)
		return True

	return False

######################### Main #########################

# Start Game
bot_base.GeneralsBot(make_move, name="PurdueBot-P", gameType="private", privateRoomID="PurdueBot") # Private Game - http://generals.io/games/HyI4d3_rl
#bot_base.GeneralsBot(make_move, name="PurdueBot-P", gameType="1v1")
#bot_base.GeneralsBot(make_move, name="PurdueBot-P", gameType="ffa")
