- Can't use control UI via docker - due to openclaw security constraints 
**OpenClaw gateway is actually running successfully already.** 🎉  
The logs prove it.

The key lines:

[gateway] listening on ws://127.0.0.1:18789  
[browser/server] Browser control listening on http://127.0.0.1:18791/

This means:

✔ Gateway started  
✔ Agents can connect  
✔ No crash

The reason you **cannot access it from your browser** is simply this:

127.0.0.1 inside container ≠ 127.0.0.1 on host

OpenClaw is binding to **container loopback**, so Docker cannot expose it.

However — and this is important — **Factoria does not need host access to OpenClaw**.

Your architecture is meant to be:

Host  
│  
├─ FastAPI (localhost:8000)  
│  
└─ Docker network  
      │  
      ├─ factoria-api  
      │  
      └─ openclaw-gateway

Inside Docker, the API can reach OpenClaw via:

ws://openclaw:18789

So the gateway **already works for the real purpose**.