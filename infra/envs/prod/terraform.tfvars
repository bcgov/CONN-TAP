aws_region = "ca-central-1"

licence = "dd5a29"
env     = "prod"

vpc_name        = "Prod"
ec2_subnet_name = "Prod-App-A"

ec2_security_group_names = [
  "App",
  "Data"
]

powerbi_key_name      = "dmp-powerbi-prod"
ec2_public_key        = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCwdZN3D8GY51HG3bFW9aRgzJDoXjbLLgwvhrO/0z1NSSAvGkBtXhkAasz18ZhDci8FTchQCtjbhb/Y9T0TeoFIsGYuhFwec1/iFZ5WODW3u7RWeVcgHUnLdJXcn984H0ayy5Ru89fEXsFwQqGA9iHsaaKtZ8wBLuCrAT+ygE5edy88Z1KRoquiEbtv6VF8OUn43IiAibL7okumKLGNGGfBZ5c9A3k3zUyhfZav561Ypr8QQS2z0nZuqYw3gfgFeZQPUqYAUDAPiRUXcKl6oGf1AYNftD4JE1Rve4ZL3rqZtx9Wqd4f+h/905liqTQgJRbdfYTnEoElFE8f8B4PRD8P52dgl3NB+5CdTPl6sNXmuNkOcoVdeUuCSS2Vt9gsZ7tAqJ9RaCPCL+gpOmQDQWIRI0W1+dtM0WjptqMJtvSIgvg3DSMEouyHlkXngd6pDVIh56kqquZsMT1SJ+XjN4iUcLIPB4ool2SePgBrx1EnBAgmyhUFDtXpzSt62EveJuWQe+tPclcOmLYd1t9nsoOTQda5qs9nyn/zaj+KplD8eb7cfhzrI5jSx6jKp01U7d643+jf9linMO9RpGFpgzh0j5GIH6lPrXBfS3EIRLNbb1FSh5H7DpFw7z0HhGCmP8c/lw0T8AbQS3PyfE0vpeUYPZpNvvq8fWwnL4+5yNKIdw== dmp-powerbi-prod"
powerbi_ami_id        = "ami-067abc25c5d2e14af"
powerbi_instance_type = "t3.large"
powerbi_instance_name = "ec2-powerbi-desktop-837925920977"

enable_redshift    = false
enable_tsma_lambda = true

ngta_raw_bucket_name    = "dd5a29-prod-ngta-raw-data"
tsma_raw_bucket_name    = "dd5a29-prod-tsma-raw-data"
mapping_bucket_name     = "dd5a29-prod-tsma-ngta-mapping"
price_books_bucket_name = "dd5a29-prod-tsma-ngta-price-books"
glue_assets_bucket_name = "dd5a29-prod-glue-assets"

glue_catalog_database_name   = "dd5a29_prod_dmp"
glue_job_ngta_ingestion_name = "dd5a29-prod-ngta-ingestion"
lambda_tsma_fact_name        = "dd5a29-prod-tsma-fact-loader"
athena_workgroup_name        = "dd5a29-prod-athena"
athena_results_prefix        = "athena-results/"

assets_dir                   = "./_glue_assets"