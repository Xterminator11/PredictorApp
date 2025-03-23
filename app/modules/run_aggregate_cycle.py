import boto3
import botocore


s3 = boto3.resource("s3")
my_bucket = s3.Bucket("predictor-app-dallas-ipl2025")
for my_bucket_object in my_bucket.objects.all():
   if str(my_bucket_object.key).startswith("aggregates/"):
      continue
   else:
      s3.get_object("predictor-app-dallas-ipl2025",my_bucket_object.key)
