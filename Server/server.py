from settings import *
PACKET_SIZE = 1024

class Server:
    def __init__(self, ip='127.0.0.1', port=10001):
        port = 1024+random.randint(1, 1000)
        self.address = (ip, port)
        self.client = {}
        self.init_hints = []
        self.hints = []
        self.games = []

    def near(self, latitude, longitude, hint):
#print type(latitude), type(longitude), type(hint.latitude)
        if ((latitude-hint.latitude)**2+(longitude-hint.longitude)**2)**0.5 < 0.0001:
            return True
        return False

    def handle_json(self, data, my_token):
        try:
            json_data = json.loads(data)
        except ValueError, e:
            print >>sys.stderr, e
            return 'ERROR'
        except TypeError, e:
            print >>sys.stderr, e
            return 'ERROR'

        try:
            json_type = json_data['jsonType']
        except ValueError, e:
            print >>sys.stderr, e
            return 'ERROR'
        except TypeError, e:
            print >>sys.stderr, e
            return 'ERROR'

        ### Fist time use this app ###
        if json_type == -1:
            m = md5.new()
            mykey = m.hexdigest()
            while mykey in self.client:
                m.update("wala")
                mykey = m.hexdigest()
            self.client[mykey] = Client()
            response = {}
            response["token"] = mykey
            response = json.dumps(response)
            return response

        ### Not the first time, so there's a token ###
        ### Then get the token ###
        try:
            my_token = json_data["token"]
        except KeyError, e:
            print >>sys.stderr, e, 'no token'
            return 'ERROR'
            
        ### Now we have token, then we can do things via token ###
        ### Choosing a new game, if continue, it won't enter this phase ###
        if json_type == 4:
            response = {}
            self.write_cnt_response(response, "game", self.games)
            response = json.dumps(response)
            print >>sys.stderr, 'retrun games'
            return response
        
        elif json_type == 0:
            try:
                name = json_data["playerName"]
            except KeyError, e:
                print >>sys.stderr, e, 'no key playerName'
                return 'ERROR'
            except ValueError, e:
                print >>sys.stderr, e, 'no name obj'
                return 'ERROR'
            else:
                response = {}
                if self.set_client_name(name, my_token):
                    print >>sys.stderr, 'set name: ', name
                    response["success"] = "true"
                    for c in self.client:
                        self.client[my_token].others_msg.extend(self.client[c].msg)
                else:
                    response["success"] = "false"
                response = json.dumps(response)
                return response
                
        elif json_type == 1:
            response = {}
            write_cnt_response(response, "hint", self.init_hints)
            response = json.dumps(response)
            print >>sys.stderr, 'retrun hints'
            return response

        elif json_type == 2:
            try:
                latitude = json_data["lat"]
                longitude = json_data["long"]
            except ValueError, e:
                print >>sys.stderr, e, 'no lat or long obj'
                return 'ERROR'
            else:
                response = {}
                self.client[my_token].set_lat(latitude)
                self.client[my_token].set_long(longitude)
                print >>sys.stderr, 'lat: ', json_data["lat"], 'long: ', json_data["long"]

                player_id = 0
                for s in self.client:
                    if s == my_token:
                        continue
                    player = "player"+str(player_id)
                    player_id = player_id + 1
                    position = {}
                    position["lat"] = self.client[s].latitude
                    position["long"] = self.client[s].longitude
                    response[player] = position
                
                response["playerCnt"] = player_id

                hint_id = 0
                for h in self.hints:
                    if my_token in h.sent:
                        continue
                    if self.near(latitude, longitude, h):
                        hint = "hint"+str(hint_id)
                        response[hint] = h.content
                        hint_id = hint_id + 1
                        h.sent.append(my_token)

                response["hintCnt"] = hint_id

                msg_id = 0
                for m in self.client[my_token].others_msg:
                    data = {}
                    data["lat"] = m.latitude
                    data["long"] = m.longitude
                    data["content"] = m.content
                    msg = "msg"+str(msg_id)
                    response[msg] = data
                    msg_id = msg_id + 1

                response["msgCnt"] = msg_id
                del self.client[my_token].others_msg[:]
                        
                response = json.dumps(response)
                return response
                
        elif json_type == 3:
            content = json_data["msg"]
            latitude = self.client[my_token].latitude
            longitude = self.client[my_token].longitude
            message = Message(latitude, longitude, content)

            for c in self.client:
                if c == my_token:
                    self.client[c].msg.append(message)
                else: 
                    self.client[c].others_msg.append(message)
            print >>sys.stderr, 'get msg: ', json_data["msg"]
            response = {}
            response["success"] = "true"
            response = json.dumps(response)
            return response
        else:
            print >>sys.stderr, 'none of above'
            
        return "test"
        
    def set_client_name(self, name, my_token):
        for client in self.client:
            if name == self.client[client].name:
                return False
        self.client[my_token].set_name(name)
        return True

    def listen(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        
        # Bind the socket to the port
        print >>sys.stderr, 'starting up on %s port %s' % self.address
        self.sock.bind(self.address)
        
        # Listen for incoming connections
        self.sock.listen(5)

        # Sockets from which we expect to read
        inputs = [self.sock]
        # Sockets to which we expect to write
        outputs = [self.sock]
        # Outgoing message queues (socket:Queue)
        message_queues = {}
        
        while inputs:
            # Wait for at least one of the sockets to be ready for processing
            print >>sys.stderr, '\nwaiting for the next event'
            readable, writable, exceptional = select.select(inputs, outputs, inputs)

            # Handle inputs
            for s in readable:
                if s is self.sock:
                    # A "readable" server socket is ready to accept a connection
                    connection, client_address = s.accept()
                    print >>sys.stderr, 'new connection from', client_address
                    new_client = Client()
                    self.client[connection] = new_client
                    connection.setblocking(0)
                    inputs.append(connection)
    
                    # Give the connection a queue for data we want to send
                    message_queues[connection] = Queue.Queue()
                else:
                    try:
                        data = s.recv(PACKET_SIZE)
                    except SocketError, e:
                        print >>sys.stderr, 'SocketError', e
                        continue
                    
                    print "get: ", data
                    if data:
                        # A readable client socket has data
                        print >>sys.stderr, 'received "%s" from %s' % (data, s.getpeername())
                        response = self.handle_json(data, s) + "\n"
                        message_queues[s].put(response)
                        # Add output channel for response
                        if s not in outputs:
                            outputs.append(s)
                    else:
                        # Interpret empty result as closed connection
                        print >>sys.stderr, 'closing', client_address, 'after reading no data'
                        # Stop listening for input on the connection
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        del self.client[s]
                        print 'remove client: ', self.client
                        s.close()

                        # Remove message queue
                        del message_queues[s]

            # Handle outputs
            for s in writable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except Queue.Empty:
                    # No messages waiting so stop checking for writability.
                    print >>sys.stderr, 'output queue for', s.getpeername(), 'is empty'
                    outputs.remove(s)
                else:
                    print >>sys.stderr, 'sending "%s" to %s' % (next_msg, s.getpeername())
                    s.send(next_msg)

            # Handle "exceptional conditions"
            for s in exceptional:
                print >>sys.stderr, 'handling exceptional condition for', s.getpeername()
                # Stop listening for input on the connection
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()

                # Remove message queue
                del message_queues[s]

    def write_cnt_response(self, response, base_str, target_list):
        response[base_str+"Cnt"] = len(target_list)
        my_id = 0
        for data in target_list:
            label = base_str+str(my_id)
            response[label] = data
            my_id = my_id + 1

    def set_game(self, fname):
        with open(fname) as f:
            for line in f:
                self.games.append(line)

    def set_init_hint(self, fname):
        with open(fname) as f:
            for line in f:
                self.init_hints.append(line)

    def set_hint(self, fname):
        with open(fname) as f:
            for line in f:
                latitude, longitude, content = line.split(',')
                self.hints.append(Message(latitude, longitude, content))