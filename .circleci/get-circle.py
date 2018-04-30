#!/usr/bin/env python

import argparse
import json
import os
import requests
import shutil
import stat

"""
Download an asset from the latest build of a branch of CircleCI artifacts.
"""

def get_artifacts(token, repo, branch):
	r = requests.get(
		'https://circleci.com/api/v1.1/project/' + repo + '/latest/artifacts',
		params={ 'circle-token': token, 'branch': branch, 'filter': 'successful' }
	)
	r.raise_for_status()

	return r.json()

def find_artifact(token, repo, branch, path):
	artifacts = get_artifacts(token, repo, branch)

	for artifact in artifacts:
		if artifact['path'] == path:
			return artifact

	raise Exception('Artifact ' + path + ' not found')

def download_artifact(token, repo, branch, path, dest, ex):
	artifact = find_artifact(token, repo, branch, path)
	url = artifact['url']

	if dest is None:
		dest = os.path.basename(path)

	r = requests.get(
		url,
		params={ 'circle-token': token },
		stream=True
	)
	r.raw.decode_content = True
	r.raise_for_status()

	f = open(dest, 'wb')
	shutil.copyfileobj(r.raw, f)
	f.close()

	if ex:
		st = os.stat(dest)
		os.chmod(dest, st.st_mode | stat.S_IEXEC)

def pretty(obj):
	return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))

def main():
	parser = argparse.ArgumentParser(description='Download a CircleCI artifact.')
	parser.add_argument('--token',  help='CircleCI token')
	parser.add_argument('--repo',   help='Artifact repository')
	parser.add_argument('--path',   help='Artifact path')
	parser.add_argument('--branch', help='Artifact branch', default='master')
	parser.add_argument('--dest',   help='Local path')
	parser.add_argument('--ex',     help='Mark executable', action='store_true')
	args = parser.parse_args()

	if args.path is None:
		artifacts = get_artifacts(args.token, args.repo, args.branch)
		print pretty(artifacts)
	else:
		download_artifact(args.token, args.repo, args.branch, args.path, args.dest, args.ex)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		pass
