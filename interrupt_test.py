'''
This is for testing the ADR interrupt code.
'''

from ADRinterrupt import InterruptClient, InterruptServer
import multiprocessing
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
    s_task = multiprocessing.Process(target=server_thread)
    s_task.daemon = True
    c_task = multiprocessing.Process(target=client_thread)
    c_task.daemon = True
    s_task.start()
    c_task.start()
    s_task.join()
    c_task.join()


if __name__ == '__main__':
    main()
