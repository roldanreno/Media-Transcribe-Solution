import aws_cdk as core
import aws_cdk.assertions as assertions

from media_transcribe_solution.media_transcribe_solution_stack import MediaTranscribeSolutionStack

# example tests. To run these tests, uncomment this file along with the example
# resource in media_transcribe_solution/media_transcribe_solution_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MediaTranscribeSolutionStack(app, "media-transcribe-solution")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
