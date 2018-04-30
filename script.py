from datetime import datetime
from subprocess import call, PIPE
import array
import fcntl
import gc
import os
import socket
import struct
import sys
import time
import urllib2

jitter = 1

def test(name, op):
	sys.stdout.write('Testing ' + name + '...')

	spacing = 80 - 8 - 3 -3 - len(name)
	if spacing > 0:
		sys.stdout.write(' ' * spacing)

	sys.stdout.flush()

	try:
		op()
		print '[X]'
	except Exception as ex:
		print '[ ]'
		if len(str(ex)) > 0:
			print '\n\tFailed: ' + str(ex) + '\n'

def check(code):
	if code != 0:
		raise Exception('Return code was ' + str(code))

def invoke():
	check(call(['ls', '-l'], stdout=PIPE))

def background():
	start = datetime.now()
	check(call(['sleep', str(jitter)]))
	end = datetime.now()

	diff = end - start
	elapsed = (diff.days * 86400000) + (diff.seconds * 1000) + (diff.microseconds / 1000)

	# Super-generous tolerance check
	if elapsed < 950:
		raise Exception('Expected 1 second elapsed, was ' + str(elapsed))

def large_file():
	try:
		os.remove('large_file')
	except:
		pass

	check(call(['dd if=/dev/zero iflag=count_bytes count=1G bs=1M of=large_file; sync'], stdout=PIPE, stderr=PIPE, shell=True))

	size = os.path.getsize('large_file')
	os.remove('large_file')

	if size < 1024000000:
		raise Exception('Expected 1 GB file, was ' + str(size))

def large_mem():
	def alloc():
		some_str = ' ' * 1024000000
		time.sleep(jitter)

	alloc()
	gc.collect()

def nonexistent_command():
	code = call(['wat'], stdout=PIPE, stderr=PIPE, shell=True)
	if code == 0:
		raise Exception("Nonexistent command exited 0")

def output_folder():
	if not os.path.isdir('output'):
		raise Exception('Output dir missing')

	filename = 'output/output-test.txt'
	open(filename, 'wb').write('This is a test\n')

	contents = open(filename, 'r'). read()

	if contents != 'This is a test\n':
		raise Exception("Contents were not correct: " + str(contents))

def root_file():
	filename = '/root-test.txt'
	open(filename, 'wb').write('This is a test\n')

	contents = open(filename, 'r'). read()

	if contents != 'This is a test\n':
		raise Exception("Contents were not correct: " + str(contents))

def invalid_fs():
	check(call(['mkdir /invalid; chown -R $RANDOM:$RANDOM /invalid; touch /invalid/file;'], stdout=PIPE, stderr=PIPE, shell=True))

# Get interfaces. Source:
# https://gist.github.com/pklaus/289646
def all_interfaces():
	max_possible = 128  # arbitrary. raise if needed.
	bytes = max_possible * 32
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	names = array.array('B', '\0' * bytes)
	outbytes = struct.unpack('iL', fcntl.ioctl(
		s.fileno(),
		0x8912,  # SIOCGIFCONF
		struct.pack('iL', bytes, names.buffer_info()[0])
	))[0]
	namestr = names.tostring()
	lst = []
	for i in range(0, outbytes, 40):
		name = namestr[i:i+16].split('\0', 1)[0]
		ip   = namestr[i+20:i+24]
		lst.append((name, ip))
	return lst

def interface():
	ifs = all_interfaces()
	found = False

	for i in ifs:
		if i[0] != 'lo':
			found = True

	if not found:
		raise Exception("Non-lookback interface not found")

def dns():
	socket.gethostbyname('google.com')

def tcp():
	contents = urllib2.urlopen("http://google.com").read()

	if len(contents) < 10:
		raise Exception("No content in response")
	elif 'html' not in contents.lower():
		raise Exception("Response is not HTML")


def main():
	test('basic command', invoke)
	test('background control', background)
	test('allocate large file', large_file)
	test('allocate large mem', large_mem)
	test('nonexistent command', nonexistent_command)
	test('output folder', output_folder)
	test('root folder', root_file)
	test('invalid fs', invalid_fs)
	test('network interface', interface)
	test('network DNS', dns)
	test('network TCP', tcp)

	sys.stdout.write('')
	sys.stdout.flush()

if __name__ == "__main__":
    main()
