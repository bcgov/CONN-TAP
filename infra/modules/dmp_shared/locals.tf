locals {
  glue_scripts = {
    "load-ngta-rogers-pricebook-notebook" = {
      key      = "scripts/load-ngta-rogers-pricebook-notebook.py"
      source   = "${var.assets_dir}/glue_scripts/load-ngta-rogers-pricebook-notebook.py"
      job_name = "load-ngta-rogers-pricebook-notebook"
    }
    "load-ngta-telus-pricebook-notebook" = {
      key      = "scripts/load-ngta-telus-pricebook-notebook.py"
      source   = "${var.assets_dir}/glue_scripts/load-ngta-telus-pricebook-notebook.py"
      job_name = "load-ngta-telus-pricebook-notebook"
    }
    "load-tsma-pricebook-notebook" = {
      key      = "scripts/load-tsma-pricebook-notebook.py"
      source   = "${var.assets_dir}/glue_scripts/load-tsma-pricebook-notebook.py"
      job_name = "load-tsma-pricebook-notebook"
    }
    "mapping-to-master" = {
      key      = "scripts/mapping-to-master.py"
      source   = "${var.assets_dir}/glue_scripts/mapping-to-master.py"
      job_name = "mapping-to-master"
    }
    "move_tsma_files" = {
      key      = "scripts/move_tsma_files.py"
      source   = "${var.assets_dir}/glue_scripts/move_tsma_files.py"
      job_name = "move_tsma_files"
    }
    "ngta-rogers-fact" = {
      key      = "scripts/ngta-rogers-fact.py"
      source   = "${var.assets_dir}/glue_scripts/ngta-rogers-fact.py"
      job_name = "ngta-rogers-fact"
    }
    "ngta-telus-fact" = {
      key      = "scripts/ngta-telus-fact.py"
      source   = "${var.assets_dir}/glue_scripts/ngta-telus-fact.py"
      job_name = "ngta-telus-fact"
    }
    "rogers_spend_ingestion" = {
      key      = "scripts/rogers_spend_ingestion.py"
      source   = "${var.assets_dir}/glue_scripts/rogers_spend_ingestion.py"
      job_name = "rogers_spend_ingestion"
    }
    "telus_quantities_ingestion" = {
      key      = "scripts/telus_quantities_ingestion.py"
      source   = "${var.assets_dir}/glue_scripts/telus_quantities_ingestion.py"
      job_name = "telus_quantities_ingestion"
    }
    "telus_spend_ingestion" = {
      key      = "scripts/telus_spend_ingestion.py"
      source   = "${var.assets_dir}/glue_scripts/telus_spend_ingestion.py"
      job_name = "telus_spend_ingestion"
    }
    "tsma-fact" = {
      key      = "scripts/tsma-fact.py"
      source   = "${var.assets_dir}/glue_scripts/tsma-fact.py"
      job_name = "tsma-fact"
    }
    "tsma-service-dashboard-data" = {
      key      = "scripts/tsma-service-dashboard-data.py"
      source   = "${var.assets_dir}/glue_scripts/tsma-service-dashboard-data.py"
      job_name = "tsma-service-dashboard-data"
    }
    "tsma_fact" = {
      key      = "scripts/tsma_fact.py"
      source   = "${var.assets_dir}/glue_scripts/tsma_fact.py"
      job_name = "tsma_fact"
    }
    "tsma_qsr_ingestion" = {
      key      = "scripts/tsma_qsr_ingestion.py"
      source   = "${var.assets_dir}/glue_scripts/tsma_qsr_ingestion.py"
      job_name = "tsma_qsr_ingestion"
    }
  }

}