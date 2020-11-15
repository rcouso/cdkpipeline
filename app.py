#!/usr/bin/env python3

from aws_cdk import core

from pipelines_webinar_stack import PipelinesWebinarStack
from pipeline_stack import PipelineStack


app = core.App()
PipelinesWebinarStack(app, "pipelines-webinar")
PipelineStack(app, 'PipelineStack', env={
    'account': '282334958158',
    'region' : 'eu-west-1'
})

app.synth()
