terraform {
  required_version = ">=1.7.5"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~>3.1.1"
    }
  }
}

resource "null_resource" "test" {
  triggers = {
    "some" =        "trigger"
  }
}