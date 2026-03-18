

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
# import boto3

# # Initialize S3 client
# s3 = boto3.client('s3')

# def move_s3_files(source_bucket, source_prefix, destination_prefix):
#     # List objects in the source folder
#     response = s3.list_objects_v2(Bucket=source_bucket, Prefix=source_prefix)
    
#     if 'Contents' in response:
#         for obj in response['Contents']:
#             source_key = obj['Key']
#             destination_key = destination_prefix + source_key[len(source_prefix):]
            
#             # Copy the object to the new location
#             s3.copy_object(Bucket=source_bucket, 
#                            CopySource={'Bucket': source_bucket, 'Key': source_key}, 
#                            Key=destination_key)
            
#             # Delete the original object
#             s3.delete_object(Bucket=source_bucket, Key=source_key)
#             print(f"Moved {source_key} to {destination_key}")
#     else:
#         print(f"No files found in {source_prefix}.")

# # Set your parameters
# source_bucket = "tsma-raw-data"
# folders = ["wln/", "wls/"]
# destination_prefixes = ["archieve/wln/", "archieve/wls/"]

# # source_bucket = "tsma-raw-data"
# # folders = ["wln/"]
# # destination_prefixes = ["archieve/wln/"]

# # Execute the function for each folder
# for source_prefix, destination_prefix in zip(folders, destination_prefixes):
#     move_s3_files(source_bucket, source_prefix, destination_prefix)
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