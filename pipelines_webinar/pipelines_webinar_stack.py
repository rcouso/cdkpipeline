from os import path

from aws_cdk import core

import aws_cdk.aws_lambda as lmb
import aws_cdk.aws_apigateway as apigw
import aws_cdk.aws_codedeploy as codedeploy
import aws_cdk.aws_cloudwatch as cloudwatch
import aws_cdk.aws_cloudwatch_actions as cw_actions
import aws_cdk.aws_sns as sns
from aws_cdk.aws_apigateway import EndpointType
import aws_cdk.aws_dynamodb as dynamodb
from aws_cdk.aws_dynamodb import Attribute
import aws_cdk.custom_resources as cr

class PipelinesWebinarStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here
        this_dir = path.dirname(__file__)

        handler = lmb.Function(self, 'Handler',
            runtime=lmb.Runtime.PYTHON_3_7,
            handler='handler.handler',
            code=lmb.Code.from_asset(path.join(this_dir, 'lambda')))
        alias = lmb.Alias(self, "HandlerAlias",
            alias_name="Current",
            version=handler.current_version)
        gw = apigw.LambdaRestApi(self, 'Gateway',
            description='Endpoint for a singple Lambda-powered web service',
            handler=alias,
            endpoint_types=[EndpointType.REGIONAL])
        failure_alarm=cloudwatch.Alarm(self, "FailureAlarm",
            metric=cloudwatch.Metric(
                metric_name="5XXError",
                namespace="AWS/ApiGateway",
                dimensions={
                    "ApiName": "Gateway",
                },
                statistic="Sum",
                period=core.Duration.minutes(1)),
            threshold=1,
            evaluation_periods=1)
        alarm500topic = sns.Topic(self, "Alarm500Topic")
        failure_alarm.add_alarm_action(cw_actions.SnsAction(alarm500topic))
        codedeploy.LambdaDeploymentGroup(self,"DeploymentGroup",
            alias=alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.CANARY_10_PERCENT_10_MINUTES,alarms=[failure_alarm])
        # Create a dynamodb table
        table = dynamodb.Table(self, "TestTable", partition_key=Attribute(name="id", type=dynamodb.AttributeType.STRING))
        cr.AwsCustomResource(self, "TestTableCustomResource", on_create={
                'action':'putItem',
                'service':'DynamoDB',
                'physical_resource_id': cr.PhysicalResourceId.of(table._physical_name),
                'parameters':{
                    'TableName': cr.PhysicalResourceId.of(table._physical_name),
                    'Item' : {'id' : {'S': 'HOLA'}}
                }
            },
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE)
        )
        # OUTPUT
        self.url_output = core.CfnOutput(self, 'Url', value=gw.url)
