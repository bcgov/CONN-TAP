import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from awsglue import DynamicFrame
import gs_now

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

# Script generated for node Price Book - Amazon Redshift
PriceBookAmazonRedshift_node1740480132714 = glueContext.create_dynamic_frame.from_options(connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "clean_data.tsma_ngta_price_book", "connectionName": "app-glue-data-redshift-connection5"}, transformation_ctx="PriceBookAmazonRedshift_node1740480132714")

# Script generated for node Amazon Redshift
AmazonRedshift_node1739271093618 = glueContext.create_dynamic_frame.from_options(connection_type="redshift", connection_options={"sampleQuery": "select entity_key, entity as right_entity from clean_data.entity_dim", "redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "connectionName": "app-glue-data-redshift-connection5"}, transformation_ctx="AmazonRedshift_node1739271093618")

# Script generated for node WLN - Amazon S3
WLNAmazonS3_node1739176883852 = glueContext.create_dynamic_frame.from_options(format_options={"quoteChar": "\"", "withHeader": True, "separator": ",", "optimizePerformance": False}, connection_type="s3", format="csv", connection_options={"paths": ["s3://tsma-raw-data/wln/"], "recurse": True}, transformation_ctx="WLNAmazonS3_node1739176883852")

# Script generated for node WLS - Change Schema
WLSChangeSchema_node1739192276010 = ApplyMapping.apply(frame=WLSAmazonS3_node1739190063708, mappings=[("ban", "string", "ban", "string"), ("cellular telephone number", "string", "cellular_telephone_number", "string"), ("cellular user equipment", "string", "cellular_user_equipment", "string"), ("unit type", "string", "unit_type", "string"), ("retailer", "string", "retailer", "string"), ("retailer address", "string", "retailer_address", "string"), ("retailer city", "string", "retailer_city", "string"), ("retailer province", "string", "retailer_province", "string"), ("retailer postal code", "string", "retailer_postal_code", "string"), ("status", "string", "status", "string"), ("gps entity", "string", "entity", "string"), ("billing name 1", "string", "rcid_cust_nm", "string"), ("billing name 2", "string", "billing_name_2", "string"), ("billing address 1", "string", "billing_address_1", "string"), ("billing address 2", "string", "billing_address_2", "string"), ("billing city", "string", "billing_city", "string"), ("billing province", "string", "billing_province", "string"), ("billing postal code", "string", "billing_postal_code", "string"), ("user", "string", "user_new", "string"), ("bill date", "string", "date", "string"), ("voice - weekday mins", "string", "voice_weekday_mins", "string"), ("voice - evening mins", "string", "voice_evening_mins", "string"), ("voice - weekend mins", "string", "voice_weekend_mins", "string"), ("total voice mins", "string", "total_voice_mins", "string"), ("mobile to mobile min", "string", "mobile_to_mobile_min", "string"), ("can ld mins", "string", "can_ld_mins", "string"), ("us/int ld mins", "string", "us_int_ld_mins", "string"), ("us/int roaming mins", "string", "us_int_roaming_mins", "string"), ("can data - gb used", "string", "can_data_gb_used", "string"), ("us/int data roam - gb used", "string", "us_int_data_roam_gb_used", "string"), ("sms messages - outgoing", "string", "sms_messages_outgoing", "string"), ("system access & 911", "string", "system_access_and_911", "string"), ("voice - monthly service fee", "string", "voice_monthly_service_fee", "string"), ("voice - overage charge", "string", "voice_overage_charge", "string"), ("voice - can ld charge", "string", "voice_can_ld_charge", "string"), ("voice - us/int ld charge", "string", "voice_us_int_ld_charge", "string"), ("voice - us/int roaming min charge", "string", "voice_us_int_roaming_min_charge", "string"), ("voice directory assistance", "string", "voice_directory_assistance", "string"), ("sms message overage", "string", "sms_message_overage", "string"), ("voice - other charges", "string", "voice_other_charges", "string"), ("voice - total charges", "string", "voice_total_charges", "string"), ("data - monthly service fee", "string", "data_monthly_service_fee", "string"), ("data - overage charge", "string", "data_overage_charge", "string"), ("data - other charges", "string", "data_other_charges", "string"), ("data - total charges", "string", "data_total_charges", "string"), ("other charges & credits", "string", "other_charges_and_credits", "string"), ("hst/pst", "string", "hst_pst", "string"), ("gst", "string", "gst", "string"), ("`billed amount (before tax)`", "string", "billed_amount_before_tax", "string"), ("`billed amount (after tax)`", "string", "billed_amount_after_tax", "string"), ("voice rate plan", "string", "voice_rate_plan", "string"), ("data rate plan", "string", "data_rate_plan", "string")], transformation_ctx="WLSChangeSchema_node1739192276010")

# Script generated for node Pricebook Join - Select Fields
PricebookJoinSelectFields_node1741180096784 = SelectFields.apply(frame=PriceBookAmazonRedshift_node1740480132714, paths=["price_book_key", "service_id"], transformation_ctx="PricebookJoinSelectFields_node1741180096784")

# Script generated for node Renamed keys for Join
RenamedkeysforJoin_node1739272311947 = ApplyMapping.apply(frame=AmazonRedshift_node1739271093618, mappings=[("entity_key", "int", "entity_key", "int"), ("right_entity", "string", "right_entity", "string")], transformation_ctx="RenamedkeysforJoin_node1739272311947")

# Script generated for node WLN - Change Schema
WLNChangeSchema_node1739178850830 = ApplyMapping.apply(frame=WLNAmazonS3_node1739176883852, mappings=[("monthid", "string", "monthid", "string"), ("monthstartdt", "string", "monthstartdt", "string"), ("ccyymm", "string", "ccyymm", "string"), ("yearnum", "string", "yearnum", "string"), ("lob", "string", "lob", "string"), ("entity", "string", "entity", "string"), ("billgsystemcd", "string", "billgsystemcd", "string"), ("rcid", "string", "rcid", "string"), ("rcid_cust_nm", "string", "rcid_cust_nm", "string"), ("cbu_cid", "string", "cbu_cid", "string"), ("cbucid_cust_nm", "string", "cbucid_cust_nm", "string"), ("tsma_spend_ind", "string", "tsma_spend_ind", "string"), ("dataexclusion_flg", "string", "dataexclusion_flg", "string"), ("tsma_service_tower", "string", "tsma_service_tower", "string"), ("sap_mic_cd_flg", "string", "sap_mic_cd_flg", "string"), ("sap_mic_cd", "string", "sap_mic_cd", "string"), ("bpi_prod_cd", "string", "bpi_prod_cd", "string"), ("bpi_prod_desc", "string", "bpi_prod_desc", "string"), ("prod_family_cd", "string", "prod_family_cd", "string"), ("prod_family_desc", "string", "prod_family_desc", "string"), ("rn_1", "string", "rn_1", "string"), ("rn_2", "string", "rn_2", "string"), ("rn_3", "string", "rn_3", "string"), ("rn_4", "string", "rn_4", "string"), ("epp3_desc", "string", "epp3_desc", "string"), ("epp3_cd", "string", "epp3_cd", "string"), ("quantity", "string", "quantity", "int"), ("billedamt", "string", "billedamt", "string"), ("comment", "string", "comment", "string")], transformation_ctx="WLNChangeSchema_node1739178850830")

# Script generated for node WLS - SQL Query
SqlQuery15 = '''
-- SELECT 'WLS' AS lob,
-- entity,
-- 'Cellular' AS tsma_service_tower,
-- CAST(NULL AS STRING) AS bpi_prod_cd,
-- CAST(NULL AS STRING) as quantity,
-- billed_amount,
-- date,
-- cellular_telephone_number,
-- voice_rate_plan,
-- data_rate_plan,
-- status
-- FROM myDataSource

SELECT
    entity,
    -- date,
    -- TO_DATE(date, 'dd-MM-yyyy') AS date, --main code
    CASE
        WHEN date LIKE '%-%-% %:%:%' THEN
            TRY_CAST(date AS DATE)
        WHEN date LIKE '%-%-%' THEN
            TRY_CAST(
                SUBSTRING(date, 7, 4) || '-' ||
                SUBSTRING(date, 4, 2) || '-' ||
                SUBSTRING(date, 1, 2) AS DATE
            )
        ELSE NULL
    END AS date,
    'Cellular' AS tsma_service_tower,
    'WLS' AS lob,
    CAST(REPLACE(REPLACE(billed_amount_before_tax, '$', ''), ',', '') AS FLOAT) AS billedamt,
    NULL AS quantity,
    ban,
    cellular_telephone_number,
    cellular_user_equipment,
    status,
    total_voice_mins,
    can_ld_mins,
    us_int_ld_mins,
    us_int_roaming_mins,
    can_data_gb_used,
    us_int_data_roam_gb_used,
    sms_messages_outgoing,
    voice_monthly_service_fee,
    voice_overage_charge,
    voice_can_ld_charge,
    voice_us_int_ld_charge,
    voice_us_int_roaming_min_charge,
    voice_directory_assistance,
    sms_message_overage,
    voice_other_charges,
    voice_total_charges,
    data_monthly_service_fee,
    data_overage_charge,
    data_other_charges,
    data_total_charges,
    other_charges_and_credits,
    voice_rate_plan,
    data_rate_plan,
    NULL AS rcid,
    rcid_cust_nm,
    NULL AS cbu_cid,
    NULL AS cbucid_cust_nm,
    CONCAT(`voice_rate_plan`, ' | ', `data_rate_plan`) AS bpi_prod_cd,
    CONCAT(`voice_rate_plan`, ' | ', `data_rate_plan`) AS bpi_prod_desc,
    NULL AS rn_1,
    NULL AS rn_2,
    NULL AS rn_3,
    NULL AS rn_4,
    'TSMA' as agreement,
    'TELUS' as vendor,
    billing_city
FROM
    myDataSource;
'''
WLSSQLQuery_node1739256189809 = sparkSqlQuery(glueContext, query = SqlQuery15, mapping = {"myDataSource":WLSChangeSchema_node1739192276010}, transformation_ctx = "WLSSQLQuery_node1739256189809")

# Script generated for node wls_raw - Add Current Timestamp
wls_rawAddCurrentTimestamp_node1742375921657 = WLSChangeSchema_node1739192276010.gs_now(colName="inserted_at")

# Script generated for node Renamed keys for Pricebook - Join
RenamedkeysforPricebookJoin_node1741067662130 = ApplyMapping.apply(frame=PricebookJoinSelectFields_node1741180096784, mappings=[("price_book_key", "long", "price_book_key", "long"), ("service_id", "string", "service_id", "string")], transformation_ctx="RenamedkeysforPricebookJoin_node1741067662130")

# Script generated for node WLN - SQL Query
SqlQuery16 = '''
-- select *,
-- CASE WHEN monthstartdt IS NULL 
-- THEN DATE_FORMAT(TO_DATE(CONCAT(CCYYMM, '01'), 'yyyyMMdd'), 'yyyy-MM-dd')      
-- ELSE monthstartdt END AS date,
-- CAST(NULL AS STRING) as cellular_telephone_number,
-- CAST(NULL AS STRING) as voice_rate_plan,
-- CAST(NULL AS STRING) as data_rate_plan,
-- CAST(NULL AS STRING) as status
-- from myDataSource

SELECT
    entity,
    TO_DATE(CONCAT(CCYYMM, '01'), 'yyyyMMdd') AS date,
    tsma_service_tower,
    'WLN' AS lob,
    CAST(REPLACE(REPLACE(billedamt, '$', ''), ',', '') AS FLOAT) AS billedamt,
    quantity,
    NULL AS ban,
    NULL AS cellular_telephone_number,
    NULL AS cellular_user_equipment,
    NULL AS status,
    NULL AS total_voice_mins,
    NULL AS can_ld_mins,
    NULL AS us_int_ld_mins,
    NULL AS us_int_roaming_mins,
    NULL AS can_data_gb_used,
    NULL AS us_int_data_roam_gb_used,
    NULL AS sms_messages_outgoing,
    NULL AS voice_monthly_service_fee,
    NULL AS voice_overage_charge,
    NULL AS voice_can_ld_charge,
    NULL AS voice_us_int_ld_charge,
    NULL AS voice_us_int_roaming_min_charge,
    NULL AS voice_directory_assistance,
    NULL AS sms_message_overage,
    NULL AS voice_other_charges,
    NULL AS voice_total_charges,
    NULL AS data_monthly_service_fee,
    NULL AS data_overage_charge,
    NULL AS data_other_charges,
    NULL AS data_total_charges,
    NULL AS other_charges_and_credits,
    NULL AS voice_rate_plan,
    NULL AS data_rate_plan,
    rcid,
    rcid_cust_nm,
    cbu_cid,
    cbucid_cust_nm,
    bpi_prod_cd,
    bpi_prod_desc,
    rn_1,
    rn_2,
    rn_3,
    rn_4,
    'TSMA' as agreement,
    'TELUS' as vendor,
    NULL as billing_city
FROM
    myDataSource;
'''
WLNSQLQuery_node1739256425995 = sparkSqlQuery(glueContext, query = SqlQuery16, mapping = {"myDataSource":WLNChangeSchema_node1739178850830}, transformation_ctx = "WLNSQLQuery_node1739256425995")

# Script generated for node wln_raw - Add Current Timestamp
wln_rawAddCurrentTimestamp_node1742375984123 = WLNChangeSchema_node1739178850830.gs_now(colName="inserted_at")

# Script generated for node Union
Union_node1739257696911 = sparkUnion(glueContext, unionType = "ALL", mapping = {"source1": WLNSQLQuery_node1739256425995, "source2": WLSSQLQuery_node1739256189809}, transformation_ctx = "Union_node1739257696911")

# Script generated for node Entity - Join
Union_node1739257696911DF = Union_node1739257696911.toDF()
RenamedkeysforJoin_node1739272311947DF = RenamedkeysforJoin_node1739272311947.toDF()
EntityJoin_node1739272211103 = DynamicFrame.fromDF(Union_node1739257696911DF.join(RenamedkeysforJoin_node1739272311947DF, (Union_node1739257696911DF['entity'] == RenamedkeysforJoin_node1739272311947DF['right_entity']), "left"), glueContext, "EntityJoin_node1739272211103")

# Script generated for node Entity Join - Drop Fields
EntityJoinDropFields_node1739272615556 = DropFields.apply(frame=EntityJoin_node1739272211103, paths=["right_entity", "entity"], transformation_ctx="EntityJoinDropFields_node1739272615556")

# Script generated for node Pricebook - Join
EntityJoinDropFields_node1739272615556DF = EntityJoinDropFields_node1739272615556.toDF()
RenamedkeysforPricebookJoin_node1741067662130DF = RenamedkeysforPricebookJoin_node1741067662130.toDF()
PricebookJoin_node1740480149680 = DynamicFrame.fromDF(EntityJoinDropFields_node1739272615556DF.join(RenamedkeysforPricebookJoin_node1741067662130DF, (EntityJoinDropFields_node1739272615556DF['bpi_prod_cd'] == RenamedkeysforPricebookJoin_node1741067662130DF['service_id']), "left"), glueContext, "PricebookJoin_node1740480149680")

# Script generated for node Pricebook Join - Drop Fields
PricebookJoinDropFields_node1741172998972 = DropFields.apply(frame=PricebookJoin_node1740480149680, paths=["right_tsma_service_tower", "right_vendor", "right_agreement", "right_short_service_description", "service_id", "right_monthly_fee"], transformation_ctx="PricebookJoinDropFields_node1741172998972")

# Script generated for node tsma_fact - Add Current Timestamp
tsma_factAddCurrentTimestamp_node1742375595434 = PricebookJoinDropFields_node1741172998972.gs_now(colName="inserted_at")

# Script generated for node WLS Raw - Amazon Redshift
WLSRawAmazonRedshift_node1742375323178 = glueContext.write_dynamic_frame.from_options(frame=wls_rawAddCurrentTimestamp_node1742375921657, connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "raw_data.tsma_subscriber_usage_spend", "connectionName": "app-glue-data-redshift-connection5", "preactions": "CREATE TABLE IF NOT EXISTS raw_data.tsma_subscriber_usage_spend (ban VARCHAR, cellular_telephone_number VARCHAR, cellular_user_equipment VARCHAR, unit_type VARCHAR, retailer VARCHAR, retailer_address VARCHAR, retailer_city VARCHAR, retailer_province VARCHAR, retailer_postal_code VARCHAR, status VARCHAR, entity VARCHAR, rcid_cust_nm VARCHAR, billing_name_2 VARCHAR, billing_address_1 VARCHAR, billing_address_2 VARCHAR, billing_city VARCHAR, billing_province VARCHAR, billing_postal_code VARCHAR, user_new VARCHAR, date VARCHAR, voice_weekday_mins VARCHAR, voice_evening_mins VARCHAR, voice_weekend_mins VARCHAR, total_voice_mins VARCHAR, mobile_to_mobile_min VARCHAR, can_ld_mins VARCHAR, us_int_ld_mins VARCHAR, us_int_roaming_mins VARCHAR, can_data_gb_used VARCHAR, us_int_data_roam_gb_used VARCHAR, sms_messages_outgoing VARCHAR, system_access_and_911 VARCHAR, voice_monthly_service_fee VARCHAR, voice_overage_charge VARCHAR, voice_can_ld_charge VARCHAR, voice_us_int_ld_charge VARCHAR, voice_us_int_roaming_min_charge VARCHAR, voice_directory_assistance VARCHAR, sms_message_overage VARCHAR, voice_other_charges VARCHAR, voice_total_charges VARCHAR, data_monthly_service_fee VARCHAR, data_overage_charge VARCHAR, data_other_charges VARCHAR, data_total_charges VARCHAR, other_charges_and_credits VARCHAR, hst_pst VARCHAR, gst VARCHAR, billed_amount_before_tax VARCHAR, billed_amount_after_tax VARCHAR, voice_rate_plan VARCHAR, data_rate_plan VARCHAR, inserted_at TIMESTAMP);"}, transformation_ctx="WLSRawAmazonRedshift_node1742375323178")

# Script generated for node Amazon Redshift
AmazonRedshift_node1742375357869 = glueContext.write_dynamic_frame.from_options(frame=wln_rawAddCurrentTimestamp_node1742375984123, connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "raw_data.tsma_qsr_d_v", "connectionName": "app-glue-data-redshift-connection5", "preactions": "CREATE TABLE IF NOT EXISTS raw_data.tsma_qsr_d_v (monthid VARCHAR, monthstartdt VARCHAR, ccyymm VARCHAR, yearnum VARCHAR, lob VARCHAR, entity VARCHAR, billgsystemcd VARCHAR, rcid VARCHAR, rcid_cust_nm VARCHAR, cbu_cid VARCHAR, cbucid_cust_nm VARCHAR, tsma_spend_ind VARCHAR, dataexclusion_flg VARCHAR, tsma_service_tower VARCHAR, sap_mic_cd_flg VARCHAR, sap_mic_cd VARCHAR, bpi_prod_cd VARCHAR, bpi_prod_desc VARCHAR, prod_family_cd VARCHAR, prod_family_desc VARCHAR, rn_1 VARCHAR, rn_2 VARCHAR, rn_3 VARCHAR, rn_4 VARCHAR, epp3_desc VARCHAR, epp3_cd VARCHAR, quantity INTEGER, billedamt VARCHAR, comment VARCHAR, inserted_at TIMESTAMP);"}, transformation_ctx="AmazonRedshift_node1742375357869")

# Script generated for node Amazon Redshift
AmazonRedshift_node1739272798937 = glueContext.write_dynamic_frame.from_options(frame=tsma_factAddCurrentTimestamp_node1742375595434, connection_type="redshift", connection_options={"redshiftTmpDir": "s3://aws-glue-assets-585768151939-ca-central-1/temporary/", "useConnectionProperties": "true", "dbtable": "clean_data.tsma_fact", "connectionName": "app-glue-data-redshift-connection5", "preactions": "CREATE TABLE IF NOT EXISTS clean_data.tsma_fact (date DATE, tsma_service_tower VARCHAR, lob VARCHAR, billedamt REAL, quantity INTEGER, ban VARCHAR, cellular_telephone_number VARCHAR, cellular_user_equipment VARCHAR, status VARCHAR, total_voice_mins VARCHAR, can_ld_mins VARCHAR, us_int_ld_mins VARCHAR, us_int_roaming_mins VARCHAR, can_data_gb_used VARCHAR, us_int_data_roam_gb_used VARCHAR, sms_messages_outgoing VARCHAR, voice_monthly_service_fee VARCHAR, voice_overage_charge VARCHAR, voice_can_ld_charge VARCHAR, voice_us_int_ld_charge VARCHAR, voice_us_int_roaming_min_charge VARCHAR, voice_directory_assistance VARCHAR, sms_message_overage VARCHAR, voice_other_charges VARCHAR, voice_total_charges VARCHAR, data_monthly_service_fee VARCHAR, data_overage_charge VARCHAR, data_other_charges VARCHAR, data_total_charges VARCHAR, other_charges_and_credits VARCHAR, voice_rate_plan VARCHAR, data_rate_plan VARCHAR, rcid VARCHAR, rcid_cust_nm VARCHAR, cbu_cid VARCHAR, cbucid_cust_nm VARCHAR, bpi_prod_cd VARCHAR, bpi_prod_desc VARCHAR, rn_1 VARCHAR, rn_2 VARCHAR, rn_3 VARCHAR, rn_4 VARCHAR, agreement VARCHAR, vendor VARCHAR, billing_city VARCHAR, entity_key INTEGER, price_book_key VARCHAR, inserted_at TIMESTAMP);"}, transformation_ctx="AmazonRedshift_node1739272798937")

job.commit()