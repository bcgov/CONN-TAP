aws_region = "ca-central-1"

licence = "dd5a29"
env     = "test"

vpc_name        = "Test"
ec2_subnet_name = "Test-App-A"

ec2_security_group_names = [
  "App",
  "Data"
]

powerbi_key_name      = "dmp-powerbi-test"
ec2_public_key        = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCZ7vI3PIiZqqwDjLmhDKrGAGNPkW4K9HbPXuK3g4k2/8IrQ6oQfVBWqwuwW8jfBcILXzZJL5/nlo3LNy5s05tEpB6/9CkKyLbcSZjT7HeComi7Kj2VksnplgcYD/nTXqjKr3lXBQzRkD+kHAQ6wa0ia62RwOD8Pr50WNlomd8FfRwFrrbDxlGFPb+nXaChsGL7SCsP7aT6uXeCXd6EWEu9OI1DanUvQA1r45lfiG9ziWh37kZqhlVtEVC8tbkwIMWzOQPQEYrWkJ2l3l7BynQNa6uZkoBLT4yY5p7hQUmdx1H58wtwE3L5h/hUSKsoHjekxk4YxoFFaqZlH9ZzBHY7"
powerbi_ami_id        = "ami-067abc25c5d2e14af"
powerbi_instance_type = "t3.large"
powerbi_instance_name = "ec2-powerbi-desktop-935827529718"

enable_redshift    = false
enable_tsma_lambda = true

ngta_raw_bucket_name       = "dd5a29-test-ngta-raw-data"
tsma_raw_bucket_name       = "dd5a29-test-tsma-raw-data"
mapping_bucket_name        = "dd5a29-test-tsma-ngta-mapping"
price_books_bucket_name    = "dd5a29-test-tsma-ngta-price-books"
glue_assets_bucket_name    = "dd5a29-test-glue-assets"

glue_catalog_database_name   = "dd5a29_test_dmp"
glue_job_ngta_ingestion_name = "dd5a29-test-ngta-ingestion"
lambda_tsma_fact_name        = "dd5a29-test-tsma-fact-loader"
athena_workgroup_name        = "dd5a29-test-athena"
athena_results_prefix        = "athena-results/"

assets_dir                   = "./_glue_assets"