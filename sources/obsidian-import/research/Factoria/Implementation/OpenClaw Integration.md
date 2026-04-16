Excellent — **Option A is the correct architecture** for Factoria.  
It keeps the system **secure, modular, and production-ready**.

You will now have a **3-service architecture**:

Factoria API  
      │  
      ▼  
OpenClaw Gateway  
      │  
      ▼  
Agent Runtime

Later we will add the **Runner service**, making the full system:

           +------------------+  
           |   Factoria API   |  
           | (workflow brain) |  
           +---------+--------+  
                     │  
                     ▼  
           +------------------+  
           |  OpenClaw Gateway|  
           |  (agent runtime) |  
           +---------+--------+  
                     │  
                     ▼  
           +------------------+  
           |   Runner Service |  
           |  (dbt / SQL / GH)|  
           +------------------+

This separation is **critical for security** because agents cannot directly execute infrastructure operations.



# 2 config files required - docker issues

You will likely end up with **two config files**, and they serve different purposes.

---

# 1️⃣ `config.json` (Gateway Runtime Config)

This is the file we just mounted:

gateway/openclaw/config.json

Mounted to:

/home/node/.openclaw/config.json

This controls **gateway runtime behaviour**, like:

- bind address
    
- auth
    
- control UI
    
- ports
    
- logging
    

Example:

{  
  "gateway": {  
    "bind": "lan",  
    "controlUi": {  
      "dangerouslyAllowHostHeaderOriginFallback": true  
    }  
  }  
}

This file is **required for Docker deployment**.

---

# 2️⃣ `openclaw.config.json` (Agent Platform Config)

This file configures **the OpenClaw agent runtime**.

It defines things like:

- default model
    
- tool policies
    
- sandboxing
    
- agent limits
    
- extensions
    

Example structure:

{  
  "agents": {  
    "defaults": {  
      "model": "anthropic/claude-opus-4-6",  
      "sandbox": true  
    }  
  }  
}

This is the file **your agents will rely on later**.