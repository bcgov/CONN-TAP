module "ngta_raw_data" {
  source = "../../modules/s3_bucket"
  name   = var.ngta_raw_bucket
}

module "tsma_raw_data" {
  source = "../../modules/s3_bucket"
  name   = var.tsma_raw_bucket
}

module "tsma_ngta_mapping" {
  source = "../../modules/s3_bucket"
  name   = var.tsma_ngta_mapping_bucket
}

module "tsma_ngta_price_books" {
  source = "../../modules/s3_bucket"
  name   = var.tsma_ngta_price_books_bucket
}
