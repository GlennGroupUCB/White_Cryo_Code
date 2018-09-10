from __future__ import print_function
import multiprocessing.connection as mpc
from multiprocessing import AuthenticationError
from multiprocessing import TimeoutError

# This file is used to send and receive packets between programs that can be used to control the
#   temperature setting for the cryostat. See ADR.py on how the program can be used to receive
#   packets.
# Created by Sean Moss on 8/24/18


class InterruptServer():
    '''
    Acts as the receiving end of the interrupt packets.

    To use, create an instance, call open(), and then poll() when you want to check for packets.
    poll() returns None if there are no packets, or a float if there is a temperature change request.
    Currently, this code only accepts one connection at a time, but this could be changed somewhat easily.
    Make sure to call close() when you are done with the listener.
    '''
    
    def __init__(self, addr='localhost', port=8888, password=None):
        '''
        Prepares (but does not open) a connection to listen for temperature change requests.

        :param str addr: The address to use for the connection (defaults to localhost).
        :param int port: The port to listen on for packets (defaults to 8888).
        :param str password: The password to use for authentication, empty string for no password, or None to prompt at runtime.
        '''
        self._address = (addr, port)
        self._authkey = (password if password is not None else str(input('Please enter the password to use for the server (empty for no password) > '))).strip()
        self._listener = None
        self._connection = None

    def open(self):
        '''
        Opens the listener to start accepting connections from clients.
        '''
        if self._listener is not None:
            print('Warning: the ADR interrupt listener cannot be opened twice.')
            return
        self._listener = mpc.Listener(self._address, 'AF_INET', authkey=(self._authkey if len(self._authkey) > 0 else None))

    def poll(self):
        '''
        Performs a non-blocking check for waiting packets from Clients. Returns None if there are no packets, or a float with the new
        requested temperature, in Kelvin. This float is not checked for validity so the caller needs to check.
        '''
        if self._listener is None: # open() has not been called yet
            return None
        if self._connection is None: # try to accept a new connection object
            try:
                self._connection = self._listener.accept()
                if self._connection is not None:
                    print('A connection was made for ADR interrupts from {}.'.format(self._listener.last_accepted))
            except AuthenticationError:
                print ('A connection was attempted, but failed the authentication.')
            return None

        packet = None
        try:
            if self._connection.poll():
                packet = self._connection.recv()
        except EOFError:
            print('The client disconnected from the listener.')
            self._connection = None
            return None
        
        if packet is None:
            return None
        try:
            new_temp = float(packet)
            self._connection.send((True, str(new_temp)))
            return new_temp
        except ValueError:
            print('Listener received a packet, but it was not formatted as a float')
            self._connection.send((False, 'Packet was not formatted as a float.'))
            return None

    def close(self):
        if self._listener is not None:
            self._listener.close()
            self._listener = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None


class InterruptClient():
    '''
    Acts as the sending end of the interrupt packets.

    To use, create an instance, call open(), and then send(float) to send a temperature set request.
    send() will hang until a packet is received from the server with a result flag and message.
    '''
    
    def __init__(self, addr='localhost', port=8888, password=None):
        '''
        Prepares (but does not open) a connection to send interrupt commands to the ADR interrupt listener.

        :param str addr: The address to connect to (defaults to localhost).
        :param int port: The port to send packets on (defaults to 8888).
        :param str password: The password to use for authentication, empty string for no password, or None to prompt at runtime.
        '''
        self._address = (addr, port)
        self._authkey = (password if password is not None else str(input('Please enter the password for the ADR interrupt listener > '))).strip()
        self._client = None

    def open(self):
        '''
        Attempts to open the connection to the ADR interrupt listener, returns the success. Will print an error message on
        failure.
        '''
        try:
            self._client = mpc.Client(self._address, 'AF_INET', authkey=(self._authkey if len(self._authkey) > 0 else None))
        except AuthenticationError:
            print('ERROR: Authentication with the ADR interrupt listener failed.')
            return False
        except TimeoutError:
            print('ERROR: Connection attempt with ADR interrupt listener timed out.')
            return False
        return True

    def send(self, temp):
        '''
        Sends the temperature interrupt as a float, given in Kelvins. This method will block until it reveives a message from the listener,
        or 5 seconds pass. Returns True if the interrupt was accepted, False otherwise.

        :param float temp: The temperature to set the ADR target to, in Kelvin.
        '''
        if self._client is None:
            return False
        try:
            temp = float(temp)
        except ValueError:
            print('ERROR: The temperature was not given as a float')
            return False

        try:
            self._client.send(temp)
        except TimeoutError:
            print('ERROR: The connection to the ADR listener timed out while sending, did the running instance of ADR.py close?')
            return False

        packet = None
        try:
            if self._client.poll(timeout=5):
                rbytes = self._client.recv()
                packet = (bool(rbytes[0]), str(rbytes[1]))
        except TimeoutError:
            print('ERROR: The server accepted the interrupt packet, but did not acknowledge it. Check ADR.py for cryostat state.')
            return False

        if packet is None:
            print('ERROR: The server accepted the interrupt packet, but did not acknowledge it. Check ADR.py for cryostat state.')
            return False
        if packet[0]:
            print('SUCCESS: The ADR listener accepted the packet, temperature: {}'.format(packet[1]))
        else:
            print('ERROR: The ADR listener rejected the packet, reason: "{}"'.format(packet[1]))

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None
