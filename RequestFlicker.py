from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer
import json

class RequestFlicker(WebSocket):

	INVALID_FIRST_MESSAGE = ("Bad first message, "
							"example for service : \\\\echoService," 
                            "for client : {\"service\":\"echoService\",\"request\":\"ping\"}")
	
	pendingRequest = {}
	servicesRegistered = {}
	requestNumber = 0
	def __init__(self, server, sock, address):
		self.role = Role.NOT_SET
		WebSocket.__init__(self, server, sock, address)
		
	def handleMessage(self):
			
		try:
			if self.data is None:
				self.data = ''
			
			msg = str(self.data)
			
			if msg == "ping":
				self.sendMessage("pong")
				return
			
			# CASE 1 : REQUESTER
			if self.role == Role.REQUESTER:
				#We only listen to one request at a time
				#For another request, create a new connection
				print 'Ignoring message ',msg
				return
			
			# CASE 2 : NOT_SET			
			if self.role == Role.NOT_SET:	
				request = getRequest(msg)
				if request is not None:
					self.role = Role.REQUESTER
					serviceName = request['service']
					if serviceName in RequestFlicker.servicesRegistered :
						self.requestId = RequestFlicker.requestNumber
						RequestFlicker.requestNumber +=1
						idAndRequest = {}
						idAndRequest['id'] = self.requestId
						idAndRequest['request'] = request['request']
						RequestFlicker.pendingRequest[self.requestId] = self						
						RequestFlicker.servicesRegistered[serviceName].sendMessage(json.dumps(idAndRequest))						
					else:
						self.sendMessage(getErrorMessage('No service registered for {}'.format(serviceName)))
				else:		
					registrationName = getRegistrationName(msg)
					if registrationName is not None:
						self.role = Role.SERVICE
						self.serviceName = registrationName
						self.sendMessage('service registered : {}!'.format(registrationName))
						RequestFlicker.servicesRegistered[self.serviceName] = self						
					else:				
						self.sendMessage(RequestFlicker.INVALID_FIRST_MESSAGE)	
				return
			
			# CASE 3 : SERVICE			
			if self.role == Role.SERVICE:				
				answer = getAnwser(msg)
				if answer is not None:
					id = int(answer['id'])
					if id in RequestFlicker.pendingRequest :
						RequestFlicker.pendingRequest[id].sendMessage(json.dumps(answer['answer']))
					else:
						self.sendMessage('client disconnected')
				else:
					self.sendMessage('Invalid answer, should be a json string with id and answer field.'
					'example {\"id\":102,\"answer\":\"pong\"}')
		except Exception,e:
			print 'Exception while handling message'
			print 'Message: {} '.format(msg)
			print str(e)	
	
	def handleConnected(self):
		print self.address, 'connected'

	def handleClose(self):
	
		try:
			if self.role == Role.SERVICE:
				print 'Service {} disconnected'.format(self.serviceName)
				del RequestFlicker.servicesRegistered[self.serviceName]
				return
				
			if self.role == Role.REQUESTER:	
				if hasattr(self, 'requestId'):
					print 'Requester {} disconnected'.format(self.requestId)
					del RequestFlicker.pendingRequest[self.requestId]
				else :				
					print 'Requester disconnected'
				return
				
			print 'NotSet disconnected'
		except Exception,e:
			print 'Exception while handling close'
			print str(e)
			
#Helpers methods
def getAnwser(string):
	if is_json(string):
		data = json.loads(string)
		if (('id' not in data) or not isinstance(data['id'], (int, long)) or ('answer' not in data) or (IsNull(data['answer']))):
			return None		
		else:
			return data
	else:
		return None
		
def getRequest(string):
	if is_json(string):
		data = json.loads(string)
		if (('service' not in data) or (IsNull(data['service'])) or ('request' not in data) or (IsNull(data['request']))):
			return None		
		else:
			return data
	else:
		return None

def getRegistrationName(msg):
	if msg.startswith('\\\\') and  len(msg) > 2:
		return msg[2:]
	else:
		return None
		

def is_json(myjson):
  try:
	json_object = json.loads(myjson)
  except ValueError, e:
	return False
  return True
  
def IsNull(value):
	return value is None or len(value) == 0
	
def getErrorMessage(error):
	msg = {}
	msg['error'] = error
	return json.dumps(msg)
	
class Role:
    NOT_SET = 0
    REQUESTER = 1
    SERVICE = 2
	
server = SimpleWebSocketServer('', 8181, RequestFlicker)
server.serveforever()