
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame
from pyspark.sql.functions import lit
from pyspark.sql import functions as F
from pyspark.sql.functions import trim, regexp_replace
from pyspark.sql.functions import col, when

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
# Script generated for node Voice - Amazon S3
voice_raw = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-ngta-price-books/ngta-price-books/ngta-rogers-price-books/ngta_rogers_pricebook_v.csv"]})

# Script generated for node Cellular - Amazon S
cellular_raw = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-ngta-price-books/ngta-price-books/ngta-rogers-price-books/ngta_rogers_pricebook_c.csv"]})

# Script generated for node Data - Amazon S3
data_raw = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-ngta-price-books/ngta-price-books/ngta-rogers-price-books/ngta_rogers_pricebook_d.csv"]})

# Script generated for node Voice - Change Schema
voice_raw = ApplyMapping.apply(frame=voice_raw, mappings=[("service id", "string", "service_id", "string"), ("service name", "string", "service_name", "string"), ("service component", "string", "service_component", "string"), ("monthly fixed fee", "string", "monthly_fixed_fee", "string"), ("cpm rate", "string", "cpm_rate", "string"), ("ecf rate", "string", "ecf_rate", "string"), ("terminating country", "string", "terminating_country", "string")])

# Script generated for node Cellular - Change Schema
cellular_raw = ApplyMapping.apply(frame=cellular_raw, mappings=[("service id", "string", "service_id", "string"), ("service name", "string", "service_name", "string"), ("service component", "string", "service_component", "string"), ("speed mbps or capacity mb", "string", "speed_mbps_or_capacity_mb", "string"), ("monthly fixed fee", "string", "monthly_fixed_fee", "string"), ("ecf rate", "string", "ecf_rate", "string"), ("`rlh (roam like home) usa overage fee`", "string", "rlh_roam_like_home_usa_overage_fee", "string"), ("`rlh (roam like home) intl overage fee`", "string", "rlh_roam_like_home_intl_overage_fee", "string")])

# Script generated for node Data - Change Schema
data_raw = ApplyMapping.apply(frame=data_raw, mappings=[("service id", "string", "service_id", "string"), ("service name", "string", "service_name", "string"), ("service component", "string", "service_component", "string"), ("speed mbps or capacity mb", "string", "speed_mbps_or_capacity_mb", "string"), ("monthly fixed fee", "string", "monthly_fixed_fee", "string"), ("ecf rate", "string", "ecf_rate", "string")])
voice_raw_spark_df = voice_raw.toDF()
cellular_raw_spark_df = cellular_raw.toDF()
data_raw_spark_df = data_raw.toDF()
data_raw_spark_df.count()
voice_raw_spark_df_transformed = voice_raw_spark_df.select(
    "service_id",
    "service_name",
    "service_component",
    F.lit(None).cast("string").alias("speed_mbps_or_capacity_mb"),
    "monthly_fixed_fee",
    "ecf_rate",
    F.lit(None).cast("string").alias("rlh_roam_like_home_usa_overage_fee"),
    F.lit(None).cast("string").alias("rlh_roam_like_home_intl_overage_fee"),
    "cpm_rate",
    "terminating_country",
    F.lit("Voice").alias("service_category")
)



cellular_raw_spark_df_transformed = cellular_raw_spark_df.select(
    "service_id",
    "service_name",
    "service_component",
    "speed_mbps_or_capacity_mb",
    "monthly_fixed_fee",
    "ecf_rate",
    "rlh_roam_like_home_usa_overage_fee",
    "rlh_roam_like_home_intl_overage_fee",
    F.lit(None).cast("string").alias("cpm_rate"),
    F.lit(None).cast("string").alias("terminating_country"),
    F.lit("Cellular").alias("service_category")
)



data_raw_spark_df_transformed = data_raw_spark_df.select(
    "service_id",
    "service_name",
    "service_component",
   "speed_mbps_or_capacity_mb",
    "monthly_fixed_fee",
    "ecf_rate",
    F.lit(None).cast("string").alias("rlh_roam_like_home_usa_overage_fee"),
    F.lit(None).cast("string").alias("rlh_roam_like_home_intl_overage_fee"),
    F.lit(None).cast("string").alias("cpm_rate"),
    F.lit(None).cast("string").alias("terminating_country"),
    F.lit("Data").alias("service_category")
)

combined_df = voice_raw_spark_df_transformed.union(cellular_raw_spark_df_transformed).union(data_raw_spark_df_transformed)
combined_df.count()
final_combined_df = combined_df.select(
    # trim(F.col("service_id")).alias("service_id"),
    trim(
        regexp_replace(col("service_id"), "[\u0000-\u001F\u007F\u00A0]", "")  # Removes invisible & non-breaking spaces
    ).alias("service_id"),
    F.col("service_component").alias("short_service_description"),
    "service_category",
    "service_name",
    F.col("monthly_fixed_fee").alias("monthly_fee"),
    "ecf_rate",
    F.lit(None).cast("string").alias("service_sla"),
    F.lit(None).cast("string").alias("technical_service_support"),
    F.lit(None).cast("string").alias("ordering_lead_time_objectives"),
    F.lit(None).cast("string").alias("delivery_lead_time_objectives_service_interval"),
    F.lit(None).cast("string").alias("technical_service_standards"),
    "speed_mbps_or_capacity_mb",
    "rlh_roam_like_home_usa_overage_fee",
    "rlh_roam_like_home_intl_overage_fee",
    "cpm_rate",
    "terminating_country",
    F.lit("NGTA").alias("agreement"),
    F.lit("ROGERS").alias("vendor"),
    F.lit(None).cast("string").alias("tsma_service_tower")
    # F.lit(None).cast("string").alias("monthly_fee_alt")
)

# final_combined_df.filter(final_combined_df.service_id == 'AV_F_GM').show()
# final_combined_df.show()
#REPLACE BLANKS WITH NULL
final_combined_df = final_combined_df.select([when(col(c) == "", None).otherwise(col(c)).alias(c) for c in final_combined_df.columns])

#REMOVE NULL SERVICE ID's
final_combined_df = final_combined_df.dropna(subset=["service_id"])

#DROP DUPLICATES
final_df_drop_dup = final_combined_df.dropDuplicates(["service_id"])
final_df_drop_dup.count()

# final_df_drop_dup.show()
dynamic_frame = DynamicFrame.fromDF(final_df_drop_dup, glueContext, "dynamic_frame")
glueContext.write_dynamic_frame.from_options(
    frame=dynamic_frame,
    connection_type="redshift",
    connection_options={
        "postactions": """
            BEGIN;
            MERGE INTO clean_data.tsma_ngta_price_book
            USING clean_data.tsma_ngta_rogers_pricebook_temp
            ON tsma_ngta_price_book.service_id = tsma_ngta_rogers_pricebook_temp.service_id
            AND tsma_ngta_price_book.short_service_description = tsma_ngta_rogers_pricebook_temp.short_service_description
            WHEN MATCHED THEN
                UPDATE SET
                    service_id = tsma_ngta_rogers_pricebook_temp.service_id,
                    short_service_description = tsma_ngta_rogers_pricebook_temp.short_service_description,
                    service_category = tsma_ngta_rogers_pricebook_temp.service_category,
                    service_name = tsma_ngta_rogers_pricebook_temp.service_name,
                    monthly_fee = tsma_ngta_rogers_pricebook_temp.monthly_fee,
                    ecf_rate = tsma_ngta_rogers_pricebook_temp.ecf_rate,
                    service_sla = tsma_ngta_rogers_pricebook_temp.service_sla,
                    technical_service_support = tsma_ngta_rogers_pricebook_temp.technical_service_support,
                    ordering_lead_time_objectives = tsma_ngta_rogers_pricebook_temp.ordering_lead_time_objectives,
                    delivery_lead_time_objectives_service_interval = tsma_ngta_rogers_pricebook_temp.delivery_lead_time_objectives_service_interval,
                    technical_service_standards = tsma_ngta_rogers_pricebook_temp.technical_service_standards,
                    speed_mbps_or_capacity_mb = tsma_ngta_rogers_pricebook_temp.speed_mbps_or_capacity_mb,
                    rlh_roam_like_home_usa_overage_fee = tsma_ngta_rogers_pricebook_temp.rlh_roam_like_home_usa_overage_fee,
                    rlh_roam_like_home_intl_overage_fee = tsma_ngta_rogers_pricebook_temp.rlh_roam_like_home_intl_overage_fee,
                    cpm_rate = tsma_ngta_rogers_pricebook_temp.cpm_rate,
                    terminating_country = tsma_ngta_rogers_pricebook_temp.terminating_country,
                    agreement = tsma_ngta_rogers_pricebook_temp.agreement,
                    vendor = tsma_ngta_rogers_pricebook_temp.vendor,
                    tsma_service_tower = tsma_ngta_rogers_pricebook_temp.tsma_service_tower
            WHEN NOT MATCHED THEN
                INSERT (
                    service_id,
                    short_service_description,
                    service_category,
                    service_name,
                    monthly_fee,
                    ecf_rate,
                    service_sla,
                    technical_service_support,
                    ordering_lead_time_objectives,
                    delivery_lead_time_objectives_service_interval,
                    technical_service_standards,
                    speed_mbps_or_capacity_mb,
                    rlh_roam_like_home_usa_overage_fee,
                    rlh_roam_like_home_intl_overage_fee,
                    cpm_rate,
                    terminating_country,
                    agreement,
                    vendor,
                    tsma_service_tower
                ) VALUES(
                    tsma_ngta_rogers_pricebook_temp.service_id,
                    tsma_ngta_rogers_pricebook_temp.short_service_description,
                    tsma_ngta_rogers_pricebook_temp.service_category,
                    tsma_ngta_rogers_pricebook_temp.service_name,
                    tsma_ngta_rogers_pricebook_temp.monthly_fee,
                    tsma_ngta_rogers_pricebook_temp.ecf_rate,
                    tsma_ngta_rogers_pricebook_temp.service_sla,
                    tsma_ngta_rogers_pricebook_temp.technical_service_support,
                    tsma_ngta_rogers_pricebook_temp.ordering_lead_time_objectives,
                    tsma_ngta_rogers_pricebook_temp.delivery_lead_time_objectives_service_interval,
                    tsma_ngta_rogers_pricebook_temp.technical_service_standards,
                    tsma_ngta_rogers_pricebook_temp.speed_mbps_or_capacity_mb,
                    tsma_ngta_rogers_pricebook_temp.rlh_roam_like_home_usa_overage_fee,
                    tsma_ngta_rogers_pricebook_temp.rlh_roam_like_home_intl_overage_fee,
                    tsma_ngta_rogers_pricebook_temp.cpm_rate,
                    tsma_ngta_rogers_pricebook_temp.terminating_country,
                    tsma_ngta_rogers_pricebook_temp.agreement,
                    tsma_ngta_rogers_pricebook_temp.vendor,
                    tsma_ngta_rogers_pricebook_temp.tsma_service_tower
                );
            DROP TABLE clean_data.tsma_ngta_rogers_pricebook_temp;
            END;
        """,
        "redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/",
        "useConnectionProperties": "true",
        "dbtable": "clean_data.tsma_ngta_rogers_pricebook_temp",
        "connectionName": "app-glue-data-redshift-connection5",
        "preactions": """
            CREATE TABLE IF NOT EXISTS clean_data.tsma_ngta_price_book (
                service_id VARCHAR,
                short_service_description VARCHAR,
                service_category VARCHAR,
                service_name VARCHAR,
                monthly_fee VARCHAR,
                ecf_rate VARCHAR,
                service_sla VARCHAR,
                technical_service_support VARCHAR,
                ordering_lead_time_objectives VARCHAR,
                delivery_lead_time_objectives_service_interval VARCHAR,
                technical_service_standards VARCHAR,
                speed_mbps_or_capacity_mb VARCHAR,
                rlh_roam_like_home_usa_overage_fee VARCHAR,
                rlh_roam_like_home_intl_overage_fee VARCHAR,
                cpm_rate VARCHAR,
                terminating_country VARCHAR,
                agreement VARCHAR,
                vendor VARCHAR,
                tsma_service_tower VARCHAR
            );
            DROP TABLE IF EXISTS clean_data.tsma_ngta_rogers_pricebook_temp;
            CREATE TABLE clean_data.tsma_ngta_rogers_pricebook_temp (
                service_id VARCHAR,
                short_service_description VARCHAR,
                service_category VARCHAR,
                service_name VARCHAR,
                monthly_fee VARCHAR,
                ecf_rate VARCHAR,
                service_sla VARCHAR,
                technical_service_support VARCHAR(5000),
                ordering_lead_time_objectives VARCHAR(5000),
                delivery_lead_time_objectives_service_interval VARCHAR(5000),
                technical_service_standards VARCHAR(5000),
                speed_mbps_or_capacity_mb VARCHAR,
                rlh_roam_like_home_usa_overage_fee VARCHAR,
                rlh_roam_like_home_intl_overage_fee VARCHAR,
                cpm_rate VARCHAR,
                terminating_country VARCHAR,
                agreement VARCHAR,
                vendor VARCHAR,
                tsma_service_tower VARCHAR
            );
        """,
    }
)

job.commit()