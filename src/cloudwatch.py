import boto3
import json
import csv
import datetime
import sys

REGION = "us-east-1" 

cloudwatch = boto3.client("cloudwatch", region_name=REGION)
elbv2 = boto3.client("elbv2", region_name=REGION)

def load_alb_info():
    """Load ALB info from alb_info.json"""
    with open("alb_info.json") as f:
        alb_info = json.load(f)
    return alb_info


def get_metric(metric_name, namespace, dimensions, period=60, minutes=30, stat="Average"):
    """Get metric data from CloudWatch"""
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(minutes=minutes)

    try:
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'm1', 
                    'MetricStat': {
                        'Metric': {
                            'Namespace': namespace,
                            'MetricName': metric_name,
                            'Dimensions': dimensions
                        },
                        'Period': period,
                        'Stat': stat,
                    },
                    'ReturnData': True,
                }
            ],
            StartTime=start,
            EndTime=end,
            ScanBy='TimestampAscending'
        )

        results = response.get("MetricDataResults", [])
        if not results:
            return []

        metric_result = results[0]
        timestamps = metric_result.get("Timestamps", [])
        values = metric_result.get("Values", [])

        datapoints = [{"Timestamp": ts, stat: val} for ts, val in zip(timestamps, values)]
        return datapoints
    except Exception as e:
        print(f"⚠️ Error getting metric {metric_name}: {e}")
        return []

def main():
    alb_info = load_alb_info()
    lb_fullname = alb_info["LoadBalancerFullName"]

    target_groups = {
        "cluster1": alb_info["TargetGroup1"].split(':')[-1],
        "cluster2": alb_info["TargetGroup2"].split(':')[-1]
    }

    print("Fetching CloudWatch metrics for Target Groups...")
    metrics_data = {}

    for tg_label, tg_fullname in target_groups.items():
        tg_arn = alb_info[f"TargetGroup{tg_label[-1]}"]
        print(f"  🔹 {tg_label} → {tg_fullname}")

        dimensions = [
            {"Name": "TargetGroup", "Value": tg_fullname},
            {"Name": "LoadBalancer", "Value": lb_fullname}
        ]
        metrics_data[tg_label] = {
            "HealthyHostCount": get_metric("HealthyHostCount", "AWS/ApplicationELB", dimensions, stat="Maximum", minutes=60),
            "UnHealthyHostCount": get_metric("UnHealthyHostCount", "AWS/ApplicationELB", dimensions, stat="Maximum", minutes=60),
            "RequestCount": get_metric("RequestCount", "AWS/ApplicationELB", dimensions, stat="Sum", minutes=60),
            "TargetResponseTime": get_metric("TargetResponseTime", "AWS/ApplicationELB", dimensions, stat="Average", minutes=60),
            "HTTPCode_Target_2XX_Count": get_metric("HTTPCode_Target_2XX_Count", "AWS/ApplicationELB", dimensions, stat="Sum", minutes=60),
            "HTTPCode_Target_4XX_Count": get_metric("HTTPCode_Target_4XX_Count", "AWS/ApplicationELB", dimensions, stat="Sum", minutes=60),
            "HTTPCode_Target_5XX_Count": get_metric("HTTPCode_Target_5XX_Count", "AWS/ApplicationELB", dimensions, stat="Sum", minutes=60),
        }

    print(f"Fetching overall metrics for ALB: {lb_fullname}")
    alb_dimensions = [{"Name": "LoadBalancer", "Value": lb_fullname}]
    metrics_data["ALB_Total"] = {
        "RequestCount": get_metric("RequestCount", "AWS/ApplicationELB", alb_dimensions, stat="Sum", minutes=60)
    }

    return metrics_data


if __name__ == "__main__":
    data = main()
