# AI Agents Hackathon 2025 - CyberSecurity Agent

An advanced AI-powered cybersecurity assistant with integrated security tools and a modern React interface.

## Project Overview

This project implements an AI agent (R2D2) that can leverage various cybersecurity tools to perform security testing, network scanning, and vulnerability assessment. The system consists of:

1. **Python Backend**: A FastAPI server with Socket.IO integration that hosts the AI agent
2. **React Frontend**: A modern Next.js client application that provides a chat interface and terminal emulation
3. **Tool Plugins**: Various cybersecurity tool integrations (Nmap, Metasploit, Wireshark, etc.)

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm/yarn
- Kali Linux (recommended) or other Linux distribution with cybersecurity tools installed
- OpenAI API key for the AI functionality

## Getting Started

### Server Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AI_Agents_Hackathon2025.git
cd AI_Agents_Hackathon2025
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

4. Start the backend server:
```bash
python cybersecurity_agent.py
```

The server will start on port 8000 by default.

### Client Setup

1. Navigate to the client directory:
```bash
cd client
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Start the development server:
```bash
npm run dev
# or
yarn dev
```

The client will be available at http://localhost:3000

## Project Structure

```
AI_Agents_Hackathon2025/
├── client/                  # React client application (Next.js)
│   ├── public/              # Static assets
│   ├── src/                 # Frontend source code
│   ├── package.json         # Client dependencies
│   └── ...
├── *_plugin/                # Various cybersecurity tool plugins
│   ├── *_plugin.py          # Plugin entry point
│   └── src/                 # Plugin implementation
├── cybersecurity_agent.py   # Main Python backend server
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Features

- **AI-Powered Chat Interface**: Interact with the security agent through natural language
- **Integrated Terminal**: Execute commands directly from the interface
- **Tool Tracking**: Monitor tool execution status and results
- **Security Tool Integration**:
  - Nmap for network scanning
  - Wireshark for packet capture and analysis
  - Metasploit for vulnerability exploitation
  - Hydra for password cracking
  - SQLMap for SQL injection testing
  - Burp Suite for web application security testing
  - And many more tools...

## Development

### Adding New Plugins

To add a new tool plugin:

1. Create a new directory `your_tool_plugin/`
2. Implement the plugin in `your_tool_plugin/your_tool_plugin.py`
3. Add your plugin to the kernel in `cybersecurity_agent.py`

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

Copyright (c) 2025 AI Agents Hackathon Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgements

- This project was created during the AI Agents Hackathon 2025
- Special thanks to all the contributors and open-source projects that made this possible