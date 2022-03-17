import boto3
# import boto.s3
# import boto
import json
from sys import argv, exit
# from boto.s3.key import Key
# import boto.sqs
# from boto.sqs.message import Message
import os


class ProcessImage():
    def __init__(self):
        self.s3_input_bucket_name= "cse546group27inputbucket"
        self.s3_output_bucket_name="cse546group27outputbucket"
        self.sqs_queue_name = "CSE546_Group27_SQS"
        self.sqs_queue_url = 'https://queue.amazonaws.com/116117304770/CSE546_Group27_SQS'
        self.sqs_response_queue = "https://sqs.us-east-1.amazonaws.com/116117304770/CSE546_Group27_Response_Queue"
        # self.download_folder_for_images = "/Users/dp/Desktop/StoreImages"
        self.download_folder_for_images = "/home/ec2-user/StoreImages"
        self.sqs_service = boto3.resource("sqs")
        self.sqs_client = boto3.client("sqs")
    def fetch_image_from_sqs(self):
        # sqs_service = boto3.resource("sqs")
        queue = self.sqs_service.get_queue_by_name(QueueName=self.sqs_queue_name)
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20)
        # print("Messages:  ")
        # print(messages)
        content = ['no_message']
        if messages:
            for each_message in messages:
                # print(each_message)
                # print(each_message.receipt_handle)
                content = json.loads(each_message.body)
                each_message.delete()
                # print("Message deleted")
                # print("Content:", content)
                # tag = content[0]
                # if tag == "process":
                #     s3_bucket_name = content[1]
                #     file_name = content[4]
                #     print(s3_bucket_name, file_name)
                #     execution = self.process_image(s3_bucket_name, file_name)
                #     if execution:
                #         print("Message Processed !!")
        else:
            print("No messages in Queue")
        return content
    
    def send_image_for_processing(self, content):
        # if content[0] == "process":
        print(content[1], content[4])
        execution = self.process_image(content[1], content[4])
        if execution:
            print("Message Processed")
    
    def process_image(self,s3_bucket_name, file_name):
        # file_name_and_extension = file_name.split(".")
        boto3_session =  boto3.Session()
        s3 = boto3_session.client("s3")
        self.download_image(s3, file_name)
        downloaded_image = self.download_folder_for_images + "/" + file_name
        image_processed_file = self.download_folder_for_images + "/" + file_name.split(".")[0] + ".txt"
        
        print("Processing the Image !!!")
        os.system("python3 /home/ec2-user/face_recognition.py " + downloaded_image + " > " + image_processed_file)
        # os.system("python3 /Users/dp/Desktop/face_recognition.py " + "> " + image_processed_file)
        self.upload_result_to_s3(s3, image_processed_file, file_name)
        
    def download_image(self,s3_client, key_name):
        if not os.path.exists(self.download_folder_for_images):
            os.makedirs(self.download_folder_for_images)
        s3_client.download_file(self.s3_input_bucket_name, key_name, self.download_folder_for_images + "/" + key_name)
        print("Image Downloaded!!!")
        
    def upload_result_to_s3(self, s3_client, file_path, file_name):
        with open(file_path, "r") as f:
            content = f.readline()
            print("content of file  ", content)
        with open(file_path, "w") as f:
            f.write(file_name + ":" + content)
        # s3_client.upload_file(file_path, self.s3_output_bucket_name, file_name.split(".")[0] + ".txt")
        # print("File uploaded succesfully!!")
        self.upload_result_to_sqs_response(file_path, s3_client)
        
    def upload_result_to_sqs_response(self, file_path, s3_client):
        with open(file_path, "r") as f:
            content = f.readline()
            key, value = content.split(":")
            message = {key : value}
            response = self.sqs_client.send_message(QueueUrl=self.sqs_response_queue, MessageBody=json.dumps(message))
            print("Message Upload to Response Queue", response)
            self.upload_to_sqs_from_s3(s3_client)
    
    def upload_to_sqs_from_s3(self, s3_client):
        s3_client = boto3.client("s3")
        queue = self.sqs_service.get_queue_by_name(QueueName=self.sqs_response_queue)
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20)
        if messages:
            for m in messages:
                content = json.loads(m.body)
                s3_client.put_object(Body=list(content.values())[0], Bucket=self.s3_output_bucket_name, Key=list(content.keys())[0].split(".")[0]+".txt")
                
if __name__=="__main__":
    process_image = ProcessImage()
    # while True:
    #     content = process_image.fetch_image_from_sqs()
    #     if content[0] == "process":
    #         process_image.send_image_for_processing(content)
    #     else:
    #         break
    process_image.upload_to_sqs_from_s3("xxx")