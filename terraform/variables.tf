variable "tenant_id" {
  description = "Tenant identifier used for cost allocation and incident attribution (maps to the 'tenantId' tag on all cloud resources)."
  type        = string
}

variable "submission_id" {
  description = "Submission identifier used for cost allocation and incident attribution (maps to the 'submissionId' tag on all cloud resources)."
  type        = string
}

variable "cost_centre" {
  description = "Cost centre code used for financial charge-back (maps to the 'costCentre' tag on all cloud resources)."
  type        = string
}

variable "aws_region" {
  description = "AWS region in which to deploy resources."
  type        = string
  default     = "eu-west-1"
}
