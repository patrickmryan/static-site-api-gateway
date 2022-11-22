import os
import aws_cdk as cdk
from static_high_side.static_high_side_stack import StaticHighSideStack


app = cdk.App()
StaticHighSideStack(
    app,
    "static-high-side-site",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
