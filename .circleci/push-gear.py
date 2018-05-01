#!/usr/bin/env python

from subprocess import call, check_output
import os
import json

import flywheel


"""
Push a gear, possibly changing the version while doing so.
"""

manifest_path = 'manifest.json'

def check(code):
	if code != 0:
		raise Exception('Return code was ' + str(code))

def load_json_from_file(path):
	contents = open(path).read()
	return json.loads(contents)

def write_json_to_file(path, obj):
	handle = open(manifest_path, 'w')
	handle.write(pretty(obj))
	handle.close()

def pretty(obj):
	return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))

def main():
	key = os.environ.get('FlywheelKey')
	fw = flywheel.Flywheel(key)

	manifest = load_json_from_file(manifest_path)
	name = manifest['name']
	version = manifest['name']
	new_version = version

	for gear in fw.get_all_gears():
		if gear['gear']['name'] == name:
			new_version = int(gear['gear']['version']) + 1

	if new_version != version:
		print 'New gear version will be ' + str(new_version)

		manifest['version'] = str(new_version)
		write_json_to_file(manifest_path, manifest)

	if os.environ.get('CIRCLE_BRANCH') == 'master':
		check(call(['fw', 'gear', 'upload']))

	else:
		print 'Not running on master, so not pushing.'


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		pass
