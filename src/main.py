import asyncio
import sys
import time
from setup import create_security_group, setup
from create_alb import main as create_alb
from benchmark import main as run_benchmark
from cloudwatch import main as fetch_metrics
from visualize import plot_metrics_from_data

async def main():
    """
    Pipeline principal que ejecuta todos los pasos de la infraestructura
    de forma secuencial, importando las funciones necesarias.
    """
    try:
        print("\n--- Creating Security Group and Instances ---")
        create_security_group()
        setup()
        print("Security Group and Instances created.")

        print("\n--- Creating Application Load Balancer ---")
        create_alb()
        print("Application Load Balancer created.")

        print("\n--- Running Benchmark ---")
        time.sleep(180)
        await run_benchmark()
        print("Benchmark completed.")

        print("\n--- Waiting for CloudWatch metrics to populate (2 minutes) ---")
        time.sleep(120)
        print("Wait finished.")
        
        print("\n--- Getting CloudWatch Metrics ---")
        metrics_data = fetch_metrics()
        print("Metrics fetched.")

        print("\n--- Visualizing Metrics ---")
        plot_metrics_from_data(metrics_data)
        print("Visualization complete. Plots saved in 'plots/' directory.")

        print("\nPipeline completed successfully!")
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
   
    asyncio.run(main())
