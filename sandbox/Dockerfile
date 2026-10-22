FROM mcr.microsoft.com/playwright:v1.64.1-noble

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv python3-pip \
        xvfb x11vnc novnc websockify fluxbox \
        git curl jq unzip poppler-utils fonts-noto fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Browser automation over MCP; install the Chromium build its bundled Playwright expects.
ARG PLAYWRIGHT_MCP_VERSION=0.0.83
RUN npm install -g @playwright/mcp@${PLAYWRIGHT_MCP_VERSION} \
    && node "$(npm root -g)/@playwright/mcp/node_modules/playwright/cli.js" install chromium

RUN python3 -m venv /opt/agent \
    && /opt/agent/bin/pip install --no-cache-dir \
        "claude-agent-sdk==0.2.168" "fastapi==0.148.0" "uvicorn==0.54.0" "httpx==0.28.1" \
        pandas openpyxl reportlab requests beautifulsoup4

RUN useradd --create-home --shell /bin/bash saarthi
COPY agent_server /opt/agent_server
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER saarthi
WORKDIR /home/saarthi
ENV HOME=/home/saarthi \
    DISPLAY=:99 \
    PATH="/home/saarthi/.local/bin:/opt/agent/bin:$PATH" \
    PYTHONPATH=/opt

EXPOSE 8700 6080
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
