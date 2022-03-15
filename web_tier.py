from flask import Flask, render_template, request, redirect, url_for
import json
import boto3
from time import sleep


app = Flask(__name__)

class UploadImage:
    def __init__(self) -> None:
        # Please provide your aws region where s3 bucket and SQS are created.
        self.aws_region = "us-east-one"
        # Please provide your input bucket name. Just the name is enough because it is running in ec2. arn format not required.
        # Example :- self.s3_input_bucket_name= "cse546group27inputbucket"
        self.s3_input_bucket_name= "cse546group27inputbucket"
        # Please provide your output bucket name. Just the name is enough because it is running in ec2. arn format not required.   
        self.s3_output_bucket_name="cse546group27outputbucket"
        # Please provide your SQS name. Just the name is enough because it is running in ec2. arn format not required.   
        self.sqs_queue_name = "CSE546_Group27_SQS"
        self.sqs_queue_url = 'https://queue.amazonaws.com/116117304770/CSE546_Group27_SQS'
        
    
    def image_upload(self, file, file_name):
        boto3_session =  boto3.Session()
        
        s3 = boto3_session.client("s3")
        self.upload_image_to_s3(s3, file, file_name)
        
        # all_buckets = s3.list_buckets()
        # s3.upload_fileobj(file, self.s3_input_bucket_name, str(file_name))
        # print("Image uploaded to S3")
        sqs = boto3_session.client("sqs")
        self.upload_message_to_sqs_queue(sqs, file_name)
        # all_queues = sqs.list_queues()
    #     message_attributes = {
    #     'Title': {
    #         'DataType': 'String',
    #         'StringValue': 'Image Name'
    #     },
    #     'Author': {
    #         'DataType': 'String',
    #         'StringValue': 'Sudarshan Darshin Koushik'
    #     }
    # }
    #     message_body = json.dumps(["process", self.s3_input_bucket_name, "", "", file_name])
    #     sqs.send_message(QueueUrl=self.sqs_queue_url, MessageAttributes=message_attributes, MessageBody=message_body)
        
    #     print("Message Uploaded to Queue")
        return "Success"
    
    def upload_image_to_s3(self, s3_client, file, file_name):
        s3_client.upload_fileobj(file, self.s3_input_bucket_name, str(file_name))
        print("Image uploaded to S3")
        return
    
    def upload_message_to_sqs_queue(self, sqs_client, file_name):
        message_attributes = {
        'Title': {
            'DataType': 'String',
            'StringValue': 'Image Name'
        },
        'Author': {
            'DataType': 'String',
            'StringValue': 'Sudarshan Darshin Koushik'
        }
    }
        message_body = json.dumps(["process", self.s3_input_bucket_name, "", "", file_name])
        sqs_client.send_message(QueueUrl=self.sqs_queue_url, MessageAttributes=message_attributes, MessageBody=message_body)
        
        print("Message Uploaded to Queue")
        return
    
    def retrieve_data_from_s3(self):
        list_of_objects = {"response": []}
        boto3_session =  boto3.Session()
        s3 = boto3_session.client("s3")
        objects = s3.list_objects_v2(Bucket=self.s3_output_bucket_name)
        for obj in objects['Contents']:
            key = obj["Key"]
            obj = s3.get_object(Bucket=self.s3_output_bucket_name, Key=key)
            j = obj["Body"].read().decode("utf-8")
            list_of_objects["response"].append(j[:-1])
        
        return list_of_objects
        
        
@app.route('/upload-image', methods=['POST'])
def upload_image():
    aws_object = UploadImage()
    for file in request.files.getlist('file'):
        if file.filename:
            aws_object.image_upload(file, file.filename)
    return "Success POST Call!!"

@app.route('/', methods=["GET"])
def fetch_output():
    aws_obj = UploadImage()
    return aws_obj.retrieve_data_from_s3()
    


if __name__=="__main__":
    app.run(debug=True)