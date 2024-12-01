output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.stock_prices.name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecr_repository_urls" {
  description = "URLs of the ECR repositories"
  value = {
    flink_processor = aws_ecr_repository.flink_processor.repository_url
    stock_scraper   = aws_ecr_repository.stock_scraper.repository_url
    dashboard       = aws_ecr_repository.dashboard.repository_url
  }
}
