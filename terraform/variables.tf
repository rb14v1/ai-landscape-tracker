variable "tenant_id" {
  description = "Tenant identifier used for cost allocation and incident attribution (maps to the 'tenantId' tag)."
  type        = string
}

variable "submission_id" {
  description = "Submission / work-order identifier used for cost allocation and governance (maps to the 'submissionId' tag)."
  type        = string
}

variable "cost_centre" {
  description = "Cost centre code used for financial attribution (maps to the 'costCentre' tag)."
  type        = string
}
