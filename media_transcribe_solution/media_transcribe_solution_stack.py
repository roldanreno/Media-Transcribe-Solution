from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_mediaconvert as mediaconvert,
    aws_iot as iot,
    Duration
)
from constructs import Construct
import aws_cdk.aws_lambda_event_sources as eventsources
import json

class MediaTranscribeSolutionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ################### BUCKETS ######################

        #Bucket to receive the video ingest from Cx
        vIngestBucket = s3.Bucket(self, "vIngestBucket",
            versioned=True, 
            encryption=s3.BucketEncryption.S3_MANAGED 
        )
        #Bucket to receive the output from media convert lambda
        audioIngestBucket = s3.Bucket(self, "audioBucket",
            versioned=True, 
            encryption=s3.BucketEncryption.S3_MANAGED 
        )
        #Bucket to receive the output from Transcript
        textIngestBucket = s3.Bucket(self, "textBucket",
            versioned=True, 
            encryption=s3.BucketEncryption.S3_MANAGED 
        )
        #Bucket to receive the ingest from text bucket into Bedrock KB
        KBIngestBucket = s3.Bucket(self, "KBBucket",
            versioned=True, 
            encryption=s3.BucketEncryption.S3_MANAGED 
        )

        ############### DEFINE ROLES ####################

        transcribeRole = iam.Role(self, "transcribeRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        transcribeRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        transcribeRole.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["s3:*", "transcribe:*"]
        ))

        mediaconvertLambdaRole = iam.Role(self, "mediaconverteRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        mediaconvertLambdaRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        mediaconvertLambdaRole.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["mediaconvert:*", "s3:*", "iam:PassRole"]
        ))

        mediaconvertExecutionRole = iam.Role(self, "mediaconvertExecutionRole",
            assumed_by=iam.ServicePrincipal("mediaconvert.amazonaws.com")
        )
        mediaconvertExecutionRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"))
        mediaconvertExecutionRole.add_to_policy(iam.PolicyStatement(
            resources=[vIngestBucket.bucket_arn],
            actions=["Get:*", "List:*"]
        ))
        mediaconvertExecutionRole.add_to_policy(iam.PolicyStatement(
            resources=[audioIngestBucket.bucket_arn],
            actions=["Put:*"]
        ))

        ############# MEDIA CONVERT QUEUE ################
        cfn_queue = mediaconvert.CfnQueue(self, "MyCfnQueue",
            description="Queue to convert video to audio",
            pricing_plan="ON_DEMAND"
        )
            #Preset config JSON, used to build the job preset
        with open('../VideoDemo/src/config/presetConfig.json', 'r') as file:
            presetConfig = json.load(file)
            #Mediaconvert job preset definition
        cfn_preset = mediaconvert.CfnPreset(self, "MyCfnPreset",
            description= "MP3 Output",
            settings_json=presetConfig,
            name="mp3"

        )
        
        ################## LAMBDAS #######################

        #Lambda function that will trigger when object drops in audio ingest bucket
        transcribeAudioLambda = _lambda.Function(
            self,
            id="transcribeAudioLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(15),
            code=_lambda.Code.from_asset("../VideoDemo/src/lambda"), 
            handler="transcribeAudio.handler",
            role= transcribeRole,
            environment = {
                'DESTINATION':textIngestBucket.bucket_name,
                'REGION': "us-east-1"
            }
        )

        #Lambda function that will be triggered when object drops in vIngest bucket
        ConvertVideoToAudioLambda = _lambda.Function(
            self,
            id="ConvertVideoToAudioLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="ConvertVideoToAudio.handler",
            code=_lambda.Code.from_asset("../VideoDemo/src/lambda"),
            timeout=Duration.minutes(15),
            role=mediaconvertLambdaRole,
            environment = {
                'DESTINATION': 's3://' + audioIngestBucket.bucket_name + '/',
                'REGION': "us-east-1",
                'QUEUE': cfn_queue.attr_arn,
                'ROLE': mediaconvertExecutionRole.role_arn
            }
        )

        #Lambda function to move the text transcription to knowledge base
        ############### Lambda triggers ##################
        ConvertVideoToAudioLambda.add_event_source(eventsources.S3EventSource(vIngestBucket,
            events=[s3.EventType.OBJECT_CREATED]
        ))

        transcribeAudioLambda.add_event_source(eventsources.S3EventSource(audioIngestBucket,
            events=[s3.EventType.OBJECT_CREATED]
        ))
        
        

