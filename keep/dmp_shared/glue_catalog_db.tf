resource "aws_glue_catalog_database" "ngta_telecom" {
  name = "ngta_telecom"
}

resource "aws_glue_catalog_database" "tsma_telecom_qsr" {
  name = "tsma_telecom_qsr"
}