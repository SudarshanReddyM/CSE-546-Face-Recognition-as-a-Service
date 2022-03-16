import boto3
# from cv2 import threshold
# import json
import paramiko
import threading
# from boto.s3.key import Key
# from boto.sqs.message import Message
from time import sleep
# import boto.s3
# import boto.sqs
# from sys import argv, exit
import time
# import os
# import boto

class Controller():
    def __init__(self):
        self.master_instance_id = "i-004ec846439426020"
        self.list_of_instance_ids = list()
        self.count_of_insances = 0
        self.sqs_queue_url = 'https://queue.amazonaws.com/116117304770/CSE546_Group27_SQS'
        self.list_of_threads = list()
        self.list_of_processing_instances = list()
        
    def start_instances(self, no_of_instances, ec2_client):
        for i in range(no_of_instances):
            ec2_client = boto3.client('ec2')
            start_instance = ec2_client.run_instances(
                BlockDeviceMappings=self.ec2_instance_config(),
                ImageId='ami-0417b03aea7f9fb32',
                InstanceType='t2.micro',
                KeyName='CSE546_SSH_Access', #key file name
                MinCount=1,
                MaxCount=1,
                Monitoring={
                    'Enabled': False
                },
                SecurityGroupIds=[
                    "sg-0282b800556f86195"
                ],
            )
            instance = start_instance["Instances"][0]
        try:
            ec2_client.create_tags(Resources=[instance["InstanceId"]], Tags=[{'Key':'Name', 'Value':'app_tier '+str(i)}])
        except:
            print("Not Tagged ! Instance might be terminated :", instance)
        print(start_instance)
            
    def ec2_instance_config(self):
        config = [
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {

                    'DeleteOnTermination': True,
                    'VolumeSize': 16,
                    'VolumeType': 'gp2'
                },
            },
        ]
        return config
    
    def get_count_of_running_and_stopped_instances(self, ec2_client):
        running_instances = self.get_list_of_running_instances(ec2_client)
        stopped_instances = self.get_list_of_stopped_instances(ec2_client)        
        return len(running_instances), len(stopped_instances)
    
    def get_list_of_running_instances(self, ec2_client):
        running_instances = ec2_client.instances.filter(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ["running", "pending"]
                }
            ]
        )
        running_instances = [i.id for i in running_instances if i.id != self.master_instance_id]
        return running_instances
    
    def get_list_of_stopped_instances(self, ec2_client):
        stopped_instances = ec2_client.instances.filter(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ["stopped", "stopping"]
                }
            ]
        )
        stopped_instances = [i.id for i in stopped_instances]
        return stopped_instances
    
    def get_queue_length(self, sqs_client):
        queue = sqs_client.get_queue_attributes(QueueUrl=self.sqs_queue_url, AttributeNames=['ApproximateNumberOfMessages',])
        return int(queue['Attributes']['ApproximateNumberOfMessages'])
    
    def process_image_in_ec2(self, ec2_client, instance_id):
        key = paramiko.RSAKey.from_private_key_file('/home/ec2-user/IAAS/CSE546_SSH_Access.pem') #pem file
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        instance = [i for i in ec2_client.instances.filter(InstanceIds=[instance_id])][0]
        while True:
            try:
                client.connect(hostname=instance.public_ip_address, username="ec2-user", pkey=key, timeout=30)
                print("Starting to Process")
                client.exec_command('python3 /home/ec2-user/process_image.py')
                print("Processed!!")
                client.close()
                break
            except Exception as e:
                print("Reattempting to connect "+str(e))
                sleep(10)
    
    def spin_up_instances(self):
        boto3_session = boto3.Session()
        ec2_client = boto3_session.resource("ec2")
        sqs_client = boto3_session.client("sqs")
        max_instances = 19
        
        
        while True:
            print("*"*15, "Start of Loop", "*"*15)
            no_of_running_instances , no_of_stopped_instances = self.get_count_of_running_and_stopped_instances(ec2_client)
            messages_in_queue = self.get_queue_length(sqs_client)
            print("Messages in Queue: ", messages_in_queue)
            print("Running Instances: ", no_of_running_instances)
            print("Stopped Instances: ", no_of_stopped_instances)
            stopped_instances = self.get_list_of_stopped_instances(ec2_client)
            
            if messages_in_queue > no_of_stopped_instances:
                no_of_new_instances_to_start = min(max_instances - no_of_stopped_instances, messages_in_queue)
                if no_of_new_instances_to_start > 0:
                    print(f"Starting {no_of_new_instances_to_start} new instances")
                    self.start_instances(no_of_new_instances_to_start, ec2_client)
                # Include sleep if necessary
                print(f"Starting {stopped_instances} stopped instances")
                ec2_client.instances.filter(InstanceIds=stopped_instances).start()
                time.sleep(60)
                
            else:
                no_of_instances_to_start = min(no_of_stopped_instances, messages_in_queue - (no_of_running_instances - len(self.list_of_processing_instances)))
                if no_of_instances_to_start > 0:
                    print(f"Messages are less, Starting {no_of_instances_to_start} instances")
                    ec2_client.instances.filter(InstanceIds=stopped_instances[:no_of_instances_to_start]).start()
                    time.sleep(60)
            
            self.execute_each_instance(ec2_client)
            
            # idle_instances = [id for id in  s elf.get_list_of_running_instances(ec2_client) if id]
            idle_instances = list()
            for id in self.get_list_of_running_instances(ec2_client):
                if id not in self.list_of_processing_instances:
                    idle_instances.append(id)
            
            if len(idle_instances):
                print("Stopping Idle Instances: ", idle_instances)
                ec2_client.instances.filter(InstanceIds=idle_instances).stop()
                time.sleep(45)
            
            if self.get_queue_length(sqs_client) == 0:
                time.sleep(20)
                
    def execute_each_instance(self, ec2_client):
        for instance_id in self.get_list_of_running_instances(ec2_client):
            if instance_id not in self.list_of_processing_instances:
                thread = threading.Thread(name=instance_id, target=self.process_image_in_ec2, args=(ec2_client, instance_id))
                self.list_of_threads.append(thread)
                self.list_of_processing_instances.append(instance_id)
                thread.start()
        for each_thread in self.list_of_threads:
            if each_thread.is_alive():
                self.list_of_processing_instances.remove(each_thread.getName())
                self.list_of_threads.remove(each_thread)
            
        
if __name__=="__main__":
    controller = Controller()
    controller.spin_up_instances()
     
