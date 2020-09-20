import typing

from qgis import processing
from qgis.core import (
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterExpression,
    QgsProcessingOutputString,
)
from qgis.PyQt.QtCore import QCoreApplication


class ExpressionToStringConverter(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExpressionToStringConverter()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'expressiontostringconverter'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Convert expression to string')

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
            'Convert an expression to a string so that it may be used by '
            'downstream algorithms that expect to receive input as a string'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT,
                self.tr('Expression'),
                optional=True
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT,
                self.tr('Converted string')
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        result = parse_as_expression(
            self.parameterAsExpression(parameters, self.INPUT, context))
        feedback.pushInfo(f'result: {result}')
        return {
            self.OUTPUT: result
        }


def parse_as_expression(
        raw_expression: str,
        context: typing.Optional[QgsExpressionContext] = None,
        default: typing.Optional[typing.Any] = None
):
    expression = QgsExpression(raw_expression)
    if expression.hasParserError():
        raise RuntimeError(
            f'Encountered error while parsing {raw_expression!r}: '
            f'{expression.parserErrorString()}'
        )
    if context is None:
        ctx = QgsExpressionContext()
        ctx.appendScope(QgsExpressionContextUtils.globalScope())
    else:
        ctx = context
    result = expression.evaluate(ctx)
    if expression.hasEvalError():
        raise ValueError(
            f'Encountered error while evaluating {raw_expression!r}: '
            f'{expression.evalErrorString()}'
        )
    return result if result is not None else default


