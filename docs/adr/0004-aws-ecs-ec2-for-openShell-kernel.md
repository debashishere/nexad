# AWS ECS on EC2 over ECS Fargate / GCP Cloud Run

NexAd deploys on AWS ECS on EC2 (Amazon Linux 2023 hosts) rather than ECS Fargate or GCP Cloud Run. Fargate and Cloud Run both run on managed kernels that restrict eBPF and Landlock LSM syscalls — capabilities required by the NVIDIA OpenShell sandbox. EC2 hosts give full kernel control, allowing OpenShell's Landlock filesystem confinement and eBPF network filtering to function correctly. AWS Secrets Manager handles credential storage, consistent with the LLD spec.
