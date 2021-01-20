from aws_cdk.core import Stack, StackProps, Construct, SecretValue
from aws_cdk.pipelines import CdkPipeline, SimpleSynthAction, ShellScriptAction

import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions

from webservice_stage import WebServiceStage
from aws_cdk.aws_codebuild import BuildEnvironment

from aws_cdk import aws_codebuild

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
                build_command="pytest pipelines_webinar/unittests",
                synth_command="cdk synth"
            )
        )
        # DEV STAGE
        dev_app = WebServiceStage(self, 'Dev', env={
            'account': '722610601746',
            'region' : 'eu-west-1'
        })
        dev_stage = pipeline.add_application_stage(dev_app)
        dev_stage.add_actions(ShellScriptAction(
            action_name="Integ",
            run_order=dev_stage.next_sequential_run_order(),
            additional_artifacts=[source_artifact],
            environment=BuildEnvironment(
                environment_variables={'CODECOV_TOKEN':aws_codebuild.BuildEnvironmentVariable(value='9e4d7998-7a8e-45a2-81fe-8a9c761cb03a')}),
            commands=[
                "pip install -r requirements.txt",
                "pytest pipelines_webinar/integtests",
                "echo 'TOKEN='$CODECOV_TOKEN",
                "pytest pipelines_webinar/unittests"
                # coverage
                # "pip install coverage",
                # "coverage run -a --source pipelines_webinar/unittests",
                # "coverage run -a --source pipelines_webinar/integtests",
                # "bash pipelines_webinar/coverage.sh"
            ],

        use_outputs={
            "SERVICE_URL": pipeline.stack_output(dev_app.url_output)
        }))
        dev_stage.add_manual_approval_action(action_name='PromoteToPro')
        # PRO STAGE
        pipeline.add_application_stage(WebServiceStage(self, 'Prod', env={
            'account': '807034265755',
            'region' : 'eu-west-1'
        }))
