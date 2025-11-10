#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 et

# Stardew Valley Player Swap
# Copyright © 2021 A. Karl Kornel
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <https://www.gnu.org/licenses/>.


import argparse
import logging
import os
import pathlib
import sys
from typing import *
#import xml.etree.ElementTree as ElementTree
from lxml import etree as ElementTree

# LOGGING

# Create the logger, set STDERR logging, and set log level
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
if 'LOG_LEVEL' in os.environ:
    logger.setLevel(os.environ['LOG_LEVEL'])

# Map logger functions to the global namespace
debug = logger.debug
warning = logger.warning
error = logger.error
exception = logger.exception

# CHECK INPUT

# Get the input filename
debug('Parsing arguments')
argp = argparse.ArgumentParser(
    description='Swap a Stardew Valley player and Farmhand',
)
argp.add_argument('save_path',
    help='The Stardew Valley save directory',
    type=str,
)
argp.add_argument('--xml_format',
    help='Generate formatted (human-readable) XML',
    action='store_true',
)
args = argp.parse_args()

# Check if we have a directory 
debug(f"Using save path {args.save_path}")
save_dir = pathlib.Path(args.save_path)
if not save_dir.exists():
    error(f"{save_dir} does not exist")
    sys.exit(1)
if not save_dir.is_dir():
    error(f"{save_dir} is not a directory")
    sys.exit(1)

# Fully resolve the path
save_dir = save_dir.resolve()
debug(f"Using save directory name {save_dir.name}")

# Our directory should have a file whose name is the same as the save
# directory.  We should also have a "SaveGameInfo" file.
found_savegameinfo = False
save_file: Union[pathlib.Path, None] = None
for f in save_dir.iterdir():
    debug(f"Checking file {f.name}")
    if f.name == 'SaveGameInfo' and f.is_file() is True:
        debug('Found SaveGameInfo file')

        found_savegameinfo = True
    elif f.name == save_dir.name and f.is_file() is True:
        debug('Found save file')
        save_file = f
if not found_savegameinfo:
    error("Your directory does not look like a Stardew Valley save.  It should have a 'SaveGameInfo' file.")
    sys.exit(2)
if save_file is None:
    error(f"Your directory does not look like a Stardew Valley save.  It should have a '{save_dir.name}' file.")
    sys.exit(2)

# We found our save!
debug(f"Using save file {save_file}")

# READ XML

# Register namespaces
ElementTree.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
ElementTree.register_namespace('xsd', 'http://www.w3.org/2001/XMLSchema')

# Make a support function to find a child element
def xml_find_one_child(
    element: ElementTree._Element,
    name: str,
    attrib: Optional[Tuple[str, str]] = None,
) -> ElementTree._Element:
    if attrib is None:
        debug(f"Searching for <{name}> in <{element.tag}>")
    else:
        debug(f"Searching for <{name} {attrib[0]}={attrib[1]}> in <{element.tag}>")
    match: Optional[ElementTree._Element] = None
    for child in element:
        if child.tag == name:
            # Do we have attributes to check for?
            if attrib is None:
                # Check if we already found a match.
                if match is not None:
                    raise KeyError(f"Found multiple <{name}> in the {element.tag}")
                else:
                    debug('No attribute check needed.  Found match!')
                    match = child
                    break
            else:
                debug('Found potential match.  Checking attributes.')
                if attrib[0] in child.attrib:
                    if child.attrib[attrib[0]] == attrib[1]:
                        # Check if we already found a match.
                        if match is not None:
                            raise KeyError(f"Found multiple <{name}> in the {element.tag}")
                        else:
                            debug('Found match with attributes!')
                            match = child
                            break
                    else:
                        debug('Found attribute, but value does not match.')
                else:
                    debug('Attribute not found.  Skipping.')
    if match is None:
        raise KeyError(f"Could not find a <{name}> in the {element.tag}")
    else:
        debug(f'Found: {match.tag} {[e.tag for e in match]}')
        return match

# Set parser configuration
xml_parser = ElementTree.XMLParser(
    remove_blank_text=True, # Cleans up human-readable XML
)

# Now, start reading!
# First, import all of the XML, and check the root.
debug('Parsing XML')
try:
    game_tree = ElementTree.parse(str(save_file), xml_parser)
except Exception as e:
    exception('Problem parsing save file XML')
    sys.exit(3)
game_root = game_tree.getroot()
if game_root.tag != 'SaveGame':
    error(f"Root XML tag is '{game_root.tag}', not SaveGame.")
    sys.exit(3)

# Look for the player tag in the XML, and pull it from the root
debug('Searching for player and cabins')
try:
    player = xml_find_one_child(game_root, 'player')
    player_name_val = xml_find_one_child(player, 'name').text
    if player_name_val is None:
        error('Player has no name!')
        sys.exit(3)
    if isinstance(player_name_val, bytes):
        player_name = player_name_val.decode('utf-8')
    else:
        player_name = player_name_val
except KeyError:
    exception('Could not find the player!')
    sys.exit(3)

# We've found the player.  Now grab an inventory of all of the cabins, and the
# players in each cabin.
# To do that, we need to look through the list of buildings.
# The path to buildings is:
# game_root -> <locations><GameLocation xsi:type="Farm"><buildings>
# <buildings> includes things like silos and the greenhouse, so we have to be
# careful.
# Each cabin is a <Building>, with an <indoors xsi:type="Cabin">

debug('Drilling down to <Buildings>')
try:
    farmhands = xml_find_one_child(game_root, 'farmhands')
except KeyError:
    exception('Could not drill down to buidings!')
    sys.exit(3)

# Look up who is in each cabin.
debug('Checking cabin occupancy')
farmhand_names: List[Union[str, None]] = list()
i = 0
while (i<len(farmhands)):
    farmhand = farmhands[i]
    try:
        farmhand_name_val = xml_find_one_child(farmhand, 'name').text
        if farmhand_name_val is None:
            error('Found a farmhand with no name!')
            sys.exit(3)
        if isinstance(farmhand_name_val, bytes):
            farmhand_names.append(farmhand_name_val.decode('utf-8'))
        else:
            farmhand_names.append(farmhand_name_val)
    except KeyError:
        farmhand_names.append(None)
    i = i + 1

# SELECT PLAYER

# Show the player and cabin occupant names
print(f"Found {len(farmhands)} farmhands!")
print(f" Player: {player_name}")
i = 0
for farmhand_name in farmhand_names:
    i = i + 1
    if farmhand_name is None:
        continue
    else:
        print(f"Farmhand {i}: {farmhand_name}")

# Ask for a cabin number
target_farmhand_i: Optional[int] = None
while target_farmhand_i is None:
    try:
        # Get the input and convert to int.
        # This can raise a KeyboardInterrupt or a ValueError.
        target_farmhand_i = int(input('Which farmhand number would you like to swap? '))

        # Check for non-positive integets.
        if target_farmhand_i <= 0:
            print('Please enter a positive number')
            target_farmhand_i = None
            continue

        # Convert the target cabin to an array index
        target_farmhand_i = target_farmhand_i - 1

        # Pull the target farmhand name and farmhand.  This can raise an IndexError.
        target_farmhand_name = farmhand_names[target_farmhand_i]
        target_farmhand = farmhands[target_farmhand_i]

        # Check if the targeted farmhand exists.
        if target_farmhand_name is None:
            print('That cabin is empty.  You must select an occupied cabin.')
            target_farmhand_i = None

        # That's all the validation!
    except KeyboardInterrupt:
        print('Exiting')
        sys.exit(0)
    except ValueError:
        print('Please enter a number.')
        target_farmhand_i = None
    except IndexError:
        print('Please enter a valid cabin number.')
        target_farmhand_i = None

# Cabin selected!
# game_root (Element) is the root element, which contains a player
# player (Element) is the current player
# player_name (str) is the name of the current player
# target_cabin (int) is the index number
# target_building (Element) is the target building (cabin)
# target_indoors (Element) is the target indoors (which has the farmhand)
# target_farmhand (Element) is the farmhand
# target_farmhand_name (str) is the name of the new player

# Display pending action
print('Swapping')
print(f"    {player_name}")
print('and')
print(f"    {target_farmhand_name}")

# Ask for final confirmation
do_continue: Optional[bool] = None
while do_continue is None:
    # Prompt
    try:
        continue_response = input('Continue [Y/N]? ')
    except KeyboardInterrupt:
        print('Exiting')
        sys.exit(0)
    continue_response = continue_response.upper()
    
    # Check if Y or N
    if continue_response == 'Y':
        do_continue = True
    elif continue_response == 'N':
        do_continue = False

# Should we continue?
if do_continue == False:
    print('Exiting')
    sys.exit(0)

# Continue!!!

# * Remove the current player (player) from the root element (game_root)
# * Remove the farmhand (target_farmhand) from the target indoors (target_indoors)
debug('Step: Remove player and farmhand')
game_root.remove(player)
farmhands.remove(target_farmhand)

# * Rename the current player (player) from "<player>" to "<farmhand>"
# * Rename the current farmhand (target_farmhand) from "<farmhand>" to "<player>"
debug('Step: Change tags')
player.tag = 'Farmer'
target_farmhand.tag = 'player'

# * Swap the text of the current player (player) <homeLocation>
#   with the text of the current farmhand (target_farmhand) <homeLocation>
debug('Step: Swap home locations')

# Get the home locations
try:
    player_homelocation = xml_find_one_child(player, 'homeLocation')
    target_farmhand_homelocation = xml_find_one_child(target_farmhand, 'homeLocation')
except KeyError:
    exception('Player or farmhand is missing a homeLocation!')
    sys.exit(3)

# Do the swap!
player_homelocation_text = player_homelocation.text
player_homelocation.text = target_farmhand_homelocation.text
target_farmhand_homelocation.text = player_homelocation_text

# * Add the old player (player) to the target indoors (target_indoors), at the end.
# * Add the new player (target_farmhand) to the root element, at the start
debug('Step: Insert back into tree')
farmhands.append(player)
game_root.insert(0, target_farmhand)

# WRITE XML

# Append ".orig" to the current file name
orig_file = save_file.with_name(save_file.name + '.orig')
save_file.rename(orig_file)

# Write out the new XML to the original path
game_tree.write(
    str(save_file),
    encoding='utf-8',
    pretty_print=args.xml_format,
)

print('All done!')
sys.exit(0)
