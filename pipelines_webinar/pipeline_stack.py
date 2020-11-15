from aws_cdk.core import Stack, StackProps, Construct, SecretValue
from aws_cdk.pipelines import CdkPipeline, SimpleSynthAction

import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions

from webservice_stage import WebServiceStage
from argparse import _get_action_name

class PipelineStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        source_artifact = codepipeline.Artifact()
        cloud_assembly_artifact = codepipeline.Artifact()

        pipeline = CdkPipeline(self, "Pipeline",
            pipeline_name="WebinarPipeline",
            cloud_assembly_artifact=cloud_assembly_artifact,
            source_action=codepipeline_actions.GitHubSourceAction(
                action_name="GitHub",
                output=source_artifact,
                oauth_token=SecretValue.secrets_manager("github-token"),
                trigger=codepipeline_actions.GitHubTrigger.POLL,
                # Replace these with your actual GitHub project info
                owner="rcouso",
                repo="cdkpipeline",
                branch="main"),
            synth_action=SimpleSynthAction(
                source_artifact=source_artifact,
                cloud_assembly_artifact=cloud_assembly_artifact,
                # Use this if you need a build step (if you're not using ts-node
                # or if you have TypeScript Lambdas that need to be compiled).
                install_command="npm install -g aws-cdk && pip install -r requirements.txt",
                synth_command="cdk synth"
            )
        )

        pre_prod_stage = pipeline.add_application_stage(WebServiceStage(self, 'Pre-Prod', env={
            'account': '282334958158',
            'region' : 'eu-west-1'
        }))

        pre_prod_stage.add_manual_approval_action(
            action_name =  "PromoteToProd")

        pipeline.add_application_stage(WebServiceStage(self, 'Prod', env={
            'account': '282334958158',
            'region' : 'eu-west-1'
        }))