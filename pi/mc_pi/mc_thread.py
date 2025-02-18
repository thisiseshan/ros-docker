import errno
import json
import math
import queue
import socket
import threading
import time


# Get local machine name
SERVER_HOST = socket.gethostname()
MSG_SIZE = 1024
CPU_SUB_SERVER_PORT = 9999
MC_SUB_SERVER_PORT = 9998

def get_parsed_results():
        parsed = []
        totalConnectedMotors = 1
        for _ in range(totalConnectedMotors):
            parsed.append(
                {
                    "MODE" : 3,
                    "POSITION" : 1.0,
                    "VELOCITY" : 1.0,
                    "TORQUE" : 1.0,
                    "VOLTAGE": 1.0,
                    "TEMPERATURE" : 1.0,
                    "FAULT" : 1.0
                }
            )
        return parsed

def get_cpu_info(sock):
    while True:
        try:
            # 0. get message and process
            bytes_msg = sock.recv(MSG_SIZE)

            # 1. exit the loop if no more data to read
            if not bytes_msg:
                continue

            # 2. cconvert to json object and get the id and mc12 data
            json_msg = json.loads(bytes_msg)
            msg_id = json_msg["id"]
            mc12 = json_msg["mc12"]
            

            # 3. skip if not data received yet
            if not mc12:
                continue
            # cpu_data.put(mc12)
            
            # 4. get data for 2nd motor (0th index, since theres only 1 motor connected
            mc2data = mc12[0]

            # 5. log
            print("MC: from CPU id={}, m_mc2={}".format(msg_id, mc2data))

            # 6. set attributes
            # m.setAttributes(mc2data[0], pos=mc2data[1], velocity = mc2data[2], torque=mc2data[3])
        
        except KeyError:
                print("Error: 'id' or 'mc12' key not found in JSON data")
        except json.JSONDecodeError:
            print("Error: Invalid JSON data received. Reconnecting...")
        
        except socket.timeout as e:
            print("Timeout occurred while waiting for response: {}".format(e))
        
        except IOError as e:  
            if e.errno == errno.EPIPE:  
                print("broken pipe: {}".format(e))
    
      

def send_mc_info(sock):
        
    id = 1
    while True:
        # 0. get data from the 12 controllers
        # if connected to 1 motor, there's only 1 element
        parsedRes = get_parsed_results()

        # - hard code motor id= 2
        motorId = 2
        mcs12 = [[motorId, math.nan, parsed["VELOCITY"], parsed["TORQUE"] ] for parsed in parsedRes]
        
        # 1. create a dict
        data = {"mc12": mcs12, "id":id}

        # 2. send as bytes encoded json
        sock.send((json.dumps(data)).encode())
        id+=1

        # 3. sleep for 20ms so its sending at 50Hz
        time.sleep(0.02)


def main():
    # 1. init socket and time out to listen to cpu_sub node
    cpu_sub_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cpu_sub_socket.settimeout(2.0)
    # connect to server
    cpu_sub_socket.connect((SERVER_HOST, CPU_SUB_SERVER_PORT))
    cpu_sub_socket.setblocking(False)  # set socket to non-blocking

    # 2. inis socket and timeout to send msg to mc_sub node
    mc_sub_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mc_sub_socket.settimeout(10.0)
    mc_sub_socket.connect((SERVER_HOST, MC_SUB_SERVER_PORT))

    # 3. init thread
    get_cpu_info_thread = threading.Thread(target=get_cpu_info, args=(cpu_sub_socket,))
    send_mc_info_thread = threading.Thread(target=send_mc_info, args=(mc_sub_socket,))
    
    # 4. run
    get_cpu_info_thread.start()
    send_mc_info_thread.start()

    get_cpu_info_thread.join()
    send_mc_info_thread.join()


if __name__ == "__main__":
    main()