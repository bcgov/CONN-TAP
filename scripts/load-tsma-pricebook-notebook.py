import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame
from pyspark.sql.functions import lit

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
# PriceBookAmazonRedshift_node1740480132714 = glueContext.create_dynamic_frame.from_options(connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "clean_data.tsma_ngta_price_book", "connectionName": "app-glue-data-redshift-connection5"}, transformation_ctx="PriceBookAmazonRedshift_node1740480132714")
#Read mapping file data for TSMA
data = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-ngta-mapping/mapping/data_services.csv"]})

cellular = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-ngta-mapping/mapping/cellular_services.csv"], "recurse": True})

voice = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-ngta-mapping/mapping/voice_services.csv"]})
data_spark = data.toDF()
cellular_spark = cellular.toDF()
voice_spark = voice.toDF()
from pyspark.sql.functions import concat_ws, lit

cellular_spark = cellular_spark.select(
    concat_ws(" | ", "TSMA Voice Rate Plan", "TSMA Data Rate Plan").alias("TSMA_BPI_PROD_CD"),
    concat_ws(" | ", "TSMA Voice Rate Plan", "TSMA Data Rate Plan").alias("TSMA_BPI_PROD_DESC")
)
from pyspark.sql.functions import col

tsma_services = data_spark.select("TSMA_BPI_PROD_CD","TSMA_BPI_PROD_DESC").union(
    voice_spark.select("TSMA_BPI_PROD_CD","TSMA_BPI_PROD_DESC")).union(
    cellular_spark.select("TSMA_BPI_PROD_CD", "TSMA_BPI_PROD_DESC"))

tsma_services = tsma_services.select(
    col("TSMA_BPI_PROD_CD").alias("service_id"),
    col("TSMA_BPI_PROD_DESC").alias("short_service_description")
)
from pyspark.sql.functions import col, when
tsma_services = tsma_services.select([when(col(c) == "", None).otherwise(col(c)).alias(c) for c in tsma_services.columns])

#REMOVE NULL VALUES
tsma_services = tsma_services.dropna(subset=["service_id"])

tsma_services_drop_dup = tsma_services.drop_duplicates(subset=["service_id"])
tsma_services_drop_dup.count()
tsma_services_drop_dup.show()
#TSMA PB Data Voice
from pyspark.sql import functions as F

tsma_pb_raw = glueContext.create_dynamic_frame.from_options(
    format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, 
    connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-ngta-price-books/tsma-price-books/tsma_pricebook.csv"], "recurse": True}, 
    transformation_ctx="tsma_pb_raw")

tsma_pb_spark_df = tsma_pb_raw.toDF()

tsma_pb_transformed = tsma_pb_spark_df.select(
    F.col("bpi code").alias("service_id"),
    F.coalesce(F.col("`Avg. CY 12 22/23`"), F.col("`Avg. CY 11 21/22`")).alias("monthly_fee"),  # Fill missing values
    F.col("tsma service tower").alias("tsma_service_tower")
)
# tsma_pb_transformed.show()
#This file is made by Onpoint team and approved by BC
tsma_pb_cellular_raw = glueContext.create_dynamic_frame.from_options(
    format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, 
    connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-ngta-price-books/tsma-price-books/TSMA_Cellular_Pricebook.csv"], "recurse": True})

tsma_pb_cellular_spark_df = tsma_pb_cellular_raw.toDF()

from pyspark.sql.functions import lit
tsma_pb_cellular_transformed = tsma_pb_cellular_spark_df.select(
    F.col("`TSMA Voice Rate Plan | TSMA Data Rate Plan`").alias("service_id"),
    F.col("Monthly Fee").alias("monthly_fee"),
    lit("Cellular").alias("tsma_service_tower")  # Adding a constant column
)

# tsma_pb_cellular_transformed.show()
tsma_pb_transformed.count()
# tsma_pb_cellular_transformed.count()
tsma_pb = tsma_pb_transformed.union(tsma_pb_cellular_transformed)
from pyspark.sql.functions import col, when
tsma_pb = tsma_pb.select([when(col(c) == "", None).otherwise(col(c)).alias(c) for c in tsma_pb.columns])

#REMOVE NULL VALUES
tsma_pb = tsma_pb.dropna(subset=["service_id"])

tsma_pb_drop_dup = tsma_pb.drop_duplicates(subset=["service_id"])
tsma_pb_drop_dup.count()
tsma_final_df = tsma_services_drop_dup.join(
    tsma_pb_drop_dup,
    on="service_id",
    how="left"
)
tsma_final_df.toPandas().isnull().sum()
tsma_final_df.toPandas()['tsma_service_tower'].value_counts()
tsma_final_df.show()
from pyspark.sql import functions as F

tsma_final_df_transformed = tsma_final_df.select(
    F.col("service_id").alias("service_id"),
    F.col("short_service_description").alias("short_service_description"),
    F.lit(None).cast("string").alias("service_category"),
    F.lit(None).cast("string").alias("service_name"),
    F.col("monthly_fee"),
    F.lit(None).cast("string").alias("ecf_rate"),
    F.lit(None).cast("string").alias("service_sla"),
    F.lit(None).cast("string").alias("technical_service_support"),
    F.lit(None).cast("string").alias("ordering_lead_time_objectives"),
    F.lit(None).cast("string").alias("delivery_lead_time_objectives_service_interval"),
    F.lit(None).cast("string").alias("technical_service_standards"),
    F.lit(None).cast("string").alias("speed_mbps_or_capacity_mb"),
    F.lit(None).cast("string").alias("rlh_roam_like_home_usa_overage_fee"),
    F.lit(None).cast("string").alias("rlh_roam_like_home_intl_overage_fee"),
    F.lit(None).cast("string").alias("cpm_rate"),
    F.lit(None).cast("string").alias("terminating_country"),
    F.lit("TSMA").alias("agreement"),
    F.lit("TELUS").alias("vendor"),
    F.col("tsma_service_tower")
)
tsma_final_df_transformed.count()
# tsma_transformed.count()
# from pyspark.sql.functions import when, col

# # Assuming your DataFrame is called df
# tsma_drop_dup = tsma_drop_dup.withColumn("service_id", 
#                    when(col("service_id") == "1000M", "TEST")
#                    .otherwise(col("service_id")))

# # df.show()
# tsma_drop_dup.filter(col('service_id') == 'TEST').show()

dynamic_frame = DynamicFrame.fromDF(tsma_final_df_transformed, glueContext, "dynamic_frame")
glueContext.write_dynamic_frame.from_options(
    frame=dynamic_frame,
    connection_type="redshift",
    connection_options={
        "postactions": """
            BEGIN;
            MERGE INTO clean_data.tsma_ngta_price_book
            USING clean_data.tsma_ngta_price_book_temp_tsma
            ON tsma_ngta_price_book.service_id = tsma_ngta_price_book_temp_tsma.service_id
            AND tsma_ngta_price_book.short_service_description = tsma_ngta_price_book_temp_tsma.short_service_description
            WHEN MATCHED THEN
                UPDATE SET
                    service_id = tsma_ngta_price_book_temp_tsma.service_id,
                    short_service_description = tsma_ngta_price_book_temp_tsma.short_service_description,
                    service_category = tsma_ngta_price_book_temp_tsma.service_category,
                    service_name = tsma_ngta_price_book_temp_tsma.service_name,
                    monthly_fee = tsma_ngta_price_book_temp_tsma.monthly_fee,
                    ecf_rate = tsma_ngta_price_book_temp_tsma.ecf_rate,
                    service_sla = tsma_ngta_price_book_temp_tsma.service_sla,
                    technical_service_support = tsma_ngta_price_book_temp_tsma.technical_service_support,
                    ordering_lead_time_objectives = tsma_ngta_price_book_temp_tsma.ordering_lead_time_objectives,
                    delivery_lead_time_objectives_service_interval = tsma_ngta_price_book_temp_tsma.delivery_lead_time_objectives_service_interval,
                    technical_service_standards = tsma_ngta_price_book_temp_tsma.technical_service_standards,
                    speed_mbps_or_capacity_mb = tsma_ngta_price_book_temp_tsma.speed_mbps_or_capacity_mb,
                    rlh_roam_like_home_usa_overage_fee = tsma_ngta_price_book_temp_tsma.rlh_roam_like_home_usa_overage_fee,
                    rlh_roam_like_home_intl_overage_fee = tsma_ngta_price_book_temp_tsma.rlh_roam_like_home_intl_overage_fee,
                    cpm_rate = tsma_ngta_price_book_temp_tsma.cpm_rate,
                    terminating_country = tsma_ngta_price_book_temp_tsma.terminating_country,
                    agreement = tsma_ngta_price_book_temp_tsma.agreement,
                    vendor = tsma_ngta_price_book_temp_tsma.vendor,
                    tsma_service_tower = tsma_ngta_price_book_temp_tsma.tsma_service_tower
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
                    tsma_ngta_price_book_temp_tsma.service_id,
                    tsma_ngta_price_book_temp_tsma.short_service_description,
                    tsma_ngta_price_book_temp_tsma.service_category,
                    tsma_ngta_price_book_temp_tsma.service_name,
                    tsma_ngta_price_book_temp_tsma.monthly_fee,
                    tsma_ngta_price_book_temp_tsma.ecf_rate,
                    tsma_ngta_price_book_temp_tsma.service_sla,
                    tsma_ngta_price_book_temp_tsma.technical_service_support,
                    tsma_ngta_price_book_temp_tsma.ordering_lead_time_objectives,
                    tsma_ngta_price_book_temp_tsma.delivery_lead_time_objectives_service_interval,
                    tsma_ngta_price_book_temp_tsma.technical_service_standards,
                    tsma_ngta_price_book_temp_tsma.speed_mbps_or_capacity_mb,
                    tsma_ngta_price_book_temp_tsma.rlh_roam_like_home_usa_overage_fee,
                    tsma_ngta_price_book_temp_tsma.rlh_roam_like_home_intl_overage_fee,
                    tsma_ngta_price_book_temp_tsma.cpm_rate,
                    tsma_ngta_price_book_temp_tsma.terminating_country,
                    tsma_ngta_price_book_temp_tsma.agreement,
                    tsma_ngta_price_book_temp_tsma.vendor,
                    tsma_ngta_price_book_temp_tsma.tsma_service_tower
                );
            DROP TABLE clean_data.tsma_ngta_price_book_temp_tsma;
            END;
        """,
        "redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/",
        "useConnectionProperties": "true",
        "dbtable": "clean_data.tsma_ngta_price_book_temp_tsma",
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
            DROP TABLE IF EXISTS clean_data.tsma_ngta_price_book_temp_tsma;
            CREATE TABLE clean_data.tsma_ngta_price_book_temp_tsma (
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
        """,
    }
)
job.commit()