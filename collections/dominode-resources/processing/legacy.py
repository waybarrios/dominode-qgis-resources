import typing

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterExpression,
    QgsProcessingOutputString,
)
from qgis.PyQt.QtCore import QCoreApplication


class Legacy(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Legacy()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'legacy'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Legacy')

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
            'Always returns True'
        )

    def initAlgorithm(self, config=None):
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT,
                self.tr('True value')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        return {
            self.OUTPUT: True
        }
