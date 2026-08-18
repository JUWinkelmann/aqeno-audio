.PHONY: pi-dev pi-deploy pi-ssh pi-status pi-logs pi-logs-once pi-restart pi-health pi-diagnostics

pi-dev:
	./deploy/rh1/remote.sh dev

pi-deploy:
	./deploy/rh1/remote.sh release

pi-ssh:
	./deploy/rh1/remote.sh ssh

pi-status:
	./deploy/rh1/remote.sh status

pi-logs:
	./deploy/rh1/remote.sh logs

pi-logs-once:
	./deploy/rh1/remote.sh logs-once

pi-restart:
	./deploy/rh1/remote.sh restart

pi-health:
	./deploy/rh1/remote.sh health

pi-diagnostics:
	./deploy/rh1/remote.sh diagnostics
