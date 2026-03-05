import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue import DynamicFrame

def sparkSqlQuery(glueContext, query, mapping, transformation_ctx) -> DynamicFrame:
    for alias, frame in mapping.items():
        frame.toDF().createOrReplaceTempView(alias)
    result = spark.sql(query)
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)
def sparkUnion(glueContext, unionType, mapping, transformation_ctx) -> DynamicFrame:
    for alias, frame in mapping.items():
        frame.toDF().createOrReplaceTempView(alias)
    result = spark.sql("(select * from source1) UNION " + unionType + " (select * from source2)")
    return DynamicFrame.fromDF(result, glueContext, transformation_ctx)
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Script generated for node WLS - Amazon S3
WLSAmazonS3_node1739190063708 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-raw-data/wls/"], "recurse": True}, transformation_ctx="WLSAmazonS3_node1739190063708")

# Script generated for node WLN - Amazon S3
WLNAmazonS3_node1739176883852 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-raw-data/wln/"], "recurse": True}, transformation_ctx="WLNAmazonS3_node1739176883852")

# Script generated for node WLS - SQL Query
SqlQuery68 = '''
SELECT
    ban AS ban,
    `cellular telephone number` AS cellular_telephone_number,
    `cellular user equipment` AS cellular_user_equipment,
    `unit type` AS unit_type,
    retailer AS retailer,
    `retailer address` AS retailer_address,
    `retailer city` AS retailer_city,
    `retailer province` AS retailer_province,
    `retailer postal code` AS retailer_postal_code,
    status AS status,
    `gps entity` AS entity,
    `billing name 1` AS billing_name_1,
    `billing name 2` AS billing_name_2,
    `billing address 1` AS billing_address_1,
    `billing address 2` AS billing_address_2,
    `billing city` AS billing_city,
    `billing province` AS billing_province,
    `billing postal code` AS billing_postal_code,
    user AS user_new,
    `bill date` AS monthstartdt,
    `voice - weekday mins` AS voice_weekday_mins,
    `voice - evening mins` AS voice_evening_mins,
    `voice - weekend mins` AS voice_weekend_mins,
    `total voice mins` AS total_voice_mins,
    `mobile to mobile min` AS mobile_to_mobile_min,
    `can ld mins` AS can_ld_mins,
    `us/int ld mins` AS us_int_ld_mins,
    `us/int roaming mins` AS us_int_roaming_mins,
    `can data - gb used` AS can_data_gb_used,
    `us/int data roam - gb used` AS us_int_data_roam_gb_used,
    `sms messages - outgoing` AS sms_messages_outgoing,
    `system access & 911` AS system_access_911,
    `voice - monthly service fee` AS voice_monthly_service_fee,
    `voice - overage charge` AS voice_overage_charge,
    `voice - can ld charge` AS voice_can_ld_charge,
    `voice - us/int ld charge` AS voice_us_int_ld_charge,
    `voice - us/int roaming min charge` AS voice_us_int_roaming_min_charge,
    `voice directory assistance` AS voice_directory_assistance,
    `sms message overage` AS sms_message_overage,
    `voice - other charges` AS voice_other_charges,
    `voice - total charges` AS voice_total_charges,
    `data - monthly service fee` AS data_monthly_service_fee,
    `data - overage charge` AS data_overage_charge,
    `data - other charges` AS data_other_charges,
    `data - total charges` AS data_total_charges,
    `other charges & credits` AS other_charges_credits,
    `hst/pst` AS hst_pst,
    gst AS gst,
    `billed amount (before tax)` AS billedamt,
    `billed amount (after tax)` AS billed_amount_after_tax,
    -- `voice rate plan` AS voice_rate_plan,
    -- `data rate plan` AS data_rate_plan,
    'WLS' AS lob,
    CAST(NULL AS STRING) AS lcdcustcd,
    CAST(NULL AS STRING) AS billgsystemcd,
    CAST(NULL AS STRING) AS rcid,
    CAST(NULL AS STRING) AS rcid_cust_nm,
    CAST(NULL AS STRING) AS cbu_cid,
    CAST(NULL AS STRING) AS cbucid_cust_nm,
    CAST(NULL AS STRING) AS tsma_spend_ind,
    CAST(NULL AS STRING) AS dataexclusion_flg,
    CAST(NULL AS STRING) AS tsma_service_tower,
    CAST(NULL AS STRING) AS sap_mic_cd_flg,
    CAST(NULL AS STRING) AS sap_mic_cd,
    CAST(NULL AS STRING) AS bpi_prod_cd,
    CONCAT(`voice rate plan`, ' | ', `data rate plan`) AS bpi_prod_desc,
    CAST(NULL AS STRING) AS prod_family_cd,
    CAST(NULL AS STRING) AS prod_family_desc,
    CAST(NULL AS STRING) AS rn_1,
    CAST(NULL AS STRING) AS rn_2,
    CAST(NULL AS STRING) AS rn_3,
    CAST(NULL AS STRING) AS rn_4,
    CAST(NULL AS STRING) AS epp3_desc,
    CAST(NULL AS STRING) AS epp3_cd,
    '1' AS quantity,
    CAST(NULL AS STRING) AS comment
FROM table2;
'''
WLSSQLQuery_node1739256189809 = sparkSqlQuery(glueContext, query = SqlQuery68, mapping = {"table2":WLSAmazonS3_node1739190063708}, transformation_ctx = "WLSSQLQuery_node1739256189809")

# Script generated for node WLN - SQL Query
SqlQuery69 = '''
SELECT
    CAST(NULL AS STRING) AS ban,
    CAST(NULL AS STRING) AS cellular_telephone_number,
    CAST(NULL AS STRING) AS cellular_user_equipment,
    CAST(NULL AS STRING) AS unit_type,
    CAST(NULL AS STRING) AS retailer,
    CAST(NULL AS STRING) AS retailer_address,
    CAST(NULL AS STRING) AS retailer_city,
    CAST(NULL AS STRING) AS retailer_province,
    CAST(NULL AS STRING) AS retailer_postal_code,
    CAST(NULL AS STRING) AS status,
    entity,
    CAST(NULL AS STRING) AS billing_name_1,
    CAST(NULL AS STRING) AS billing_name_2,
    CAST(NULL AS STRING) AS billing_address_1,
    CAST(NULL AS STRING) AS billing_address_2,
    CAST(NULL AS STRING) AS billing_city,
    CAST(NULL AS STRING) AS billing_province,
    CAST(NULL AS STRING) AS billing_postal_code,
    CAST(NULL AS STRING) AS user_new,
CASE 
    WHEN monthstartdt = '' 
    THEN CAST(DATE_FORMAT(TO_DATE(CONCAT(CCYYMM, '01'), 'yyyyMMdd'), 'yyyy-MM-dd') AS STRING)     
    ELSE CAST(monthstartdt AS STRING) 
END AS monthstartdt,
    CAST(NULL AS STRING) AS voice_weekday_mins,
    CAST(NULL AS STRING) AS voice_evening_mins,
    CAST(NULL AS STRING) AS voice_weekend_mins,
    CAST(NULL AS STRING) AS total_voice_mins,
    CAST(NULL AS STRING) AS mobile_to_mobile_min,
    CAST(NULL AS STRING) AS can_ld_mins,
    CAST(NULL AS STRING) AS us_int_ld_mins,
    CAST(NULL AS STRING) AS us_int_roaming_mins,
    CAST(NULL AS STRING) AS can_data_gb_used,
    CAST(NULL AS STRING) AS us_int_data_roam_gb_used,
    CAST(NULL AS STRING) AS sms_messages_outgoing,
    CAST(NULL AS STRING) AS system_access_911,
    CAST(NULL AS STRING) AS voice_monthly_service_fee,
    CAST(NULL AS STRING) AS voice_overage_charge,
    CAST(NULL AS STRING) AS voice_can_ld_charge,
    CAST(NULL AS STRING) AS voice_us_int_ld_charge,
    CAST(NULL AS STRING) AS voice_us_int_roaming_min_charge,
    CAST(NULL AS STRING) AS voice_directory_assistance,
    CAST(NULL AS STRING) AS sms_message_overage,
    CAST(NULL AS STRING) AS voice_other_charges,
    CAST(NULL AS STRING) AS voice_total_charges,
    CAST(NULL AS STRING) AS data_monthly_service_fee,
    CAST(NULL AS STRING) AS data_overage_charge,
    CAST(NULL AS STRING) AS data_other_charges,
    CAST(NULL AS STRING) AS data_total_charges,
    CAST(NULL AS STRING) AS other_charges_credits,
    CAST(NULL AS STRING) AS hst_pst,
    CAST(NULL AS STRING) AS gst,
    billedamt,
    CAST(NULL AS STRING) AS billed_amount_after_tax,
    'WLN' AS lob,
    lcdcustcd AS lcdcustcd,
    billgsystemcd AS billgsystemcd,
    rcid AS rcid,
    rcid_cust_nm AS rcid_cust_nm,
    cbu_cid AS cbu_cid,
    cbucid_cust_nm AS cbucid_cust_nm,
    tsma_spend_ind AS tsma_spend_ind,
    dataexclusion_flg AS dataexclusion_flg,
    tsma_service_tower AS tsma_service_tower,
    sap_mic_cd_flg AS sap_mic_cd_flg,
    sap_mic_cd AS sap_mic_cd,
    bpi_prod_cd AS bpi_prod_cd,
    bpi_prod_desc,
    prod_family_cd AS prod_family_cd,
    prod_family_desc AS prod_family_desc,
    rn_1 AS rn_1,
    rn_2 AS rn_2,
    rn_3 AS rn_3,
    rn_4 AS rn_4,
    epp3_desc AS epp3_desc,
    epp3_cd AS epp3_cd,
    quantity AS quantity,
    comment AS comment
FROM table1;

'''
WLNSQLQuery_node1739256425995 = sparkSqlQuery(glueContext, query = SqlQuery69, mapping = {"table1":WLNAmazonS3_node1739176883852}, transformation_ctx = "WLNSQLQuery_node1739256425995")

# Script generated for node Union
Union_node1739257696911 = sparkUnion(glueContext, unionType = "ALL", mapping = {"source1": WLNSQLQuery_node1739256425995, "source2": WLSSQLQuery_node1739256189809}, transformation_ctx = "Union_node1739257696911")

# Script generated for node Amazon Redshift
AmazonRedshift_node1739272798937 = glueContext.write_dynamic_frame.from_options(frame=Union_node1739257696911, connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "raw_data.tsma_service_dashboard", "connectionName": "app-glue-data-redshift-connection5", "preactions": "CREATE TABLE IF NOT EXISTS raw_data.tsma_service_dashboard (ban VARCHAR, cellular_telephone_number VARCHAR, cellular_user_equipment VARCHAR, unit_type VARCHAR, retailer VARCHAR, retailer_address VARCHAR, retailer_city VARCHAR, retailer_province VARCHAR, retailer_postal_code VARCHAR, status VARCHAR, entity VARCHAR, billing_name_1 VARCHAR, billing_name_2 VARCHAR, billing_address_1 VARCHAR, billing_address_2 VARCHAR, billing_city VARCHAR, billing_province VARCHAR, billing_postal_code VARCHAR, user_new VARCHAR, monthstartdt VARCHAR, voice_weekday_mins VARCHAR, voice_evening_mins VARCHAR, voice_weekend_mins VARCHAR, total_voice_mins VARCHAR, mobile_to_mobile_min VARCHAR, can_ld_mins VARCHAR, us_int_ld_mins VARCHAR, us_int_roaming_mins VARCHAR, can_data_gb_used VARCHAR, us_int_data_roam_gb_used VARCHAR, sms_messages_outgoing VARCHAR, system_access_911 VARCHAR, voice_monthly_service_fee VARCHAR, voice_overage_charge VARCHAR, voice_can_ld_charge VARCHAR, voice_us_int_ld_charge VARCHAR, voice_us_int_roaming_min_charge VARCHAR, voice_directory_assistance VARCHAR, sms_message_overage VARCHAR, voice_other_charges VARCHAR, voice_total_charges VARCHAR, data_monthly_service_fee VARCHAR, data_overage_charge VARCHAR, data_other_charges VARCHAR, data_total_charges VARCHAR, other_charges_credits VARCHAR, hst_pst VARCHAR, gst VARCHAR, billedamt VARCHAR, billed_amount_after_tax VARCHAR, lob VARCHAR, lcdcustcd VARCHAR, billgsystemcd VARCHAR, rcid VARCHAR, rcid_cust_nm VARCHAR, cbu_cid VARCHAR, cbucid_cust_nm VARCHAR, tsma_spend_ind VARCHAR, dataexclusion_flg VARCHAR, tsma_service_tower VARCHAR, sap_mic_cd_flg VARCHAR, sap_mic_cd VARCHAR, bpi_prod_cd VARCHAR, bpi_prod_desc VARCHAR, prod_family_cd VARCHAR, prod_family_desc VARCHAR, rn_1 VARCHAR, rn_2 VARCHAR, rn_3 VARCHAR, rn_4 VARCHAR, epp3_desc VARCHAR, epp3_cd VARCHAR, quantity VARCHAR, comment VARCHAR); TRUNCATE TABLE raw_data.tsma_service_dashboard;"}, transformation_ctx="AmazonRedshift_node1739272798937")

job.commit()