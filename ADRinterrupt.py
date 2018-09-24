from __future__ import print_function
import multiprocessing.connection as mpc
from multiprocessing import AuthenticationError
from multiprocessing import TimeoutError
import select

mpc.Listener.fileno = lambda self: self._listener._socket.fileno()

# This file is used to send and receive packets between programs that can be used to control the
#   temperature setting for the cryostat. See ADR.py on how the program can be used to receive
#   packets.
# Created by Sean Moss on 8/24/18
# History:
#   9/18/18 - Fixed blocking call


class InterruptServer():
    '''
    Acts as the receiving end of the interrupt packets.

    To use, create an instance, call open(), and then poll() when you want to check for packets.
    poll() returns None if there are no packets, or a float if there is a temperature change request.
    Currently, this code only accepts one connection at a time, but this could be changed somewhat easily.
    Make sure to call close() when you are done with the listener.
    '''
    
    def __init__(self, addr='localhost', port=8888, password='', temprange=(0.05, 0.25)): # TODO: Check the hardcoded temp range values
        '''
        Prepares (but does not open) a connection to listen for temperature change requests.

        :param str addr: The address to use for the connection (defaults to localhost).
        :param int port: The port to listen on for packets (defaults to 8888).
        :param str password: The password to use for authentication, empty string for no password, or None to prompt at runtime.
        :param (float,float) temprange: The range of temperatures to accept as valid (in Kelvin).
        '''
        self._address = (addr, port)
        self._authkey = (password if password is not None else str(raw_input('Please enter the password to use for the server (empty for no password) > '))).strip()
        self._listener = None
        self._connection = None
        self._temprange = temprange
        self._lastPacket = None

    def open(self):
        '''
        Opens the listener to start accepting connections from clients.
        '''
        if self._listener is not None:
            print('Warning: the ADR interrupt listener cannot be opened twice.')
            return
        self._listener = mpc.Listener(self._address, 'AF_INET', authkey=(self._authkey if len(self._authkey) > 0 else None))

    def try_connect(self, c):
        pass

    def is_open(self):
        '''
        Returns if the server is currently open and listening.
        '''
        return self._listener is not None

    def poll(self):
        '''
        Performs a non-blocking check for waiting packets from Clients. Returns None if there are no packets, or a float with the new
        requested temperature, in Kelvin.
        '''
        if self._listener is None: # A connection has not been made yet
            return None
        if self._connection is None: # No connection yet, perform a non-blocking check for a pending connection
            try:
                sr, _, _ = select.select((self._listener,), (), (), 0)
                if self._listener in sr:
                    self._connection = self._listener.accept()
                    print('Server: Accepted interrupt client connection from {}'.format(self._listener.last_accepted))
            except Exception as e:
                print ('Server: unknown exception while trying to wait for connections: {}'.format(e))
            return None

        packet = None
        try:
            if self._connection.poll():
                packet = self._connection.recv()
        except (EOFError, IOError) as e:
            print('Server: The client disconnected from the listener.')
            self._connection = None
            return None
        except Exception as e:
            print ('Server: unknown exception while trying to poll/recv packet: {}'.format(e))
            return None
        
        if packet is None:
            return None
        try:
            new_temp = float(packet)
            if self._temprange[0] < new_temp < self._temprange[1]:
                self._connection.send((True, str(new_temp)))
                return new_temp
            else:
                self._connection.send((False, 'The temperature sent is outside of the valid range ({} -> {})'.format(self._temprange[0], self._temprange[1])))
                return None
        except ValueError:
            print('Server: Listener received a packet, but it was not formatted as a float')
            self._connection.send((False, 'Packet was not formatted as a float.'))
            return None
        except Exception as e:
            print ('Server: unknown exception while trying to parse packet: {}'.format(e))
            return None

    def close(self):
        if self._listener is not None:
            try:
                self._listener.close()
            except Exception: pass
            self._listener = None
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception: pass
            self._connection = None


class InterruptClient():
    '''
    Acts as the sending end of the interrupt packets.

    To use, create an instance, call open(), and then send(float) to send a temperature set request.
    send() will hang until a packet is received from the server with a result flag and message.

    Please see the real_test() function in interrupt_test.py to see a very basic example of how to use
    this class to change the temperature.
    '''
    
    def __init__(self, addr='localhost', port=8888, password=''):
        '''
        Prepares (but does not open) a connection to send interrupt commands to the ADR interrupt listener.

        :param str addr: The address to connect to (defaults to localhost).
        :param int port: The port to send packets on (defaults to 8888).
        :param str password: The password to use for authentication, empty string for no password, or None to prompt at runtime.
        '''
        self._address = (addr, port)
        self._authkey = (password if password is not None else str(raw_input('Please enter the password for the ADR interrupt listener > '))).strip()
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
        except Exception as e:
            print ('ERROR: unknown exception while trying to connect to server: {}'.format(e))
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
        except Exception as e:
            print ('Server: unknown exception while trying to send packet to server: {}'.format(e))
            return False

        packet = None
        try:
            if self._client.poll(5):
                rbytes = self._client.recv()
                packet = (bool(rbytes[0]), str(rbytes[1]))
        except TimeoutError:
            print('ERROR: The server accepted the interrupt packet, but did not acknowledge it. Check ADR.py for cryostat state.')
            return False
        except Exception as e:
            print ('Server: unknown exception while trying to receive confirmation packet from server: {}'.format(e))
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
            try:
                self._client.close()
            except Exception: pass
            self._client = None
