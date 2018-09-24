'''
This is for testing the ADR interrupt code.
'''

from __future__ import print_function
from ADRinterrupt import InterruptClient, InterruptServer
import threading
import time

def server_thread():
    server = InterruptServer(temprange=(-1, 1))
    server.open()
    while True:
        temp = server.poll()
        if temp is None:
            print('Server: No Packet or Invalid Packet')
        else:
            if temp == 0:
                break
            else:
                print('Server: Temperature: {}'.format(temp))
        time.sleep(1)
    print ('Server: Closing')
    server.close()

def client_thread():
    client = InterruptClient()
    client.open()
    tosend = [ 1.3, 0.05, 18, 'trash', '14', True ]
    for data in tosend:
        client.send(data)
        time.sleep(2)
    client.close()
    client.open()
    tosend.reverse()
    for data in tosend:
        client.send(data)
        time.sleep(2)
    client.send(0)
    client.close()
    print('Client: Closing')

def local_test():
    s_task = threading.Thread(target=server_thread)
    c_task = threading.Thread(target=client_thread)
    s_task.start()
    time.sleep(2.5)
    c_task.start()
    s_task.join()
    c_task.join()

def real_test():
    client = InterruptClient()
    if not client.open():
        return
    
    while True:
        entry = raw_input('Please enter the new cryostat temp as a float, or "quit" > ')
        if entry == 'quit':
            break
        try:
            new_temp = float(entry)
        except ValueError:
            print('Please enter a valid floating point number')
            continue
        client.send(new_temp)

    client.close()


if __name__ == '__main__':
    option = 0
    while True:
        try:
            entry = raw_input('Please enter 1 for local test, or 2 for real test > ')
            if entry != 'quit':
                option = int(entry)
            break
        except ValueError:
            print('Please enter a valid integer')
        else:
            if option not in [1, 2]:
                print('Please enter either 1 or 2')
    if option == 1:
        local_test()
    elif option == 2:
        real_test()
