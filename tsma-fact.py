
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
from pyspark.sql.functions import col, when, to_date, concat, substring, lit


sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
wls = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-raw-data/wls/"], "recurse": True}, transformation_ctx="WLSAmazonS3_node1739190063708")

pricebook = glueContext.create_dynamic_frame.from_options(connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "clean_data.tsma_ngta_price_book", "connectionName": "app-glue-data-redshift-connection5"}, transformation_ctx="PriceBookAmazonRedshift_node1740480132714")

entity = glueContext.create_dynamic_frame.from_options(connection_type="redshift", connection_options={"sampleQuery": "select entity_key, entity as right_entity from clean_data.entity_dim", "redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "connectionName": "app-glue-data-redshift-connection5"}, transformation_ctx="AmazonRedshift_node1739271093618")

wln = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-raw-data/wln/"], "recurse": True}, transformation_ctx="WLNAmazonS3_node1739176883852")

WLSChangeSchema = ApplyMapping.apply(frame=wls, mappings=[("ban", "string", "ban", "string"), ("cellular telephone number", "string", "cellular_telephone_number", "string"), ("cellular user equipment", "string", "cellular_user_equipment", "string"), ("unit type", "string", "unit_type", "string"), ("retailer", "string", "retailer", "string"), ("retailer address", "string", "retailer_address", "string"), ("retailer city", "string", "retailer_city", "string"), ("retailer province", "string", "retailer_province", "string"), ("retailer postal code", "string", "retailer_postal_code", "string"), ("status", "string", "status", "string"), ("gps entity", "string", "entity", "string"), ("billing name 1", "string", "rcid_cust_nm", "string"), ("billing name 2", "string", "billing_name_2", "string"), ("billing address 1", "string", "billing_address_1", "string"), ("billing address 2", "string", "billing_address_2", "string"), ("billing city", "string", "billing_city", "string"), ("billing province", "string", "billing_province", "string"), ("billing postal code", "string", "billing_postal_code", "string"), ("user", "string", "user_new", "string"), ("bill date", "string", "date", "string"), ("voice - weekday mins", "string", "voice_weekday_mins", "string"), ("voice - evening mins", "string", "voice_evening_mins", "string"), ("voice - weekend mins", "string", "voice_weekend_mins", "string"), ("total voice mins", "string", "total_voice_mins", "string"), ("mobile to mobile min", "string", "mobile_to_mobile_min", "string"), ("can ld mins", "string", "can_ld_mins", "string"), ("us/int ld mins", "string", "us_int_ld_mins", "string"), ("us/int roaming mins", "string", "us_int_roaming_mins", "string"), ("can data - gb used", "string", "can_data_gb_used", "string"), ("us/int data roam - gb used", "string", "us_int_data_roam_gb_used", "string"), ("sms messages - outgoing", "string", "sms_messages_outgoing", "string"), ("system access & 911", "string", "system_access_and_911", "string"), ("voice - monthly service fee", "string", "voice_monthly_service_fee", "string"), ("voice - overage charge", "string", "voice_overage_charge", "string"), ("voice - can ld charge", "string", "voice_can_ld_charge", "string"), ("voice - us/int ld charge", "string", "voice_us_int_ld_charge", "string"), ("voice - us/int roaming min charge", "string", "voice_us_int_roaming_min_charge", "string"), ("voice directory assistance", "string", "voice_directory_assistance", "string"), ("sms message overage", "string", "sms_message_overage", "string"), ("voice - other charges", "string", "voice_other_charges", "string"), ("voice - total charges", "string", "voice_total_charges", "string"), ("data - monthly service fee", "string", "data_monthly_service_fee", "string"), ("data - overage charge", "string", "data_overage_charge", "string"), ("data - other charges", "string", "data_other_charges", "string"), ("data - total charges", "string", "data_total_charges", "string"), ("other charges & credits", "string", "other_charges_and_credits", "string"), ("hst/pst", "string", "hst_pst", "string"), ("gst", "string", "gst", "string"), ("`billed amount (before tax)`", "string", "billed_amount_before_tax", "string"), ("`billed amount (after tax)`", "string", "billed_amount_after_tax", "string"), ("voice rate plan", "string", "voice_rate_plan", "string"), ("data rate plan", "string", "data_rate_plan", "string")], transformation_ctx="WLSChangeSchema_node1739192276010")

# PricebookJoinSelectFields = SelectFields.apply(frame=pricebook, paths=["price_book_key", "service_id"], transformation_ctx="PricebookJoinSelectFields_node1741180096784")

EntityChangeSchema = ApplyMapping.apply(frame=entity, mappings=[("entity_key", "int", "entity_key", "int"), ("right_entity", "string", "right_entity", "string")], transformation_ctx="RenamedkeysforJoin_node1739272311947")

WLNChangeSchema = ApplyMapping.apply(frame=wln, mappings=[("monthid", "string", "monthid", "string"), ("monthstartdt", "string", "monthstartdt", "string"), ("ccyymm", "string", "ccyymm", "string"), ("yearnum", "string", "yearnum", "string"), ("lob", "string", "lob", "string"), ("entity", "string", "entity", "string"), ("billgsystemcd", "string", "billgsystemcd", "string"), ("rcid", "string", "rcid", "string"), ("rcid_cust_nm", "string", "rcid_cust_nm", "string"), ("cbu_cid", "string", "cbu_cid", "string"), ("cbucid_cust_nm", "string", "cbucid_cust_nm", "string"), ("tsma_spend_ind", "string", "tsma_spend_ind", "string"), ("dataexclusion_flg", "string", "dataexclusion_flg", "string"), ("tsma_service_tower", "string", "tsma_service_tower", "string"), ("sap_mic_cd_flg", "string", "sap_mic_cd_flg", "string"), ("sap_mic_cd", "string", "sap_mic_cd", "string"), ("bpi_prod_cd", "string", "bpi_prod_cd", "string"), ("bpi_prod_desc", "string", "bpi_prod_desc", "string"), ("prod_family_cd", "string", "prod_family_cd", "string"), ("prod_family_desc", "string", "prod_family_desc", "string"), ("rn_1", "string", "rn_1", "string"), ("rn_2", "string", "rn_2", "string"), ("rn_3", "string", "rn_3", "string"), ("rn_4", "string", "rn_4", "string"), ("epp3_desc", "string", "epp3_desc", "string"), ("epp3_cd", "string", "epp3_cd", "string"), ("quantity", "string", "quantity", "int"), ("billedamt", "string", "billedamt", "string"), ("comment", "string", "comment", "string")], transformation_ctx="WLNChangeSchema_node1739178850830")

WLSChangeSchema_spark = WLSChangeSchema.toDF()
# PricebookJoinSelectFields_spark = PricebookJoinSelectFields.toDF()
EntityChangeSchema_spark = EntityChangeSchema.toDF()
WLNChangeSchema_spark = WLNChangeSchema.toDF()
#Pricebook transformation
pricebook_spark = pricebook.toDF()
pricebook_spark = pricebook_spark.filter(col("agreement") == "TSMA").select("price_book_key", "service_id")
pricebook_spark.count()
wls_df = WLSChangeSchema_spark.select(
    F.col("entity"),
     when(col("date").like("%-%-% %:%:%"), to_date(col("date")))
    .when(col("date").like("%-%-%"),
          to_date(
              concat(
                  substring(col("date"), 7, 4), lit("-"),
                  substring(col("date"), 4, 2), lit("-"),
                  substring(col("date"), 1, 2)
              ), "yyyy-MM-dd"
          )
    )
    .otherwise(None)
    .alias("date"),
    F.lit("Cellular").alias("tsma_service_tower"),
    F.lit("WLS").alias("lob"),
    F.expr("cast(replace(replace(billed_amount_before_tax, '$', ''), ',', '') as float)").alias("billedamt"),
    F.lit(None).alias("quantity"),
    "ban", "cellular_telephone_number", "cellular_user_equipment", "status", 
    "total_voice_mins", "can_ld_mins", "us_int_ld_mins", "us_int_roaming_mins", 
    "can_data_gb_used", "us_int_data_roam_gb_used", "sms_messages_outgoing", 
    "voice_monthly_service_fee", "voice_overage_charge", "voice_can_ld_charge", 
    "voice_us_int_ld_charge", "voice_us_int_roaming_min_charge", "voice_directory_assistance", 
    "sms_message_overage", "voice_other_charges", "voice_total_charges", "data_monthly_service_fee", 
    "data_overage_charge", "data_other_charges", "data_total_charges", "other_charges_and_credits", 
    "voice_rate_plan", "data_rate_plan", F.lit(None).alias("rcid"), "rcid_cust_nm", 
    F.lit(None).alias("cbu_cid"), F.lit(None).alias("cbucid_cust_nm"),
    F.concat_ws(" | ", F.col("voice_rate_plan"), F.col("data_rate_plan")).alias("bpi_prod_cd"),
    F.concat_ws(" | ", F.col("voice_rate_plan"), F.col("data_rate_plan")).alias("bpi_prod_desc"),
    F.lit(None).alias("rn_1"), F.lit(None).alias("rn_2"), F.lit(None).alias("rn_3"), F.lit(None).alias("rn_4"),
    F.lit("TSMA").alias("agreement"), F.lit("TELUS").alias("vendor"), "billing_city"
)

# Add current timestamp column
# wls_df = wls_df.withColumn("inserted_at", F.current_timestamp())
wls_df.count()
wln_df = WLNChangeSchema_spark.select(
    F.col("entity"),
    F.to_date(F.concat_ws("", F.col("CCYYMM"), F.lit("01")), "yyyyMMdd").alias("date"),
    F.col("tsma_service_tower"),
    F.lit("WLN").alias("lob"),
    F.expr("cast(replace(replace(billedamt, '$', ''), ',', '') as float)").alias("billedamt"),
    "quantity",
    F.lit(None).alias("ban"),
    F.lit(None).alias("cellular_telephone_number"),
    F.lit(None).alias("cellular_user_equipment"),
    F.lit(None).alias("status"),
    F.lit(None).alias("total_voice_mins"), F.lit(None).alias("can_ld_mins"),
    F.lit(None).alias("us_int_ld_mins"), F.lit(None).alias("us_int_roaming_mins"),
    F.lit(None).alias("can_data_gb_used"), F.lit(None).alias("us_int_data_roam_gb_used"),
    F.lit(None).alias("sms_messages_outgoing"), F.lit(None).alias("voice_monthly_service_fee"),
    F.lit(None).alias("voice_overage_charge"), F.lit(None).alias("voice_can_ld_charge"),
    F.lit(None).alias("voice_us_int_ld_charge"), F.lit(None).alias("voice_us_int_roaming_min_charge"),
    F.lit(None).alias("voice_directory_assistance"), F.lit(None).alias("sms_message_overage"),
    F.lit(None).alias("voice_other_charges"), F.lit(None).alias("voice_total_charges"),
    F.lit(None).alias("data_monthly_service_fee"), F.lit(None).alias("data_overage_charge"),
    F.lit(None).alias("data_other_charges"), F.lit(None).alias("data_total_charges"),
    F.lit(None).alias("other_charges_and_credits"), F.lit(None).alias("voice_rate_plan"),
    F.lit(None).alias("data_rate_plan"), "rcid", "rcid_cust_nm", "cbu_cid", "cbucid_cust_nm",
    "bpi_prod_cd", "bpi_prod_desc", "rn_1", "rn_2", "rn_3", "rn_4",
    F.lit("TSMA").alias("agreement"), F.lit("TELUS").alias("vendor"),
    F.lit(None).alias("billing_city")
)

# Add current timestamp column
# wln_df = wln_df.withColumn("inserted_at", F.current_timestamp())

wln_df.count()
# #Renamed keys for Pricebook - Join
# RenamedkeysforPricebookJoin = ApplyMapping.apply(frame=PricebookJoinSelectFields, mappings=[("price_book_key", "long", "price_book_key", "long"), ("service_id", "string", "service_id", "string")], transformation_ctx="RenamedkeysforPricebookJoin_node1741067662130")
# RenamedkeysforPricebookJoin = RenamedkeysforPricebookJoin.toDF()
# Perform Union
union_df = wln_df.unionByName(wls_df, allowMissingColumns=True)
# Perform Join
entity_join_df = union_df.join(EntityChangeSchema_spark, union_df["entity"] == EntityChangeSchema_spark["right_entity"], "left")
entity_join_df = entity_join_df.drop("right_entity", "entity")
# entity_join_df.count()
# #Pricebook join
# pricebook_join_df = entity_join_df.join(RenamedkeysforPricebookJoin, entity_join_df["bpi_prod_cd"] == RenamedkeysforPricebookJoin["service_id"], "left")
# pricebook_join_df.count()
# New Pricebook join
pricebook_join_df = entity_join_df.join(pricebook_spark, entity_join_df["bpi_prod_cd"] == pricebook_spark["service_id"], "left")
# pricebook_join_df.count()
pricebook_join_df = pricebook_join_df.drop("service_id")
pricebook_join_df = pricebook_join_df.select([when(col(c) == "", None).otherwise(col(c)).alias(c) for c in pricebook_join_df.columns])
tsma_fact_df = pricebook_join_df.withColumn("inserted_at", F.current_timestamp())
WLSChangeSchema_spark = WLSChangeSchema_spark.withColumn("inserted_at", F.current_timestamp())
WLNChangeSchema_spark = WLNChangeSchema_spark.withColumn("inserted_at", F.current_timestamp())
tsma_fact_df.count()
tsma_fact_df.columns
# WLSChangeSchema_spark.count()
# WLNChangeSchema_spark.count()
# tsma_fact_df.toPandas().isnull().sum()
tsma_fact_df_dynamic_frame = DynamicFrame.fromDF(tsma_fact_df, glueContext, "dynamic_frame")
WLSChangeSchema_dynamic_frame = DynamicFrame.fromDF(WLSChangeSchema_spark, glueContext, "dynamic_frame")
WLNChangeSchema_dynamic_frame = DynamicFrame.fromDF(WLNChangeSchema_spark, glueContext, "dynamic_frame")

glueContext.write_dynamic_frame.from_options(frame=WLSChangeSchema_dynamic_frame, connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "raw_data.tsma_subscriber_usage_spend", "connectionName": "app-glue-data-redshift-connection5", "preactions": "CREATE TABLE IF NOT EXISTS raw_data.tsma_subscriber_usage_spend (ban VARCHAR, cellular_telephone_number VARCHAR, cellular_user_equipment VARCHAR, unit_type VARCHAR, retailer VARCHAR, retailer_address VARCHAR, retailer_city VARCHAR, retailer_province VARCHAR, retailer_postal_code VARCHAR, status VARCHAR, entity VARCHAR, rcid_cust_nm VARCHAR, billing_name_2 VARCHAR, billing_address_1 VARCHAR, billing_address_2 VARCHAR, billing_city VARCHAR, billing_province VARCHAR, billing_postal_code VARCHAR, user_new VARCHAR, date VARCHAR, voice_weekday_mins VARCHAR, voice_evening_mins VARCHAR, voice_weekend_mins VARCHAR, total_voice_mins VARCHAR, mobile_to_mobile_min VARCHAR, can_ld_mins VARCHAR, us_int_ld_mins VARCHAR, us_int_roaming_mins VARCHAR, can_data_gb_used VARCHAR, us_int_data_roam_gb_used VARCHAR, sms_messages_outgoing VARCHAR, system_access_and_911 VARCHAR, voice_monthly_service_fee VARCHAR, voice_overage_charge VARCHAR, voice_can_ld_charge VARCHAR, voice_us_int_ld_charge VARCHAR, voice_us_int_roaming_min_charge VARCHAR, voice_directory_assistance VARCHAR, sms_message_overage VARCHAR, voice_other_charges VARCHAR, voice_total_charges VARCHAR, data_monthly_service_fee VARCHAR, data_overage_charge VARCHAR, data_other_charges VARCHAR, data_total_charges VARCHAR, other_charges_and_credits VARCHAR, hst_pst VARCHAR, gst VARCHAR, billed_amount_before_tax VARCHAR, billed_amount_after_tax VARCHAR, voice_rate_plan VARCHAR, data_rate_plan VARCHAR, inserted_at TIMESTAMP);"})

glueContext.write_dynamic_frame.from_options(frame=WLNChangeSchema_dynamic_frame, connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "raw_data.tsma_qsr_d_v", "connectionName": "app-glue-data-redshift-connection5", "preactions": "CREATE TABLE IF NOT EXISTS raw_data.tsma_qsr_d_v (monthid VARCHAR, monthstartdt VARCHAR, ccyymm VARCHAR, yearnum VARCHAR, lob VARCHAR, entity VARCHAR, billgsystemcd VARCHAR, rcid VARCHAR, rcid_cust_nm VARCHAR, cbu_cid VARCHAR, cbucid_cust_nm VARCHAR, tsma_spend_ind VARCHAR, dataexclusion_flg VARCHAR, tsma_service_tower VARCHAR, sap_mic_cd_flg VARCHAR, sap_mic_cd VARCHAR, bpi_prod_cd VARCHAR, bpi_prod_desc VARCHAR, prod_family_cd VARCHAR, prod_family_desc VARCHAR, rn_1 VARCHAR, rn_2 VARCHAR, rn_3 VARCHAR, rn_4 VARCHAR, epp3_desc VARCHAR, epp3_cd VARCHAR, quantity INTEGER, billedamt VARCHAR, comment VARCHAR, inserted_at TIMESTAMP);"})

glueContext.write_dynamic_frame.from_options(frame=tsma_fact_df_dynamic_frame, connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "clean_data.tsma_fact", "connectionName": "app-glue-data-redshift-connection5", "preactions": "CREATE TABLE IF NOT EXISTS clean_data.tsma_fact (date DATE, tsma_service_tower VARCHAR, lob VARCHAR, billedamt REAL, quantity INTEGER, ban VARCHAR, cellular_telephone_number VARCHAR, cellular_user_equipment VARCHAR, status VARCHAR, total_voice_mins VARCHAR, can_ld_mins VARCHAR, us_int_ld_mins VARCHAR, us_int_roaming_mins VARCHAR, can_data_gb_used VARCHAR, us_int_data_roam_gb_used VARCHAR, sms_messages_outgoing VARCHAR, voice_monthly_service_fee VARCHAR, voice_overage_charge VARCHAR, voice_can_ld_charge VARCHAR, voice_us_int_ld_charge VARCHAR, voice_us_int_roaming_min_charge VARCHAR, voice_directory_assistance VARCHAR, sms_message_overage VARCHAR, voice_other_charges VARCHAR, voice_total_charges VARCHAR, data_monthly_service_fee VARCHAR, data_overage_charge VARCHAR, data_other_charges VARCHAR, data_total_charges VARCHAR, other_charges_and_credits VARCHAR, voice_rate_plan VARCHAR, data_rate_plan VARCHAR, rcid VARCHAR, rcid_cust_nm VARCHAR, cbu_cid VARCHAR, cbucid_cust_nm VARCHAR, bpi_prod_cd VARCHAR, bpi_prod_desc VARCHAR, rn_1 VARCHAR, rn_2 VARCHAR, rn_3 VARCHAR, rn_4 VARCHAR, agreement VARCHAR, vendor VARCHAR, billing_city VARCHAR, entity_key INTEGER, price_book_key VARCHAR, inserted_at TIMESTAMP);"})

import boto3

# Initialize S3 client
s3 = boto3.client('s3')

def move_s3_files(source_bucket, source_prefix, destination_prefix):
    """
    Moves all files from source_prefix to destination_prefix in the same S3 bucket.
    Deletes the files after copying, but keeps an empty placeholder file to retain the folder.
    """
    print(f"Processing folder: {source_prefix} -> {destination_prefix}")

    # List objects in the source prefix
    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)

    if 'Contents' in response:
        objects_to_delete = []

        for obj in response['Contents']:
            source_key = obj['Key']
            destination_key = destination_prefix + source_key[len(source_prefix):]

            # Copy the object to the new location
            s3.copy_object(
                Bucket=source_bucket,
                CopySource={'Bucket': source_bucket, 'Key': source_key},
                Key=destination_key
            )

            # Add the object to the delete list
            objects_to_delete.append({'Key': source_key})

        # Batch delete files after copying
        if objects_to_delete:
            s3.delete_objects(Bucket=source_bucket, Delete={'Objects': objects_to_delete})
            print(f"Moved and deleted {len(objects_to_delete)} files from {source_prefix}.")

        # Create a placeholder file to keep the folder
        placeholder_key = source_prefix + ".keep"
        s3.put_object(Bucket=source_bucket, Key=placeholder_key, Body=b'')
        print(f"Placeholder file added: {placeholder_key}")

    else:
        print(f"No files found in {source_prefix}.")

    print(f"Successfully moved all files from {source_prefix} to {destination_prefix}.\n")

# Set parameters
source_bucket = "tsma-raw-data"
folders = ["wln/","wls/"]  # Add more folders if needed
destination_prefixes = ["archive/wln/","archive/wls/"]

# Execute the function for each folder
for source_prefix, destination_prefix in zip(folders, destination_prefixes):
    move_s3_files(source_bucket, source_prefix, destination_prefix)

job.commit()