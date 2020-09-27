import json
import typing

from PyQt5.QtNetwork import (
    QNetworkRequest,
)
from PyQt5.QtCore import (
    QCoreApplication,
    QUrl,
    QUrlQuery,
)
from qgis.core import (
    QgsFeedback,
    QgsNetworkAccessManager,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingOutputBoolean,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingParameterAuthConfig,
    QgsProcessingParameterExpression,
    QgsProcessingParameterString,
)


from dataset_qa_workbench.datasetqaworkbench.constants import (
    REPORT_HANDLER_INPUT_NAME,
)
from dataset_qa_workbench.processing_provider.algorithms.base import (
    parse_as_expression,
)


class DomiNodeReportUploaderAlgorithm(QgsProcessingAlgorithm):
    INPUT_AUTH_CONFIG = 'INPUT_AUTH_CONFIG'
    INPUT_DOMINODE_BASE_URL = 'INPUT_DOMINODE_BASE_URL'
    OUTPUT_RESULT = 'OUTPUT_RESULT'
    OUTPUT_DOMINODE_RESOURCE_URL = 'OUTPUT_DOMINODE_RESOURCE_URL'
    OUTPUT_VALIDATION_REPORT_URL = 'OUTPUT_VALIDATION_REPORT_URL'

    QGIS_VARIABLE_PREFIX = 'dominode_report_uploader'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def group(self):
        return self.tr('DomiNode')

    def groupId(self):
        return 'dominode'

    def name(self):
        return 'dominodereportuploader'

    def displayName(self):
        return self.tr('Upload validation report to DomiNode')

    def createInstance(self):
        return self.__class__()

    def shortHelpString(self):
        return self.tr(
            f"This algorithm uploads the generated validation report to "
            f"DomiNode.\n\n"
            f"In order to be easily automatable, the algorithm can be "
            f"configured by setting the following QGIS global variables "
            f"(go to Settings -> Options... -> Variables): "
            f"\n\n"
            f"{self.QGIS_VARIABLE_PREFIX}_auth_config_id: auth config id of "
            f"the credentials to use to authenticate with the DomiNode "
            f"server\n"
            f"{self.QGIS_VARIABLE_PREFIX}_dominode_endpoint: Endpoint of "
            f"the DomiNode API"
        )

    def initAlgorithm(
            self,
            configuration,
            p_str=None,
            Any=None,
            *args,
            **kwargs
    ):
        self.addParameter(
            QgsProcessingParameterString(
                REPORT_HANDLER_INPUT_NAME,
                self.tr('Input validation report'),
                defaultValue='{}',
                multiLine=True
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_AUTH_CONFIG,
                self.tr('DomiNode Authentication configuration ID'),
                defaultValue=f'@{self.QGIS_VARIABLE_PREFIX}_auth_config_id',
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_DOMINODE_BASE_URL,
                self.tr('DomiNode base URL'),
                defaultValue=f'@{self.QGIS_VARIABLE_PREFIX}_base_url'
            )
        )
        self.addOutput(
            QgsProcessingOutputBoolean(
                self.OUTPUT_RESULT,
                'Whether the request accepted or not'
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_DOMINODE_RESOURCE_URL,
                'URL of the relevant DomiNode resource'
            )
        )
        self.addOutput(
            QgsProcessingOutputNumber(
                self.OUTPUT_VALIDATION_REPORT_URL,
                'URL of the relevant validation report'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        raw_report = self.parameterAsString(
            parameters, REPORT_HANDLER_INPUT_NAME, context)
        report = json.loads(raw_report)
        auth_config = parse_as_expression(
            self.parameterAsExpression(
                parameters, self.INPUT_AUTH_CONFIG, context)
        )
        base_url = parse_as_expression(
            self.parameterAsExpression(
                parameters, self.INPUT_DOMINODE_BASE_URL, context)
        )
        if not base_url:
            raise QgsProcessingException(f'Invalid base_url: {base_url}')
        else:
            base_url = base_url if base_url.endswith('/') else f'{base_url}/'
        feedback.pushInfo(f'report: {report}')
        feedback.pushInfo(f'auth_config: {auth_config}')
        feedback.pushInfo(f'base_url: {base_url}')
        network_manager = QgsNetworkAccessManager.instance()
        resource = get_resource(
            report['dataset'], base_url, network_manager, feedback)
        if resource is None:
            resource = post_resource(
                report['dataset'],
                report['dataset_type'],
                report['artifact_type'],
                base_url,
                network_manager=network_manager,
                auth_config=auth_config,
                feedback=feedback
            )
        feedback.pushInfo(f'resource: {resource}')
        validation_report = post_validation_report(
            report, base_url, network_manager, auth_config, feedback)
        feedback.pushInfo(f'validation_report: {validation_report}')
        return {
            self.OUTPUT_RESULT: True,
            self.OUTPUT_DOMINODE_RESOURCE_URL: resource['url'],
            self.OUTPUT_VALIDATION_REPORT_URL: validation_report['url'],
        }


def get_resource(
        name: str,
        dominode_base_url: str,
        network_manager: QgsNetworkAccessManager,
        feedback: typing.Optional[QgsFeedback] = None,
) -> typing.Optional[typing.Dict]:
    url_query = QUrlQuery()
    url_query.addQueryItem('name', name)
    url = QUrl(
        f'{dominode_base_url}/dominode-validation/api/dominode-resources/')
    url.setQuery(url_query)
    request = QNetworkRequest(url)
    request.setHeader(QNetworkRequest.ContentTypeHeader, 'application/json')
    reply = network_manager.blockingGet(request, '', True, feedback=feedback)
    status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    result = None
    if status_code == 200:
        raw_string_contents = bytes(reply.content()).decode('utf-8')
        contents = json.loads(raw_string_contents)
        exists = contents.get('count', 0) > 0
        if exists:
            result = contents['results'][0]
    return result


def post_resource(
        name: str,
        resource_type: str,
        artifact_type: str,
        dominode_base_url: str,
        network_manager: QgsNetworkAccessManager,
        auth_config: str,
        feedback: typing.Optional[QgsFeedback] = None,
) -> typing.Dict:
    return _post_data(
        f'{dominode_base_url}/dominode-validation/api/dominode-resources/',
        {
            'name': name,
            'resource_type': resource_type,
            'artifact_type': artifact_type,
        },
        network_manager,
        auth_config,
        feedback=feedback
    )


def post_validation_report(
        report: typing.Dict,
        dominode_base_url: str,
        network_manager: QgsNetworkAccessManager,
        auth_config: str,
        feedback: typing.Optional[QgsFeedback] = None
) -> typing.Dict:
    return _post_data(
        f'{dominode_base_url}/dominode-validation/api/validation-reports/',
        {
            'resource': report['dataset'],
            'result': report['dataset_is_valid'],
            'validation_datetime': report['generated'],
            'checklist_name': report['checklist'],
            'checklist_description': report['description'],
            'checklist_steps': report['checks'],
        },
        network_manager,
        auth_config,
        feedback=feedback
    )


def _post_data(
        url: str,
        data_: typing.Dict,
        network_manager: QgsNetworkAccessManager,
        auth_config: str,
        feedback: typing.Optional[QgsFeedback] = None
):
    request = QNetworkRequest(QUrl(url))
    request.setHeader(QNetworkRequest.ContentTypeHeader, 'application/json')
    reply = network_manager.blockingPost(
        request,
        json.dumps(data_).encode('utf-8'),
        auth_config,
        True,
        feedback=feedback
    )
    status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    raw_string_contents = bytes(reply.content()).decode('utf-8')
    if status_code == 201:
        result = json.loads(raw_string_contents)
    else:
        raise QgsProcessingException(
            f'POST request failed. '
            f'status_code: {status_code} - '
            f'error_string: {reply.errorString()} - '
            f'reply_contents: {raw_string_contents}'
        )
    return result
