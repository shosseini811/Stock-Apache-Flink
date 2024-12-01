provider "aws" {
  region = "us-east-1"
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "stock-flink-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = true
  
  tags = {
    Project = "stock-flink"
    Environment = "production"
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "stock_prices" {
  name           = "bitcoin_prices"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "timestamp"
  
  attribute {
    name = "timestamp"
    type = "N"
  }
  
  tags = {
    Project = "stock-flink"
    Environment = "production"
  }
}

# ECR Repositories
resource "aws_ecr_repository" "flink_processor" {
  name = "stock-flink-processor"
}

resource "aws_ecr_repository" "stock_scraper" {
  name = "stock-scraper"
}

resource "aws_ecr_repository" "dashboard" {
  name = "stock-dashboard"
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "stock-flink-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# IAM Roles
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "stock_flink_ecs_task_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Custom policy for DynamoDB access
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "dynamodb_access"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:BatchGetItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.stock_prices.arn
      }
    ]
  })
}
