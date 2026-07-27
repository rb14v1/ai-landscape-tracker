terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ---------------------------------------------------------------------------
# Provider – default_tags ensures every AWS resource created in this root
# module inherits the three mandatory FinOps tags automatically.
# ---------------------------------------------------------------------------
provider "aws" {
  default_tags {
    tags = {
      tenantId     = var.tenant_id
      submissionId = var.submission_id
      costCentre   = var.cost_centre
    }
  }
}
