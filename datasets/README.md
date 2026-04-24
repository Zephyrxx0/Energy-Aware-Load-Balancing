# Datasets for testing/

This folder contains real-world workload traces for the professional benchmark.

## Integrated Dataset (Used by Code)

- Source: Numenta Anomaly Benchmark (NAB), real AWS CloudWatch traces
- Repository: https://github.com/numenta/NAB
- Subfolder used: `data/realAWSCloudwatch`
- Local files:
  - `nab_realAWSCloudwatch/ec2_cpu_utilization_24ae8d.csv`
  - `nab_realAWSCloudwatch/ec2_cpu_utilization_53ea38.csv`
  - `nab_realAWSCloudwatch/ec2_cpu_utilization_5f5533.csv`
  - `nab_realAWSCloudwatch/ec2_cpu_utilization_ac20cd.csv`

CSV format is expected to include a `value` column in [0, 1], representing CPU utilization.

## Other Relevant Datasets Considered

- Alibaba Cluster Trace Program: large-scale production traces for scheduling research
  - https://github.com/alibaba/clusterdata
- Google Cluster Data 2011: historical production Borg trace (~41 GB compressed)
  - https://github.com/google/cluster-data

NAB was selected for direct integration because it is immediately downloadable, lightweight,
and directly includes AWS EC2 CPU utilization time series.

## Batch Comparison Runner

To benchmark all integrated NAB CSV files and export a combined report:

python testing/run_dataset_comparison.py --dataset-dir testing/datasets/nab_realAWSCloudwatch --output-dir benchmark_results

Generated files:
- `benchmark_results/dataset_comparison_report.json`
- `benchmark_results/dataset_comparison_report.csv`
