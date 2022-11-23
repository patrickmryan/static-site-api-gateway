from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_apigateway as apigateway,
    aws_certificatemanager as acm,
    aws_iam as iam,
    aws_route53 as route53,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
)
from constructs import Construct

from config import config


class StaticHighSideStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket that will host the React application code
        bucket = s3.Bucket(
            self,
            "StaticAssetsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
        )
        # Copy built react app to bucket
        s3_deployment.BucketDeployment(
            self,
            "UiCodeToBucket",
            sources=[s3_deployment.Source.asset("react-app/build")],
            destination_bucket=bucket,
            retain_on_delete=False,
        )
        # IAM role granting apigateway read access to your S3 bucket
        api_role = iam.Role(
            self,
            "ExecuteRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
        )
        # Grant read access to read from S3 to api_role
        bucket.grant_read(api_role)

        api_policy_doc = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[iam.AnyPrincipal()],
                    actions=["execute-api:Invoke"],
                    resources=["execute-api:/*/*/*"],
                )
            ]
        )
        # When deploying in commercial accounts, we should lock down api access
        # to AWS internal network

        api_policy_doc.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["execute-api:Invoke"],
                resources=["execute-api:/*/*/*"],
                conditions={
                    "NotIpAddress": {"aws:SourceIp": config["awsIpRanges"]}
                },  # noqa: E501
            )
        )
        api = apigateway.RestApi(
            self,
            "S3Api",
            endpoint_types=[apigateway.EndpointType.REGIONAL],
            policy=api_policy_doc,
        )

        velvet_rope = iam.PolicyStatement(
            effect=iam.Effect.DENY,
            actions=["s3:List*"],
            resources=[bucket.bucket_arn, bucket.arn_for_objects("*")],
            principals=[iam.AnyPrincipal()],
            conditions={
                "StringNotLike": {
                    "aws:userId": [api_role.role_id, self.account]
                }  # noqa: E501
            },
        )
        bucket.add_to_resource_policy(velvet_rope)

        if config["hostedZoneId"]:
            hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
                self,
                "HostedZone",
                hosted_zone_id=config["hostedZoneId"],
                zone_name=config["domainName"],
            )

        api_certificate = acm.Certificate(
            self,
            "ApiCertificate",
            domain_name=f"{config['subdomain']}.{config['domainName']}",
            validation=acm.CertificateValidation.from_dns(
                hosted_zone=hosted_zone if config["hostedZoneId"] else None
            ),
        )
        # Need a domain name
        api_domain = api.add_domain_name(
            "ApiDomainName",
            certificate=api_certificate,
            domain_name=f"{config['subdomain']}.{config['domainName']}",
            security_policy=apigateway.SecurityPolicy.TLS_1_2,
        )
        route53.CnameRecord(
            self,
            "DnsCnameRecord",
            domain_name=api_domain.domain_name_alias_domain_name,
            zone=hosted_zone,
            record_name=config["subdomain"],
        )
        # hardcode index.html for when url without path entered
        api.root.add_method(
            http_method="GET",
            integration=apigateway.AwsIntegration(
                service="s3",
                integration_http_method="GET",
                # All requests to raw url directed to index.html
                path=f"{bucket.bucket_name}/index.html",
                options=apigateway.IntegrationOptions(
                    credentials_role=api_role,
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            selection_pattern="2\d{2}",  # noqa: W605
                            response_parameters={
                                "method.response.header.Content-Type": "integration.response.header.Content-Type"  # noqa: E501
                            },
                        ),
                        apigateway.IntegrationResponse(
                            status_code="403",
                            selection_pattern="4\d{2}",  # noqa: W605
                        ),
                    ],
                ),
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True
                    },  # noqa: E501
                ),
                apigateway.MethodResponse(status_code="404"),
            ],
        )
        path_resource = api.root.add_resource("{patha}")
        path_resource.add_method(
            http_method="GET",
            integration=apigateway.AwsIntegration(
                service="s3",
                integration_http_method="GET",
                path=f"{bucket.bucket_name}/{{patha}}",
                options=apigateway.IntegrationOptions(
                    credentials_role=api_role,
                    request_parameters={
                        "integration.request.path.patha": "method.request.path.patha"  # noqa: E501
                    },
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            selection_pattern="2\d{2}",  # noqa: W605
                            response_parameters={
                                "method.response.header.Content-Type": "integration.response.header.Content-Type"  # noqa: E501
                            },
                        ),
                        apigateway.IntegrationResponse(
                            status_code="403",
                            selection_pattern="4\d{2}",  # noqa: W605
                        ),
                    ],
                ),
            ),
            request_parameters={"method.request.path.patha": True},
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True
                    },  # noqa: E501
                ),
                apigateway.MethodResponse(status_code="404"),
            ],
        )

        level_1_resource = path_resource.add_resource("{pathb}")

        level_2_resource = level_1_resource.add_resource("{pathc}")
        level_2_resource.add_method(
            http_method="GET",
            integration=apigateway.AwsIntegration(
                service="s3",
                integration_http_method="GET",
                path=f"{bucket.bucket_name}/{{patha}}/{{pathb}}/{{pathc}}",
                options=apigateway.IntegrationOptions(
                    credentials_role=api_role,
                    request_parameters={
                        "integration.request.path.patha": "method.request.path.patha",  # noqa: E501
                        "integration.request.path.pathb": "method.request.path.pathb",  # noqa: E501
                        "integration.request.path.pathc": "method.request.path.pathc",  # noqa: E501
                    },
                    integration_responses=[
                        apigateway.IntegrationResponse(
                            status_code="200",
                            selection_pattern="2\d{2}",  # noqa: W605
                            response_parameters={
                                "method.response.header.Content-Type": "integration.response.header.Content-Type"  # noqa: E501
                            },
                        ),
                        apigateway.IntegrationResponse(
                            status_code="403",
                            selection_pattern="4\d{2}",  # noqa: W605
                        ),
                    ],
                ),
            ),
            request_parameters={
                "method.request.path.patha": True,
                "method.request.path.pathb": True,
                "method.request.path.pathc": True,
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True
                    },  # noqa: E501
                ),
                apigateway.MethodResponse(status_code="404"),
            ],
        )
