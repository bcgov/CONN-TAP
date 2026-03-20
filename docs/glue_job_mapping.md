| S3 Bucket | Lambda | Glue Job |
|---|---|---|
| `${license}-${env}-ngta-raw-data/raw/rogers/spend_reports/` | `lambda-ngta-rogers` | `rogers_spend_ingestion` |
| `${license}-${env}-ngta-raw-data/raw/telus/spend_reports/` | `lambda-ngta-telus` | `telus_spend_ingestion` |
| `${license}-${env}-ngta-raw-data/raw/telus/quantities_reports/` | `lambda-ngta-telus-quantities` | `telus_quantities_ingestion` |
| `${license}-${env}-tsma-raw-data/raw_quarterly_spend_report/` | `lambda-tsma-qsr` | `tsma_qsr_ingestion` |
| `${license}-${env}-tsma-raw-data (wls/,wln) (1)` | `lambda-tsma-fact (no auto trigger)` | `tsma-fact` |
| `tsma-raw-data` | `Manual` | `move_tsma_files` |
| `tsma-ngta-price-books` | `Manual` | `load-ngta-rogers-pricebook-notebook` |
| `tsma-ngta-mapping; tsma-ngta-price-books` | `Manual` | `load-tsma-pricebook-notebook` |
| `tsma-raw-data` | `Manual` | `tsma-service-dashboard-data` |
| `Glue Data Catalog (S3-backed; bucket_name placeholder)` | `Manual` | `load-ngta-telus-pricebook-notebook` |
| `Glue Data Catalog (S3-backed; bucket_name placeholder)` | `Manual` | `mapping-to-master` |
| `Glue Data Catalog (S3-backed; bucket_name placeholder)` | `Manual` | `ngta-rogers-fact` |
| `Glue Data Catalog (S3-backed; bucket_name placeholder)` | `Manual` | `ngta-telus-fact` |

(1) The the Lambda function does not have a trigger, but starts `tsma-fact` glue job, which reads from the source specified on the table above.