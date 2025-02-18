# ros-docker
## INTRODUCTION: 
This repo contain a communication framework that will a part of robot dog project in this repo:  
https://github.com/NEURoboticsClub/NU-Dog/tree/main  

Our motor controller (MC) program moteus_test.py is a program that will control the 12 motors that are running the robot's movement. We will be sending ROS commands to MC from our laptop using the script in cpu.py.  
So we need another ROS node inside our Raspberry pi to receive these commands and pass it to MC. However, there is an incompatibility issue with Raspberry Pi used in this project and the ROS version that we want to use which is ROS melodic.  

So the objective is to set up a communication framework so that a ROS node in our machine (cpu.py) can communicate with the motor controller program (moteus_test.py) in Raspberry Pi.  

This framework will solve the incompatibility issue by leveraging Docker containers.  

### How does this work?  
We will run what we will call the “bridge” nodes which are ROS nodes that will be running in the Docker environment with ROS package and other dependencies installed. These nodes do not do anything other than passing messages back and forth between MC and CPU. They are multi-threaded so that they can listen and publish messages either using Python sockets or use ROS built-in publisher-subscriber framework concurrently. 

### What actually happens when we start running these nodes?  

Take a look at the diagram below which illustrates the high level overview of the messages that are passed.  

<img width="1157" alt="Screenshot 2023-07-13 at 2 42 40 PM" src="https://github.com/freecode23/ros-docker/assets/67333705/8d88c263-55ef-4767-9753-e63fb5ea1e48"> 

1. The cpu and ROS master node will start and the cpu node will send the initial command to MC using the ROS publisher framework. This message will be received by cpu_sub.py which is one of the bridge nodes that subscribes to the topic published by cpu.  

2. Cpu_sub will then pass on to MC using socket. MC will receive these bytes messages, convert them to JSON and set the attributes of the 12 motors. The attributes are: motor id, velocity, position, and torques.  

3. MC will call getParsedResults() method, which will grab the current motor attributes at real time and send them to mc_sub bridge node via socket.  

4. MC_sub bridge node will publish messages on MC topic so that its subscriber (the cpu node) can listen and invoke its callback function and do whatever it wants to do with this new motor attributes info.  

## PREREQUSITES:  
1. Docker and docker compose installed in your machine and PI  
Follow the link below to install docker compose in linux:  
https://docs.docker.com/compose/install/linux/#install-using-the-repository  

2. Python3 installed in PI  
## Step 0: Prepare the workspace directory in both machine:  
Copy the cpu directory into your machine (non-PI).  
Copy the pi directory into your PI

## Step 1: Run ros-master, cpu-node, bridge-nodes:  
### OPTION 1: ros-master and cpu-node in your machine, and bridge-nodes in PI:  
#### Step 1.1: Inside the cpu dir, get ROS_MASTER_URI and ROS_IP from your CPU machine for the docker-compose
Make sure Raspberry PI is connected to your machine.    
Enter the command below in your machine to get ROS_MASTER_URI which is the ip address of your machine:  
```ifconfig```  
If you are connected to PI using ethernet, find the ip address that starts with "enx"  
Example:  
```enx00e04c681fa8: flags=4163<UP,BROADCAST,RUNNING,MULTICAST> \n mtu 1500 inet 10.42.0.1  netmask 255.255.255.0  broadcast 10.42.0.255 ```
The ip address we want is 10.42.0.1  
Then then environment variables in docker-compose file in cpu directory should have the following:  
```"ROS_MASTER_URI=http://10.42.0.1:11311"```  
```"ROS_IP=10.42.0.1"```  
The ROS_MASTER_URI is to identify which container ip the ROS master is in.  
The ROS_IP is to identify which container ip the cpu_node is in. 

#### Step 1.2: Inside the pi dir, get the ROS_IP for docker-compose:  
Now we want to do the same for the nodes in our PI. 
In your pi terminal enter: 
```hostname -I```.  
Get the ip address that has the same first few digits as the one in your CPU since they are connected with ethernet
You will see the output like below  :
```10.42.0.215 172.17.0.1 ```  
Notice that the first one has the same first few digits as the one in the previous step. That is the ip for PI container that we want to use.  
Now in your docker-compose file in PI directory, add the following to your environment variable:  
```"ROS_MASTER_URI=http://10.42.0.1:11311"```  
```"ROS_IP=10.42.0.215"```  
The ROS_IP is to identify which container ip the bridge nodes are in. 
This is needed so that ROS nodes can communicate with each other not just with the master  


#### Step 1.3: Inside cpu dir, run cpu and master node:  
```docker compose up --build```  

#### Step 1.4: Inside pi dir, run bridge nodes:  
```docker compose up --build``` 

### OPTION 2: Run all nodes in PI:  
cd into the pi directory and run:  
```docker compose -f docker-compose-allpi.yaml up --build```

## Step 2: Inside pi dir, run motor controller:  
```python3 mc_test.py```  

## Step 3: To stop any running containers:  
```docker compose down```


## To play in bash shell in the docker container:
docker-compose exec cpu-node /bin/bash  
cpu-node is the service name defined in docker-compose.yaml file  


