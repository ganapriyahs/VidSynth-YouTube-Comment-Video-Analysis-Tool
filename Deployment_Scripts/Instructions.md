# Scripts to Showcase Deployment from Fresh State


## Prerequisites

1. **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
2. **Authenticated**: Run `gcloud auth login`
3. **Billing Account ID**: Creat and Find via `gcloud billing accounts list`

## Quick Start (Cloud Shell recommended)

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/vidsynth.git
cd vidsynth/Deployment_Scripts

# Make scripts executable
chmod +x *.sh

# 1. Run bootstrap (~5 min)
export BILLING_ACCOUNT="01XXXX-XXXXXX-XXXXXX"
./01-bootstrap.sh

# 2. Start tmux session (prevents Cloud Shell timeout)
tmux new -s deploy

# 3. Run deployment (~30 min total)
./02-deploy.sh

# If Cloud Shell disconnects, reconnect and run:
#   tmux attach -t deploy

# 4. When demo is complete, tear down
./99-teardown.sh
```

## Tmux Information:

Cloud Shell times out after ~20 minutes of idle time. The deployment script takes ~30 minutes (mostly waiting for Composer). Tmux creates a persistent session that keeps running even if your browser disconnects:

```bash
tmux new -s deploy      # Start new session named "deploy"
./02-deploy.sh          # Run script inside tmux

# If disconnected, reconnect to Cloud Shell then:
tmux attach -t deploy   # Reattach to see progress

# When done:
tmux kill-session -t deploy   # Clean up session
```