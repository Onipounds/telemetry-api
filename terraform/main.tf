terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = "eu-west-2"
}

# --- Container registry (kept from before) ---
resource "aws_ecr_repository" "api" {
  name         = "telemetry-api"
  force_delete = true
}

# --- Networking: use the account's default VPC and its subnets ---
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# --- Firewall: allow inbound web traffic to port 8080 ---
resource "aws_security_group" "api" {
  name        = "telemetry-api-sg"
  description = "Allow inbound HTTP to the API"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- IAM role that lets ECS pull the image and write logs ---
resource "aws_iam_role" "ecs_exec" {
  name = "ecs-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec" {
  role       = aws_iam_role.ecs_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# --- Where container logs go ---
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/telemetry-api"
  retention_in_days = 1
}

# --- The cluster (logical home for the service) ---
resource "aws_ecs_cluster" "main" {
  name = "telemetry-cluster"
}

# --- Task definition: HOW to run the container ---
resource "aws_ecs_task_definition" "api" {
  family                   = "telemetry-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_exec.arn

  container_definitions = jsonencode([{
    name      = "telemetry-api"
    image     = "${aws_ecr_repository.api.repository_url}:latest"
    essential = true
    portMappings = [{ containerPort = 8080, protocol = "tcp" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.api.name
        "awslogs-region"        = "eu-west-2"
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# --- The service: keeps one task running, with a public IP ---
resource "aws_ecs_service" "api" {
  name            = "telemetry-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }
}

output "ecr_repo_url" {
  value = aws_ecr_repository.api.repository_url
}