variable "environment" {
  description = "Environment (e.g. prod, dev, staging)"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "stock-flink"
}

variable "container_memory" {
  description = "Container memory in MiB"
  type        = number
  default     = 2048
}

variable "container_cpu" {
  description = "Container CPU units"
  type        = number
  default     = 1024
}
