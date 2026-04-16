- Creating/updating the power bi models - Prod Model takeover.
	- test is done, prod not taken over yet.
- Go through inventory and understand pipeline to be able to work on the modelling ticket.
	- maybe schedule call with Justin - to drilldown details
- Check google Ads ticket.
	- Get it prepped to move forward with implementation
	- Windsor approach or connector approach ?
	- this is how we do google for fusion
	- could rate limiting be an issue if they share cred with us and both of us are using it.
	- Prefect-Native connector (maybe no need for windsor)
- **Windsor:**
	- Shutting off of Windsor templates?
		-  to prevent dupes - maybe not required
	- Setup alias account invite GEP to login:
		- GEP manage accounts that we give them
		- They can control what ads get pulled in and other settings.
- Ping Lori if there is no update ht-pet ticket on kanban board.

- email related to flight check issue


Outline full detailed steps for developing and deploying changes in the data warehouse (clients repo)
- dynamic tables
- task graphs that need to be run
- is table definition just manually run in snowflake ui to deploy?
	- code merge currently does not trigger a deploy.