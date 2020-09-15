import typing

from qgis import processing
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterMapLayer,
    QgsProcessingParameterString,
    QgsProcessingOutputString,
)
from qgis.PyQt.QtCore import QCoreApplication


class DomiNodeResourceNameValidator(QgsProcessingAlgorithm):

    INPUT_RESOURCE_NAME = 'INPUT_NAME'
    INPUT_RESOURCE_LAYER = 'INPUT_LAYER'
    OUTPUT_DEPARTMENT_ID = 'OUTPUT_DEPARTMENT_ID'
    OUTPUT_DATASET_ID = 'OUTPUT_DATASET_ID'
    OUTPUT_COLLECTION_ID = 'OUTPUT_COLLECTION_ID'
    OUTPUT_VERSION = 'OUTPUT_VERSION'
    OUTPUT_COLLECTION_VERSION = 'OUTPUT_COLLECTION_VERSION'
    OUTPUT_DATASET_NAME = 'OUTPUT_DATASET_NAME'
    OUTPUT_DB_STAGING_SCHEMA_NAME = 'OUTPUT_DB_STAGING_SCHEMA_NAME'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DomiNodeResourceNameValidator()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'resourcenamevalidator'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Validate resource name')

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
            'Check the name of a DomiNOde resource in order to determine '
            'if it complies with the DomiNode resource conventions.'
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterString(
                self.INPUT_RESOURCE_NAME,
                self.tr('Name of DomiNode resource'),
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterMapLayer(
                self.INPUT_RESOURCE_LAYER,
                self.tr('Loaded DomiNode resource'),
                optional=True
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT_DEPARTMENT_ID,
                self.tr('Resource department')
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT_DATASET_ID,
                self.tr('Resource dataset id')
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT_COLLECTION_ID,
                self.tr('Resource collection id')
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT_VERSION,
                self.tr('Resource version')
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT_COLLECTION_VERSION,
                self.tr('Resource collection version')
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT_DATASET_NAME,
                self.tr('Dataset name')
            )
        )
        self.addOutput(
            QgsProcessingOutputString(
                self.OUTPUT_DB_STAGING_SCHEMA_NAME,
                self.tr('Department staging schema name on the DB')
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        resource = self.parameterAsLayer(
            parameters, self.INPUT_RESOURCE_LAYER, context)
        feedback.pushInfo(f'resource: {resource}')
        if resource is not None:
            resource_name = resource.name()
        else:
            resource_name = self.parameterAsString(
                parameters, self.INPUT_RESOURCE_NAME, context)
        feedback.pushInfo(f'resource_name: {resource_name}')

        parts = resource_name.split('_')
        result = {
            self.OUTPUT_VERSION: None,
            self.OUTPUT_COLLECTION_ID: None,
            self.OUTPUT_COLLECTION_VERSION: None,
            self.OUTPUT_DATASET_NAME: resource_name,
        }
        if len(parts) == 4:
            department, collection_id, dataset_id, version_suffix = parts
            collection_version, format_suffix = get_format_suffix(
                version_suffix)
            result.update({
                self.OUTPUT_COLLECTION_ID: collection_id,
                self.OUTPUT_COLLECTION_VERSION: collection_version,
            })
        elif len(parts) == 3:
            department, dataset_id, version_suffix = parts
            version, format_suffix = get_format_suffix(version_suffix)
            result.update({
                self.OUTPUT_VERSION: version,
            })
        else:
            raise QgsProcessingException(f'Invalid name {resource_name!r}')
        if format_suffix is not None:
            result[self.OUTPUT_DATASET_NAME] = resource_name.replace(
                format_suffix, '')
        result.update({
            self.OUTPUT_DEPARTMENT_ID: department,
            self.OUTPUT_DATASET_ID: dataset_id,
            self.OUTPUT_DB_STAGING_SCHEMA_NAME: f'{department}_staging',
        })
        validate_name_sections(result, feedback)
        return result


def validate_name_sections(
        sections: typing.Dict,
        feedback
) -> bool:
    return True


def get_format_suffix(version_part: str) -> typing.Tuple[str, str]:
    format_parts = version_part.split('.')[3:]
    format_suffix = ''
    if len(format_parts) != 0:
        format_suffix = '.' + '.'.join(format_parts)
    return version_part.replace(format_suffix, ''), format_suffix
