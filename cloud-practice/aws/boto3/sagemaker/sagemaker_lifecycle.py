#!/usr/bin/env python3
"""SageMaker lifecycle with boto3 — train -> model -> endpoint -> invoke -> cleanup.

Uses the low-level boto3 clients (not the higher-level `sagemaker` SDK) so you see
the actual API surface the docs describe. Trains the built-in XGBoost algorithm on
a CSV you provide in S3, deploys a real-time endpoint, invokes it, and tears down.

Requires: boto3 + AWS creds with SageMaker/S3/IAM permissions, an execution role,
and a training CSV in S3 (label in column 0 for XGBoost).
    pip install boto3
    python sagemaker_lifecycle.py --help

⚠️ Training jobs AND endpoints cost money. Run `cleanup` — endpoints bill 24/7.
"""

from __future__ import annotations

import argparse
import sys
import time

import boto3

# Built-in XGBoost image account IDs vary by Region. A few common ones; see
# https://docs.aws.amazon.com/sagemaker/latest/dg/ecr-us-east-1.html for the full list.
XGBOOST_ACCOUNTS = {
    "us-east-1": "683313688378",
    "us-west-2": "246618743249",
    "eu-west-1": "685385470294",
    "ap-south-1": "720646828776",
}


def xgboost_image(region: str, version: str = "1.7-1") -> str:
    acct = XGBOOST_ACCOUNTS.get(region)
    if not acct:
        raise SystemExit(f"No XGBoost account mapping for {region}; pass --image explicitly.")
    return f"{acct}.dkr.ecr.{region}.amazonaws.com/sagemaker-xgboost:{version}"


def sm(region):
    return boto3.client("sagemaker", region_name=region)


def train(region, role_arn, train_s3, output_s3, image, job_name, instance="ml.m5.large", spot=True):
    """Create a training job (built-in XGBoost). Managed Spot on by default to save cost."""
    c = sm(region)
    kwargs = {
        "TrainingJobName": job_name,
        "AlgorithmSpecification": {"TrainingImage": image, "TrainingInputMode": "File"},
        "RoleArn": role_arn,
        "InputDataConfig": [{
            "ChannelName": "train",
            "DataSource": {"S3DataSource": {
                "S3DataType": "S3Prefix", "S3Uri": train_s3, "S3DataDistributionType": "FullyReplicated"}},
            "ContentType": "text/csv",
        }],
        "OutputDataConfig": {"S3OutputPath": output_s3},
        "ResourceConfig": {"InstanceType": instance, "InstanceCount": 1, "VolumeSizeInGB": 10},
        "HyperParameters": {"objective": "reg:squarederror", "num_round": "50"},
        "StoppingCondition": {"MaxRuntimeInSeconds": 3600},
    }
    if spot:
        # Managed Spot: cheaper, resumable; needs a checkpoint config + a longer max-wait.
        kwargs["EnableManagedSpotTraining"] = True
        kwargs["StoppingCondition"]["MaxWaitTimeInSeconds"] = 3600
    c.create_training_job(**kwargs)
    print(f"training job {job_name} started (spot={spot}) ... waiting")
    c.get_waiter("training_job_completed_or_stopped").wait(TrainingJobName=job_name)
    desc = c.describe_training_job(TrainingJobName=job_name)
    print(f"  status: {desc['TrainingJobStatus']}  artifact: {desc['ModelArtifacts']['S3ModelArtifacts']}")
    return desc["ModelArtifacts"]["S3ModelArtifacts"]


def deploy(region, role_arn, image, model_data, name, instance="ml.m5.large"):
    """Model -> EndpointConfig -> Endpoint (persistent, billable)."""
    c = sm(region)
    c.create_model(ModelName=f"{name}-model", ExecutionRoleArn=role_arn,
                   PrimaryContainer={"Image": image, "ModelDataUrl": model_data})
    c.create_endpoint_config(
        EndpointConfigName=f"{name}-epc",
        ProductionVariants=[{
            "VariantName": "AllTraffic", "ModelName": f"{name}-model",
            "InstanceType": instance, "InitialInstanceCount": 1, "InitialVariantWeight": 1.0}])
    c.create_endpoint(EndpointName=name, EndpointConfigName=f"{name}-epc")
    print(f"deploying endpoint {name} ... (this takes several minutes)")
    c.get_waiter("endpoint_in_service").wait(EndpointName=name)
    print(f"  in service: {name}")


def invoke(region, name, body, content_type="text/csv"):
    rt = boto3.client("sagemaker-runtime", region_name=region)
    resp = rt.invoke_endpoint(EndpointName=name, ContentType=content_type, Body=body)
    print("prediction:", resp["Body"].read().decode())


def cleanup(region, name):
    """Delete endpoint -> endpoint config -> model. Endpoints bill until deleted!"""
    c = sm(region)
    for fn, arg in [(c.delete_endpoint, {"EndpointName": name}),
                    (c.delete_endpoint_config, {"EndpointConfigName": f"{name}-epc"}),
                    (c.delete_model, {"ModelName": f"{name}-model"})]:
        try:
            fn(**arg); print(f"deleted {list(arg.values())[0]}")
        except Exception as e:  # noqa: BLE001 - best-effort cleanup
            print(f"  {list(arg.values())[0]}: {e}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--image", help="Override the XGBoost image URI")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train")
    t.add_argument("--role-arn", required=True); t.add_argument("--train-s3", required=True)
    t.add_argument("--output-s3", required=True)
    t.add_argument("--job-name", default=f"xgb-{int(time.time())}")

    d = sub.add_parser("deploy")
    d.add_argument("--role-arn", required=True); d.add_argument("--model-data", required=True)
    d.add_argument("--name", default="xgb-endpoint")

    i = sub.add_parser("invoke")
    i.add_argument("--name", default="xgb-endpoint"); i.add_argument("--body", required=True)

    cl = sub.add_parser("cleanup"); cl.add_argument("--name", default="xgb-endpoint")

    args = p.parse_args()
    image = args.image or (xgboost_image(args.region) if args.cmd in ("train", "deploy") else None)

    if args.cmd == "train":
        art = train(args.region, args.role_arn, args.train_s3, args.output_s3, image, args.job_name)
        print(f"\nNext: python {sys.argv[0]} deploy --role-arn {args.role_arn} --model-data {art}")
    elif args.cmd == "deploy":
        deploy(args.region, args.role_arn, image, args.model_data, args.name)
    elif args.cmd == "invoke":
        invoke(args.region, args.name, args.body)
    elif args.cmd == "cleanup":
        cleanup(args.region, args.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
