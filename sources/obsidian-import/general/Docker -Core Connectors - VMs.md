#core #connectors #deployment #docker #agents

# General Process
1. `$ ssh aldc@workstation-agent` for the server to build the agents.
	1. `cd docker_build/agent-template-env`
	2. `cp <desired-config>.json config.json` - This will be `config-test.json` or other config depending on where you are deploying. These are different for test, prod Kamloops, prod Coquitlam, and QA.
		2. Check the file to ensure some values make sense. E.g.:
			1. `sleep = 600`
			2. `thread_timeout = 3600`
			3. `max_threads > 1`
			4. `target_host` is the correct URL for the environment you are deploying to.
	3. `$ sudo ./build.sh` and follow the instructions to build the image. **NOTE** the script execution will take some time.
		1. You will set an agent like `dcgeneral`
			1. Make sure if the deployment is to Prod that you make an image for both targets. One for Kamloops and one for Coquitlam. They need to be different.
		2. Branch like `master` or `1.24.0`
		3. Version like `1.24.0`
			1. **NOTE** that if you use the same name as the existing one it will overwrite it.
			2. So, if you are making intermediate changes to test a new set of changes, deploying a new 'release', or just want to keep the previous version in the GitHub container registry you need to make the name unique.
				1. Usually, this is either `1.24.0` to `1.24.1` or adding a suffix like `1.24.0-itm-250`.
		4. The build also pushes it to the container registry
			1. You can check [https://github.com/orgs/ALDC-io/packages/container/package/agent-dcgeneral](https://github.com/orgs/ALDC-io/packages/container/package/agent-dcgeneral) to see that the image was checked in properly.
2. Log into Portainer
	1. Get the URL for the server you want to deploy to
		1. Note that there are separate servers for test, prod Kamloops, prod Coquitlam, and QA.
3. `$ ssh aldc@<URL>` for the server that will run the agents.
	1. `cd docker_assets/images/agent_template`
		1. This will change depending on the server as they appear to all be setup slightly differently. **TODO** find the locations for each server and list them.
	2. There are a different number of agents depending on the environment.
		1. 4 for test and prod Kamloops
		2. 3 for prod Coquitlam
		3. 1 for QA
	3. Repeat the following for all agents:
		1. Shut down an agent in Portainer. Keep the old one as a backup and delete the previous old one that was not running (provided things are stable).
		2. on the server `$ sudo ./run.sh`
		3. Set the image you want to pull, using the info set up when building the agent. E.g. `agent-dcgeneral:1.24.0`
			1. You can grab the agent name from the workstation terminal tab.
		4. Set the name that will represent the container in the list. This generally follows the patter `agent<n>-<version>`. E.g. `agent1-1.24.0`
		5. Finish instructions... This will create and start the container.
			1. For normal agents just hit enter when asked for options
			2. For **GEP seller cloud** agent set the options according to what is in the Dashlane Secret for options.
				1. **FIRST** enter the option name, for `gep-sellercloudvpn` the script option is `openvpn`
				2. You input the option name and hit Enter
				3. You input the value and hit Enter
				4. Do this until all are added and then type `exit`
		6. Repeat until all new agents are created, usually 4
4. You can check the logs for agents to make sure they are working properly.

# Extra Steps
There can be some extra steps, or situations that are not part of the general deployment that can come up.
## Docker Login
I have had the portion of the build process where a container is pushed to the container registry.
- The issue was that the docker cli was not logged in properly anymore

To log in again the general steps are:
1. `export DOCKER_CLI_TOKEN=<token from github>`
2. `echo $DOCKER_CLI_TOKEN | sudo docker login ghcr.io --username <github-username-of-token-account> --password-stdin`
	1. **Note** that the use of `sudo` in the command means you need to have authenticated `sudo` already so that it doesn't ask for a password. Otherwise the pipe will put your token in that password prompt.

You can go to developer settings and create tokens for GitHub that are used for this login. The `aldc-svc-automation` account is the one that should be used, but if problems are encountered you can create a personal token and authenticate on `workstation-agent` or a server with your personal account.