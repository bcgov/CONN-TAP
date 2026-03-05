module "ngta_raw_data" {
  source            = "../../modules/s3_bucket"
  name              = "ngta-raw-data"
  enable_versioning = false
}

module "tsma_raw_data" {
  source            = "../../modules/s3_bucket"
  name              = "tsma-raw-data"
  enable_versioning = false
}

module "tsma_ngta_mapping" {
  source            = "../../modules/s3_bucket"
  name              = "tsma-ngta-mapping"
  enable_versioning = false
}

module "tsma_ngta_price_books" {
  source            = "../../modules/s3_bucket"
  name              = "tsma-ngta-price-books"
  enable_versioning = false
}