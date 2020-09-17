import string

from qgis.core import *
from qgis.gui import *


@qgsfunction(args='auto', group='grid_stuff')
def get_coord_row_id(depth, feature, parent, context):
    """
    Calculates row identifier for layers created with Processing's
    'native:creategrid'

    <h2>Example usage:</h2>
    <ul>
      <li>get_coord_row_id(3) -> 13</li>
    </ul>
    """
    
    row_id, col_id = _get_grid_coord_identifiers(
        feature, context.variable('layer'), depth)
    return row_id


@qgsfunction(args='auto', group='grid_stuff')
def get_coord_col_id(depth, feature, parent, context):
    row_id, col_id = _get_grid_coord_identifiers(
        feature, context.variable('layer'), depth)
    return col_id


def _get_grid_coord_identifiers(feature, layer, depth):
    num_rows, num_cols = _get_grid_params(feature, layer)
    return find_coord_ids(feature['id'], num_rows, num_cols, depth)


def _get_grid_params(feature, layer):
    layer_extent = layer.extent()
    layer_width = layer_extent.width()
    layer_height = layer_extent.height()
    cell_width = feature['right'] - feature['left']
    cell_height = feature['top'] - feature['bottom']
    num_cols = layer_width // cell_width
    num_rows = layer_height // cell_height
    return num_rows, num_cols


def get_coords(cell: int, num_rows: int, num_cols: int):
    row = ((cell - 1) % num_rows) + 1
    col = (cell - row) / num_rows + 1
    return row, int(col)


def find_levels(coord: int, depth: int, result=None):
    levels = result or []
    if depth == 1:
        levels.append(coord + 1)
        return levels
    else:
        depth_treshold = 2 ** (depth - 1)
        level = coord // depth_treshold + 1
        levels.append(level)
        new_coord = coord - depth_treshold * (level - 1)
        return find_levels(new_coord, depth - 1, levels)


def find_alphabetic_levels(coord, depth):
    levels = find_levels(coord, depth)
    result = []
    for i in levels:
        result.append(string.ascii_letters[i - 1])
    return result


def find_coord_ids(cell, num_rows, num_cols, depth):
    row, col = get_coords(cell, num_rows, num_cols)
    col_levels = find_levels(col - 1, depth)
    row_levels = find_alphabetic_levels(row - 1, depth)
    return ''.join(str(i) for i in row_levels), ''.join(str(i) for i in col_levels)
