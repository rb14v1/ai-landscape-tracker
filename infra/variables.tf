variable "tenant_id" {
  description = "Organisation tenant identifier used for cost allocation and incident attribution."
  type        = string
}

variable "submission_id" {
  description = "Submission / project identifier used for cost allocation and incident attribution."
  type        = string
}

variable "cost_centre" {
  description = "Finance cost-centre code used for automated cloud-cost governance."
  type        = string
}
