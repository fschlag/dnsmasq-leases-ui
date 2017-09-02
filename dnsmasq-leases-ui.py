from flask import Flask, render_template, jsonify
import datetime

DNSMASQ_LEASES_FILE = "/var/lib/misc/dnsmasq.leases"

app = Flask(__name__)

class LeaseEntry:
	def __init__(self, leasetime, macAddress, ipAddress, name):
		if (leasetime == '0'):
			self.staticIP = True
		else:
			self.staticIP = False
		self.leasetime = datetime.datetime.fromtimestamp(
			int(leasetime)
			).strftime('%Y-%m-%d %H:%M:%S')
		self.macAddress = macAddress.upper()
		self.ipAddress = ipAddress
		self.name = name

	def serialize(self):
		return {
			'staticIP': self.staticIP,
			'leasetime': self.leasetime,
			'macAddress': self.macAddress,
			'ipAddress': self.ipAddress,
			'name': self.name
		}

def leaseSort(arg):
	# Fixed IPs first
	if arg.staticIP == True:
		return 0
	else:
		return arg.name.lower()

@app.route("/")
def index():
	return render_template('index.html')

@app.route("/leases")
def getLeases():
	leases = list()
	with open(DNSMASQ_LEASES_FILE) as f:
		for line in f:
			elements = line.split()
			entry = LeaseEntry(elements[0],
					   elements[1],
					   elements[2],
					   elements[3])
			leases.append(entry)
	leases.sort(key = leaseSort)
	return jsonify(leases=[lease.serialize() for lease in leases])


if __name__ == "__main__":
	app.run("0.0.0.0")
