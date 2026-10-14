# Terraform evidence for AWS diagrams

Read this for repository-based diagrams. Inspect source files and relevant configuration overrides statically. Treat comments and architecture documents as explanations to reconcile against the current resources and application code.

## Resolve only what the evidence supports

Read literal variable defaults, selected local tfvars, module inputs, and deployment wrappers such as Makefiles that set region or configuration paths. Do not dump secrets or Terraform state. Record which value won and where it came from. A locally resolvable `for_each`, `count`, or expression may be expanded; unresolved external values remain unknown. Never guess instance counts or CIDRs. An optional module existing on disk does not establish that it is deployed.

Do not invoke Terraform just to resolve values: external data sources and providers may run commands or contact AWS. Inspect existing CDK/CloudFormation source or templates without running synthesis by default.

## Placement

| Source | Semantic interpretation |
| --- | --- |
| `aws_vpc` | VPC boundary and `cidr_block` |
| `aws_subnet` | All known CIDRs, AZs, and associated route tables |
| Route to an internet gateway | Public subnet |
| No direct IGW route, NAT egress | Private subnet with internet egress |
| No internet route, local/service endpoint routes only | Isolated subnet; preserve source naming separately |
| `aws_instance`, NAT gateway | Actual subnet placement |
| `aws_lb` / `aws_ecs_service` | Logical resource plus all configured subnet/AZ placements |
| Lambda with `vpc_config` | VPC-attached logical function with every configured subnet; not a fixed replica per subnet |
| Lambda without `vpc_config` | Regional service outside customer VPC boundaries |
| RDS/Aurora/ElastiCache | Resolve subnet group, instance/cluster roles and explicit AZ settings; do not infer member locations from the subnet group alone |
| IGW / gateway endpoint | VPC association; show only when relevant |
| Interface endpoint | Retain every subnet attachment; normally summarize instead of drawing ENIs |
| API Gateway, S3, DynamoDB, SQS, SNS, Cognito, EventBridge | Regional managed service outside the VPC, even when accessed privately |
| CloudFront / IAM | Global scope where appropriate; do not force all AWS services into a Region |
| CloudWatch, ECR, Secrets Manager, KMS, SSM | Supporting services by default; preserve actual scope and exceptional dependencies |

Security groups are policy associations, not exclusive containment boundaries. Draw SG summaries only when requested or material; a resource may have more than one SG.

## Connections

| Evidence | Drawing decision |
| --- | --- |
| Application SDK/client calls and their configured targets | Application connectivity, subject to relevance filtering |
| API integration, load-balancer target registration | Entry service to its actual target |
| EventBridge target, scheduler target, event-source mapping | Event-driven invocation; identify logical event flow rather than claiming packet direction |
| DLQ configuration | Show the actual producer and failure class; distinguish delivery failures from handler failures |
| Presigned URL generation plus client upload/download | Client-to-storage transfer, not a payload passing through the URL issuer |
| SG allow rule | Policy only; **do not create an application arrow** |
| IAM resource ARN | Permission only; **do not create an application arrow** |
| Dependency on a routine supporting service | Retain the fact; omit the arrow unless exceptional |

Keep Lambda invocation/control-plane behavior distinct from runtime VPC access. For example, do not infer a runtime ECR connection solely because the Lambda uses a container image.

## HA review

Compare workload placements with endpoint placements, ingress, data roles and any bastion dependency. Record single-AZ bottlenecks without adding every underlying ENI to the diagram. Backup configuration and service availability are different properties. If a value is only a default or the live deployment has not been checked, label that evidence basis.
