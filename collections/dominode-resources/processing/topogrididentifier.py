import string
import typing

from qgis import processing
from qgis.core import (
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingOutputVectorLayer,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication


class DomiNodeTopoMapGridIdentifier(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    INPUT_DEPTH = 'DEPTH'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return self.__class__()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'topogrididentifier'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Generate grid identifier columns')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('DomiNode')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs
        to.
        """
        return 'dominode'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr(
            'Enhance topo maps index grid with identifier for the coordinates'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr('Input grid layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_DEPTH,
                self.tr('Depth'),
                defaultValue=1,
                minValue=1,
                maxValue=10
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output grid layer'),
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        depth = self.parameterAsInt(parameters, self.INPUT_DEPTH, context)
        input_layer = self.parameterAsVectorLayer(
            parameters, self.INPUT, context)
        output_fields = QgsFields(input_layer.fields())
        output_fields.append(QgsField('row_id'))
        output_fields.append(QgsField('col_id'))
        sink, destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            output_fields,
            input_layer.wkbType(),
            input_layer.crs()
        )
        if sink is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.OUTPUT))

        num_features = input_layer.featureCount()
        total = 100 / num_features if num_features else 0
        for current, feature in enumerate(input_layer.getFeatures()):
            if feedback.isCanceled():
                break
            new_feature = QgsFeature(feature)
            new_feature.setFields(output_fields)
            for index, field in enumerate(input_layer.fields()):
                new_feature[index] = feature[index]
            row_id, col_id = get_grid_coord_identifiers(
                new_feature, input_layer, depth, feedback)
            new_feature.setAttribute('row_id', row_id.upper())
            new_feature.setAttribute('col_id', col_id)
            sink.addFeature(
                new_feature, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))
        return {
            self.OUTPUT: destination_id
        }


def get_grid_coord_identifiers(feature, layer, depth, feedback):
    num_rows, num_cols = get_grid_params(feature, layer, feedback)
    return find_coord_ids(feature['id'], num_rows, num_cols, depth, feedback)


def find_coord_ids(cell, num_rows, num_cols, depth, feedback):
    row, col = get_coords(cell, num_rows, num_cols)
    col_levels = find_levels(col - 1, depth, feedback)
    row_levels = find_alphabetic_levels(row - 1, depth, feedback)
    return (
        ''.join(str(i) for i in row_levels),
        ''.join(str(i) for i in col_levels)
    )


def get_grid_params(feature, layer, feedback):
    layer_extent = layer.extent()
    layer_width = layer_extent.width()
    layer_height = layer_extent.height()
    cell_width = feature['right'] - feature['left']
    cell_height = feature['top'] - feature['bottom']
    num_cols = layer_width // cell_width
    num_rows = layer_height // cell_height
    return num_rows, num_cols


def find_levels(coord: int, depth: int, feedback, result=None):
    levels = result or []
    if depth == 1:
        levels.append(int(coord + 1))
        return levels
    else:
        depth_treshold = 2 ** (depth - 1)
        level = int(coord // depth_treshold + 1)
        levels.append(level)
        new_coord = coord - depth_treshold * (level - 1)
        return find_levels(new_coord, depth - 1, feedback, levels)


def find_alphabetic_levels(coord, depth, feedback):
    levels = find_levels(coord, depth, feedback)
    # feedback.pushInfo(f'found levels: {levels}')
    result = []
    for i in levels:
        result.append(string.ascii_letters[i - 1])
    return result


def get_coords(cell: int, num_rows: int, num_cols: int):
    row = ((cell - 1) % num_rows) + 1
    col = (cell - row) / num_rows + 1
    return row, int(col)
