'''
This is for testing the ADR interrupt code.
'''

from ADRinterrupt import InterruptClient, InterruptServer
import threading
import time


def server_thread():
    server = InterruptServer(password='')
    server.open()
    while True:
        temp = server.poll()
        if temp is None:
            print('No Packet')
        else:
            print('Temperature: {}'.format(temp))
        time.sleep(1)
    server.close()

def client_thread():
    client = InterruptClient(password='')
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
    client.close()


def main():
    s_task = threading.Thread(target=server_thread)
    c_task = threading.Thread(target=client_thread)
    s_task.start()
    #c_task.start()
    s_task.join()
    #c_task.join()


if __name__ == '__main__':
    main()
