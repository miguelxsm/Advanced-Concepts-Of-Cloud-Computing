import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

OUTPUT_DIR = "plots"

def plot_metrics_from_data(metrics_data):
    """Generates plots directly from the metrics_data dictionary."""
    
    plot_data = []
    for tg_name, tg_metrics in metrics_data.items():
        for metric_name, datapoints in tg_metrics.items():
            if not datapoints:
                continue
            for dp in datapoints:
                value = next((dp[k] for k in ["Average", "Sum", "Maximum", "Minimum", "SampleCount"] if k in dp), None)
                
                if dp.get("Timestamp") and value is not None:
                    plot_data.append({
                        "TargetGroup": tg_name,
                        "Metric": metric_name,
                        "Timestamp": dp.get("Timestamp"),
                        "Value": value
                    })

    if not plot_data:
        print("⚠️ No data available to visualize.")
        return

    df = pd.DataFrame(plot_data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    metrics = df['Metric'].unique()

    markers = ['o', 's', '^', 'x', 'd']
    linestyles = ['-', '--', ':', '-.']

    for metric in metrics:
        plt.figure(figsize=(12, 7))
        metric_df = df[df['Metric'] == metric]
        
        for i, tg_name in enumerate(sorted(metric_df['TargetGroup'].unique())):
            tg_df = metric_df[metric_df['TargetGroup'] == tg_name].sort_values('Timestamp')
            plt.plot(
                tg_df['Timestamp'],
                tg_df['Value'],
                marker=markers[i % len(markers)],
                linestyle=linestyles[i % len(linestyles)],
                label=tg_name
            )

        plt.title(f'Metric: {metric}', fontsize=16)
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Value', fontsize=12)
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend()
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        output_path = os.path.join(OUTPUT_DIR, f"{metric}.png")
        plt.savefig(output_path)
        plt.close()
