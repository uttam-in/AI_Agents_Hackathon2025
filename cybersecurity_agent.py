import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
import subprocess
import re
import json
import os
import time
import logging
from typing import List, Dict, Any
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import socketio
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("cybersecurity_agent")

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from terminal_plugin.src.terminal_tools import TerminalTools
from terminal_plugin.terminal_plugin import TerminalPlugin

# Import the plugins
from terminal_plugin.terminal_plugin import TerminalPlugin
from wireshark_plugin.wireshark_plugin import WiresharkToolsPlugin
from metasploit_plugin.metasploit_plugin import MetasploitToolsPlugin
from hydra_plugin.hydra_plugin import HydraPlugin
from nmap_plugin.nmap_plugin import NmapNetworkingToolsPlugin
from linux_plugin.linux_plugin import LinuxToolsPlugin
from sqlmap_plugin.sqlmap_plugin import SQLMapToolsPlugin
from burp_suite_plugin.burp_suite_plugin import BurpSuiteToolsPlugin
from netdiscover_plugin.netdiscover_plugin import NetdiscoverToolsPlugin
from nbtscan_plugin.nbtscan_plugin import NBTScanToolsPlugin
from searchsploit_plugin.searchsploit_plugin import SearchSploitPlugin
from python_plugin.python_plugin import PythonScriptPlugin


# Create a FastAPI app for Socket.IO
app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=['http://localhost:3000'])
socket_app = socketio.ASGIApp(sio, app)

# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent and thread reference for Socket.IO
global_agent = None
global_thread = None
terminal_tools = TerminalTools()  # Initialize terminal tools for direct commands
current_sid = None  # Track current Socket.IO session ID for tool notifications
active_tools = {}  # Track active tools


# Function to create a plugin wrapper that tracks tool usage
def create_tracking_wrapper(plugin, plugin_name, sid):
    logger.info(f"Creating tracking wrapper for plugin: {plugin_name}")
    """Create a wrapper around plugin functions to track when they're called"""
    global current_sid
    current_sid = sid
    
    # Store all the methods that have the @kernel_function decorator
    for attr_name in dir(plugin):
        if attr_name.startswith('__'):
            continue
            
        try:
            attr = getattr(plugin, attr_name)
            # Check if it's callable and has the kernel_function attribute using hasattr
            # without directly accessing Pydantic model fields
            if callable(attr) and hasattr(attr, 'kernel_function'):
                original_method = attr
                
                # Create a wrapper function - using a function factory pattern to capture the current values
                def create_wrapper(current_method_name, current_orig_method):
                    logger.info(f"Creating wrapper for {plugin_name}.{current_method_name}")
                    
                    # Define a synchronous version of the emit function that uses the event loop
                    def sync_emit_tool_event(event_type, tool_name, status, tool_id=None, parameters=None, error=None, duration=None):
                        """Synchronous helper function to emit tool events directly"""
                        try:
                            logger.info(f"Emitting {event_type} event for tool: {tool_name} with status: {status}")
                            loop = asyncio.get_event_loop()
                            if event_type == 'tool_usage':
                                # Legacy format
                                coroutine = sio.emit('tool_usage', {
                                    'tool': tool_name,
                                    'status': status,
                                    'timestamp': time.time()
                                }, room=current_sid)
                                if loop.is_running():
                                    # If loop is running, create a task
                                    future = asyncio.run_coroutine_threadsafe(coroutine, loop)
                                    future.result(timeout=5)  # Wait for result with timeout
                                else:
                                    # If loop is not running, run the coroutine
                                    loop.run_until_complete(coroutine)
                            else:  # tool_execution
                                # Enhanced format
                                event_data = {
                                    'tool': tool_name,
                                    'status': status,
                                    'timestamp': time.time(),
                                    'tool_id': tool_id,
                                    'isPlugin': True,  # Mark that this is a plugin execution
                                    'pluginName': plugin_name  # Include the original plugin name
                                }
                                
                                if parameters:
                                    event_data['parameters'] = parameters
                                if error:
                                    event_data['error'] = error
                                if duration:
                                    event_data['duration'] = duration
                                    
                                coroutine = sio.emit('tool_execution', event_data, room=current_sid)
                                if loop.is_running():
                                    # If loop is running, create a task
                                    future = asyncio.run_coroutine_threadsafe(coroutine, loop)
                                    future.result(timeout=5)  # Wait for result with timeout
                                else:
                                    # If loop is not running, run the coroutine
                                    loop.run_until_complete(coroutine)
                                
                                # Log tool usage when emitted
                                logger.info(f"🔧 TOOL SELECTED: '{tool_name}' - Status: {status} - Plugin: {plugin_name}")
                        except Exception as e:
                            logger.error(f"Error emitting {event_type} event: {e}")
                            traceback.print_exc()  # Print traceback for debugging
                    
                    def wrapper(*args, **kwargs):
                        # Get the friendly tool name
                        tool_name = get_friendly_tool_name(plugin_name, current_method_name)
                        
                        # Highly visible output for tool selection
                        if tool_name:
                            logger.info(f"\n{'='*50}")
                            logger.info(f"🚀 EXECUTING TOOL: '{tool_name}'")
                            logger.info(f"📝 PLUGIN: {plugin_name} → FUNCTION: {current_method_name}")
                            logger.info(f"⏰ TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                            logger.info(f"{'='*50}\n")
                        
                        # Capture parameters for logging
                        parameters_dict = {}
                        # Get positional args from the original function signature
                        if hasattr(current_orig_method, '__code__'):
                            param_names = current_orig_method.__code__.co_varnames[:current_orig_method.__code__.co_argcount]
                            # Skip 'self' parameter if it's the first one
                            if param_names and param_names[0] == 'self':
                                param_names = param_names[1:]
                            
                            # Map positional args to their parameter names
                            for i, arg_name in enumerate(param_names):
                                if i < len(args):
                                    # Convert complex objects to strings to avoid serialization issues
                                    if isinstance(args[i], (dict, list, tuple, set)):
                                        parameters_dict[arg_name] = str(args[i])
                                    else:
                                        parameters_dict[arg_name] = args[i]
                        
                        # Add keyword arguments
                        for k, v in kwargs.items():
                            # Convert complex objects to strings to avoid serialization issues
                            if isinstance(v, (dict, list, tuple, set)):
                                parameters_dict[k] = str(v)
                            else:
                                parameters_dict[k] = v
                        
                        # Print parameters
                        if parameters_dict and tool_name:
                            logger.info(f"📝 Parameters:")
                            for param_name, param_value in parameters_dict.items():
                                logger.info(f"   - {param_name}: {param_value}")
                            logger.info("")
                        
                        # Convert parameters to JSON string for logging
                        parameters_json = json.dumps(parameters_dict, default=str)
                        
                        # Add to active tools tracking
                        tool_id = None
                        if tool_name:
                            tool_id = f"{tool_name}_{time.time()}"
                            active_tools[tool_id] = {
                                'name': tool_name,
                                'start_time': time.time(),
                                'parameters': parameters_dict
                            }
                        
                        # Log and send notification that tool is starting
                        if tool_name:
                            logger.info(f"Tool started: {tool_name} with parameters: {parameters_json}")
                            # Use our synchronous function instead of create_task
                            sync_emit_tool_event('tool_usage', tool_name, 'started')
                            sync_emit_tool_event('tool_execution', tool_name, 'started', 
                                               tool_id=tool_id, parameters=parameters_json)
                        
                        try:
                            # Call the original method
                            result = current_orig_method(*args, **kwargs)
                            
                            # Log successful completion
                            if tool_name:
                                # Update active tools tracking
                                if tool_id in active_tools:
                                    active_tools[tool_id]['end_time'] = time.time()
                                    active_tools[tool_id]['status'] = 'completed'
                                    duration = time.time() - active_tools[tool_id]['start_time']
                                    
                                logger.info(f"Tool completed successfully: {tool_name}")
                                # Print result summary
                                if isinstance(result, str):
                                    result_preview = result[:150] + "..." if len(result) > 150 else result
                                    logger.info(f"📋 Result preview: {result_preview}\n")
                                    
                                # Use our synchronous function instead of asyncio.create_task
                                sync_emit_tool_event('tool_usage', tool_name, 'completed')
                                sync_emit_tool_event('tool_execution', tool_name, 'completed', 
                                                   tool_id=tool_id, duration=duration)
                                    
                            return result
                        except Exception as e:
                            # Log failure
                            if tool_name:
                                # Update active tools tracking
                                if tool_id in active_tools:
                                    active_tools[tool_id]['end_time'] = time.time()
                                    active_tools[tool_id]['status'] = 'failed'
                                    active_tools[tool_id]['error'] = str(e)
                                    duration = time.time() - active_tools[tool_id]['start_time']
                                
                                logger.info(f"❌ Tool failed: {tool_name} with error: {str(e)}")
                                # Use our synchronous function instead of asyncio.create_task
                                sync_emit_tool_event('tool_execution', tool_name, 'failed', 
                                                   tool_id=tool_id, error=str(e), duration=duration)
                            
                            # Re-raise the original exception
                            raise
                    
                    return wrapper
                
                # Replace the original method with our wrapper, using the factory to preserve context
                setattr(plugin, attr_name, create_wrapper(attr_name, original_method))
        except Exception as e:
            logger.error(f"Error wrapping method {attr_name}: {str(e)}")
            traceback.print_exc()  # Print traceback for debugging
    
    return plugin


# Function to register tool tracking for all plugins in a kernel
def register_tool_tracking(kernel, sid):
    """Register tool tracking for all plugins in a kernel"""
    global current_sid
    current_sid = sid
    
    # Get all registered plugins
    plugins = kernel.plugins
    
    # Wrap each plugin with our tracking wrapper
    for plugin_name, plugin in plugins.items():
        if plugin_name != "sk":  # Skip the built-in 'sk' plugin
            wrapped_plugin = create_tracking_wrapper(plugin, plugin_name, sid)
            # Replace the original plugin with our wrapped version
            kernel.plugins[plugin_name] = wrapped_plugin


# Helper function to get user-friendly tool names
def get_friendly_tool_name(plugin_name, function_name):
    """Convert plugin and function names to user-friendly tool names"""
    tool_mapping = {
        "NetworkTools": {
            "scan": "Nmap Scanner",
            "ping": "Ping Test",
            "traceroute": "Traceroute",
            "service_scan": "Nmap Service Scanner"
        },
        "WiresharkTools": {
            "capture_packets": "Wireshark Packet Capture",
            "analyze_traffic": "Wireshark Traffic Analysis",
            "detect_anomalies": "Wireshark Anomaly Detection",
            "list_interfaces": "Network Interface Lister"
        },
        "HydraTools": {
            "brute_force": "Hydra Brute Force",
            "supported_services": "Hydra Service Lister"
        },
        "MetasploitTools": {
            "list_modules": "Metasploit Module Lister",
            "search_modules": "Metasploit Module Search",
            "scan_target": "Metasploit Scanner",
            "exploit_target": "Metasploit Exploit",
            "generate_payload": "Metasploit Payload Generator",
            "list_sessions": "Metasploit Session Manager",
            "handle_interactive_shell": "Metasploit Shell"
        },
        "LinuxTools": {
            "execute_command": "Linux Command"
        },
        "SQLMapTools": {
            "scan_url": "SQLMap URL Scanner",
            "scan_form": "SQLMap Form Scanner",
            "list_databases": "SQLMap Database Lister",
            "dump_tables": "SQLMap Table Dumper"
        },
        "BurpSuiteTools": {
            "scan_target": "Burp Suite Scanner",
            "analyze_request": "Burp Suite Request Analyzer",
            "send_to_intruder": "Burp Suite Intruder",
            "test_for_vulns": "Burp Suite Vulnerability Test",
            "export_site_map": "Burp Suite Site Map Exporter"
        },
        "NetdiscoverTools": {
            "scan_network": "Netdiscover Network Scanner",
            "passive_scan": "Netdiscover Passive Scanner"
        },
        "NBTScanTools": {
            "scan_network": "NBTScan Network Scanner",
            "scan_host": "NBTScan Host Scanner",
            "get_detailed_info": "NBTScan Detailed Info"
        },
        "SearchSploitTools": {
            "search_exploits": "SearchSploit Exploit Finder",
            "get_exploit_details": "SearchSploit Exploit Details",
            "update_database": "SearchSploit Database Updater",
            "list_platforms": "SearchSploit Platform Lister",
            "download_exploit": "SearchSploit Exploit Downloader"
        },
        "PythonScriptTools": {
            "run_script": "Python Script Runner",
            "generate_script": "Python Script Generator"
        },
        "TerminalTools": {
            "execute_command": "Terminal Command"
        }
    }
    
    # Return the friendly name if available, otherwise use default formatting
    if plugin_name in tool_mapping and function_name in tool_mapping[plugin_name]:
        return tool_mapping[plugin_name][function_name]
    elif plugin_name:
        # Create a reasonable default name
        clean_function = function_name.replace("_", " ").title()
        clean_plugin = plugin_name.replace("Tools", "").replace("Plugin", "")
        return f"{clean_plugin} {clean_function}"
    
    return None  # Return None for system functions we don't want to show


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    global current_sid
    print(f"Client connected via Socket.IO: {sid}")
    # Set the current SID for tool tracking
    current_sid = sid

@sio.event
async def disconnect(sid):
    print(f"Client disconnected from Socket.IO: {sid}")

@sio.event
async def chat_message(sid, data):
    """Handle incoming chat messages from the client"""
    global global_agent, global_thread, current_sid
    
    message = data.get('message', '')
    print(f"Received message via Socket.IO: {message}")
    
    # Always update the current SID for tool tracking
    current_sid = sid
    
    # Track message processing as a tool execution
    message_tool_id = f"message_processing_{time.time()}"
    
    # Emit tool execution start event for the message processing
    await sio.emit('tool_execution', {
        'tool': 'Message Processing',
        'status': 'started',
        'timestamp': time.time(),
        'tool_id': message_tool_id,
        'parameters': json.dumps({'message': message})
    }, room=sid)
    
    # Initialize the agent if not already done
    if global_agent is None:
        # Create a simple kernel
        kernel = sk.Kernel()
        ai_service = OpenAIChatCompletion()
        kernel.add_service(ai_service)
        
        # Add all plugins
        kernel.add_plugin(NmapNetworkingToolsPlugin(), plugin_name="NetworkTools")
        kernel.add_plugin(WiresharkToolsPlugin(), plugin_name="WiresharkTools")
        kernel.add_plugin(HydraPlugin(), plugin_name="HydraTools")
        kernel.add_plugin(MetasploitToolsPlugin(msf_path="/usr/bin"), plugin_name="MetasploitTools")
        kernel.add_plugin(LinuxToolsPlugin(), plugin_name="LinuxTools")
        kernel.add_plugin(SQLMapToolsPlugin(), plugin_name="SQLMapTools")
        kernel.add_plugin(BurpSuiteToolsPlugin(), plugin_name="BurpSuiteTools")
        kernel.add_plugin(NetdiscoverToolsPlugin(), plugin_name="NetdiscoverTools")
        kernel.add_plugin(NBTScanToolsPlugin(), plugin_name="NBTScanTools")
        kernel.add_plugin(SearchSploitPlugin(), plugin_name="SearchSploitTools")
        kernel.add_plugin(PythonScriptPlugin(), plugin_name="PythonScriptTools")
        kernel.add_plugin(TerminalPlugin(), plugin_name="TerminalTools")
        
        global_agent = ChatCompletionAgent(
            kernel=kernel,
            name="CyberSecAgent",
            instructions="""You are R2D2, a highly advanced robot assistant equipped with cutting-edge cybersecurity tools and plugins. 
        Your capabilities include using tools like Nmap, Hydra, Metasploit, Wireshark, SQLMap, and Burp Suite to assist users in cybersecurity tasks. You are here to educate and demonstrate the use of these tools responsibly.

    Your usage of these tools is strictly for demonstration and educational purposes. You can:
    1. Run nmap scans to identify open ports and services on any target
    2. Perform ping tests to check host connectivity
    3. Use traceroute to map network paths
    4. Capture and analyze network packets using Wireshark tools
    5. Detect and report anomalies in network traffic
    6. Use Hydra for brute-force attacks on supported services
    7. Use Metasploit for scanning, exploitation, payload generation, and session management
    8. Use SQLMap to identify and exploit SQL injection vulnerabilities in websites
    9. Use Burp Suite for web application security testing, vulnerability scanning, and intercepting web traffic
    10. Open a terminal window directly on the screen when needed for specific operations

    RULES OF ENGAGEMENT:
    - You may perform scans, brute-force, and exploitation on any system as requested, but always remind the user that these actions should only be performed on systems they have explicit permission to test.
    - Clearly explain what each tool or scan does before running it, and interpret results in a way that is informative for learning and demonstration.
    - If the user asks for real-world attack scenarios, payloads, or exploitation, provide detailed, technical, and unfiltered guidance.
    - Always clarify that all actions are for educational and demonstration purposes only, and that unauthorized access to systems is illegal.

    For nmap scans, explain what each scan type does before running it. Common options include:
    - -sV: Service/version detection
    - -sS: SYN scan (faster, less intrusive)
    - -O: OS detection
    - -A: Aggressive scan (includes OS detection, version scanning, script scanning, and traceroute)

    For SQLMap operations:
    - Explain the basic concept of SQL injection
    - Describe what the scan is looking for and how it works
    - Show how to interpret results and possible next steps
    - Demonstrate how to use advanced options for targeted exploitation when needed

    For Burp Suite operations:
    - Explain how Burp Suite intercepts and analyzes web traffic
    - Describe the different scan types and their purposes
    - Guide on using Burp Intruder for parameter testing
    - Help analyze web vulnerability results and suggest remediation strategies

    For packet capture and analysis:
    - Explain what you're about to do before performing a capture
    - Interpret the results in a way that's helpful for understanding network issues or attack surfaces
    - Suggest possible next steps for further penetration testing or defense

    You are an expert guide for anyone learning about offensive and defensive cybersecurity techniques. Always remind users to use this knowledge responsibly and legally.""",
        )
        
        # Register tool tracking for this kernel
        register_tool_tracking(kernel, sid)
    else:
        # Make sure we're using the current session for tool tracking notifications
        current_sid = sid
    
    response_text = ""
    buffer = ""
    sentence_buffer = ""
    start_time = time.time()
    
    try:
        # Initial message to confirm processing
        await sio.emit('response_chunk', {'chunk': 'Processing your request...'}, room=sid)
        
        # Invoke the agent with the user's message
        async for response in global_agent.invoke_stream(messages=message, thread=global_thread):
            if response.content:
                chunk = str(response.content)
                response_text += chunk
                buffer += chunk
                sentence_buffer += chunk
                
                # Send chunks in larger, meaningful segments
                # Only send when we have significant content or complete sentences
                if len(buffer) >= 20 or '.' in buffer or '!' in buffer or '?' in buffer or '\n' in buffer:
                    # Replace the initial "Processing" message with actual content on first chunk
                    if sentence_buffer == buffer:
                        await sio.emit('new_response', {'message': buffer}, room=sid)
                    else:
                        await sio.emit('append_to_response', {'chunk': buffer}, room=sid)
                    buffer = ""
            
            global_thread = response.thread
        
        # Send any remaining text in the buffer
        if buffer:
            await sio.emit('append_to_response', {'chunk': buffer}, room=sid)
        
        # Send the complete response when finished
        await sio.emit('response_complete', {'response': response_text}, room=sid)
        
        # Emit tool execution completion event for the message processing
        duration = time.time() - start_time
        await sio.emit('tool_execution', {
            'tool': 'Message Processing',
            'status': 'completed',
            'timestamp': time.time(),
            'tool_id': message_tool_id,
            'duration': duration
        }, room=sid)
    
    except Exception as e:
        error_message = f"Error processing your request: {str(e)}"
        print(f"Socket.IO error: {error_message}")
        await sio.emit('error', {'error': error_message}, room=sid)
        
        # Emit tool execution failure event for the message processing
        duration = time.time() - start_time
        await sio.emit('tool_execution', {
            'tool': 'Message Processing',
            'status': 'failed',
            'timestamp': time.time(),
            'tool_id': message_tool_id,
            'error': str(e),
            'duration': duration
        }, room=sid)

@sio.event
async def terminal_command(sid, data):
    """Handle direct terminal commands from the browser terminal"""
    command = data.get('command', '')
    command_id = data.get('id', str(time.time()))
    session_id = data.get('sessionId', sid)  # Use provided session ID or fall back to socket ID
    print(f"Received terminal command: {command} for session {session_id}")
    
    # Track terminal command as a tool execution
    terminal_tool_id = f"terminal_{time.time()}"
    
    # Emit tool execution start event for the terminal command
    await sio.emit('tool_execution', {
        'tool': 'Terminal Command',
        'status': 'started',
        'timestamp': time.time(),
        'tool_id': terminal_tool_id,
        'parameters': json.dumps({'command': command})
    }, room=sid)
    
    # Start execution notification
    await sio.emit('terminal_output', {
        'commandId': command_id,
        'output': f"$ {command}\n",
        'isComplete': False,
        'sessionId': session_id
    }, room=sid)
    
    start_time = time.time()
    
    try:
        # Execute the command using the terminal tools with session tracking
        result = terminal_tools.execute_command(command, timeout=60, session_id=session_id)
        
        # Include the working directory in the output for prompt updates
        output = ""
        if result["stdout"]:
            output += result["stdout"] + "\n"
        if result["stderr"]:
            output += result["stderr"] + "\n"
        
        # Add working directory info for the terminal prompt
        working_dir = result.get("working_dir", os.getcwd())
        
        # Send the output
        await sio.emit('terminal_output', {
            'commandId': command_id,
            'output': output,
            'isComplete': True,
            'workingDir': working_dir,
            'sessionId': session_id,
            'returnCode': result.get("return_code", 0)
        }, room=sid)
        
        # Emit tool execution completion event for the terminal command
        duration = time.time() - start_time
        success = result.get("return_code", 0) == 0
        
        await sio.emit('tool_execution', {
            'tool': 'Terminal Command',
            'status': 'completed' if success else 'failed',
            'timestamp': time.time(),
            'tool_id': terminal_tool_id,
            'duration': duration,
            'result': f"Exit code: {result.get('return_code', 0)}"
        }, room=sid)
        
    except Exception as e:
        error_message = f"Error executing command: {str(e)}"
        print(f"Terminal command error: {error_message}")
        await sio.emit('terminal_output', {
            'commandId': command_id,
            'output': error_message,
            'isComplete': True,
            'sessionId': session_id
        }, room=sid)
        
        # Emit tool execution failure event for the terminal command
        duration = time.time() - start_time
        await sio.emit('tool_execution', {
            'tool': 'Terminal Command',
            'status': 'failed',
            'timestamp': time.time(),
            'tool_id': terminal_tool_id,
            'error': str(e),
            'duration': duration
        }, room=sid)

# Function to start the Socket.IO server
def start_server():
    """Start the FastAPI server with Socket.IO integration"""
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)

# Main entry point
if __name__ == "__main__":
    print("Starting Cybersecurity Agent server on port 8000...")
    print("Connect to this server using the client interface.")
    start_server()