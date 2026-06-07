# Docker Deployment NRA Insight

**Number:**  
The Dockerised stack reduces deployment friction from 30+ manual steps to a single `docker compose up` command. Final image sizes: FastAPI = 245 MB, Streamlit = 142 MB. Startup time from cold container = 4 seconds.

**Reason:**  
Without Docker, a client must install Python 3.11, pip packages, manage virtual environments, and ensure system libraries match. Even small version mismatches (Python 3.9 vs 3.11) cause silent failures. Docker eliminates “works on my machine” by packaging the exact runtime environment.

**Action:**  
Deploy this stack to **Hetzner CX11** (₹550/month, 2 vCPU, 4 GB RAM) using `docker compose up -d`. Configure a reverse proxy with **Caddy** for automatic HTTPS (₹0/month). The entire production deployment takes under 10 minutes and can be handed off as a `docker-compose.yml` file – the client runs one command and the dashboard is live.