resource "aws_kinesis_stream" "stock_stream" {
  name             = "stock-data-stream"
  shard_count      = 1
  retention_period = 24

  tags = {
    Environment = "production"
    Project     = "stock-analytics"
  }
}

resource "aws_kinesisanalyticsv2_application" "stock_analytics" {
  name                   = "stock-analytics"
  runtime_environment    = "SQL-1_0"
  service_execution_role = aws_iam_role.kinesis_analytics_role.arn

  application_configuration {
    sql_application_configuration {
      input {
        name_prefix = "SOURCE_SQL_STREAM"
        
        kinesis_streams_input {
          resource_arn = aws_kinesis_stream.stock_stream.arn
          
          input_schema {
            record_format {
              record_format_type = "JSON"
              
              mapping_parameters {
                json_mapping_parameters {
                  record_row_path = "$"
                }
              }
            }

            record_encoding = "UTF-8"

            record_columns {
              name     = "symbol"
              sql_type = "VARCHAR(4)"
              mapping  = "$.symbol"
            }
            record_columns {
              name     = "name"
              sql_type = "VARCHAR(100)"
              mapping  = "$.name"
            }
            record_columns {
              name     = "price"
              sql_type = "DOUBLE"
              mapping  = "$.price"
            }
            record_columns {
              name     = "change"
              sql_type = "VARCHAR(20)"
              mapping  = "$.change"
            }
            record_columns {
              name     = "volume"
              sql_type = "BIGINT"
              mapping  = "$.volume"
            }
            record_columns {
              name     = "timestamp"
              sql_type = "VARCHAR(30)"
              mapping  = "$.timestamp"
            }
          }
        }
      }
    }
  }
}

resource "aws_iam_role" "kinesis_analytics_role" {
  name = "kinesis-analytics-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "kinesisanalytics.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "kinesis_analytics_policy" {
  name = "kinesis-analytics-policy"
  role = aws_iam_role.kinesis_analytics_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:GetShardIterator",
          "kinesis:GetRecords",
          "kinesis:DescribeStream",
          "kinesis:ListShards"
        ]
        Resource = aws_kinesis_stream.stock_stream.arn
      }
    ]
  })
}
