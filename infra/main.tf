###############################################################################
# Tracker – Infrastructure root module
#
# This module owns the provider configuration and enforces the three mandatory
# FinOps tags on every cloud resource via provider-level default_tags.
#
# Required tag values are passed in at plan/apply time through variables so
# that org-specific identifiers are never hard-coded in source control.
#
# Usage:
#   terraform init
#   terraform apply \
#     -var="tenant_id=<tenantId>" \
#     -var="submission_id=<submissionId>" \
#     -var="cost_centre=<costCentre>"
#
# Or export TF_VAR_tenant_id / TF_VAR_submission_id / TF_VAR_cost_centre in
# your CI environment and run terraform apply without -var flags.
###############################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

###############################################################################
# Provider – default_tags propagate to every AWS resource in this module
###############################################################################

provider "aws" {
  default_tags {
    tags = {
      tenantId     = var.tenant_id
      submissionId = var.submission_id
      costCentre   = var.cost_centre
    }
  }
}
