#!/usr/bin/env python3

from aws_cdk import core

from pipelines_webinar.pipelines_webinar_stack import PipelinesWebinarStack


app = core.App()
PipelinesWebinarStack(app, "pipelines-webinar")

app.synth()
