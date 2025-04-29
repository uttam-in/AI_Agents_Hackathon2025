import Head from "next/head";
import { Geist, Geist_Mono } from "next/font/google";
import styles from "@/styles/Home.module.css";
import { ChainlitContext } from "@chainlit/react-client";
import React, { useContext, useState, useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import Terminal, { ColorMode, TerminalOutput, TerminalInput } from 'react-terminal-ui';
import Image from "next/image";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Decorative elements for cybersecurity visual effect
const HexagonGrid = () => (
  <div className={styles.hexGrid}></div>
);

const NetworkGraph = () => (
  <div className={styles.networkGraph}>
    <div className={styles.networkNode} style={{ top: '20%', left: '15%' }}></div>
    <div className={styles.networkNode} style={{ top: '45%', left: '25%' }}></div>
    <div className={styles.networkNode} style={{ top: '70%', left: '10%' }}></div>
    <div className={styles.networkNode} style={{ top: '15%', left: '75%' }}></div>
    <div className={styles.networkNode} style={{ top: '60%', left: '85%' }}></div>
    <div className={styles.networkConnection} style={{ top: '20%', left: '15%', width: '10%', transform: 'rotate(25deg)' }}></div>
    <div className={styles.networkConnection} style={{ top: '45%', left: '25%', width: '15%', transform: 'rotate(-10deg)' }}></div>
    <div className={styles.networkConnection} style={{ top: '15%', left: '75%', width: '10%', transform: 'rotate(-15deg)' }}></div>
    <div className={styles.networkConnection} style={{ top: '60%', left: '70%', width: '15%', transform: 'rotate(10deg)' }}></div>
  </div>
);

// Radar animation that only shows when loading
const RadarAnimation = ({ loading }: { loading: boolean }) => (
  <div className={`${styles.radarContainer} ${loading ? styles.radarVisible : styles.radarHidden}`}>
    <div className={styles.radarCircle}></div>
    <div className={styles.radarSweep}></div>
  </div>
);

// Live updating date/time display for the header
const HeaderDateTime = () => {
  const [dateTime, setDateTime] = useState(new Date());
  
  useEffect(() => {
    const timer = setInterval(() => {
      setDateTime(new Date());
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);
  
  return (
    <div className={styles.headerDateTime}>
      <div className={styles.time}>{dateTime.toLocaleTimeString()}</div>
      <div className={styles.date}>{dateTime.toLocaleDateString()}</div>
    </div>
  );
};

// Simple message interface
interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp?: number;  // Adding timestamp to sort messages
}

// Terminal command interface
interface TerminalCommand {
  id: string;
  command: string;
  output: string;
  timestamp: number;
  isComplete: boolean; // Whether the command execution is complete
  workingDir?: string; // Current working directory for the command
}

export default function Home() {
  // Get the client from the context (already initialized in _app.tsx)
  const client = useContext(ChainlitContext);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);
  
  // Terminal related states
  const [terminalCommands, setTerminalCommands] = useState<TerminalCommand[]>([]);
  const [terminalInput, setTerminalInput] = useState("");
  const [activeTab, setActiveTab] = useState<'analysis' | 'terminal'>('analysis');
  const [terminalProcessing, setTerminalProcessing] = useState(false);
  
  // Current assistant message being streamed
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState<Message | null>(null);

  // Tool results state
  const [toolResults, setToolResults] = useState<{
    title: string;
    content: string;
    timestamp: number;
  } | null>(null);

  // Connect to the Socket.IO server
  useEffect(() => {
    const socketInstance = io("http://localhost:8000", {
      transports: ["websocket"],
      autoConnect: true,
    });

    socketInstance.on("connect", () => {
      console.log("Connected to server");
      setConnected(true);
    });

    socketInstance.on("disconnect", () => {
      console.log("Disconnected from server");
      setConnected(false);
    });

    // Event for starting a new response message
    socketInstance.on("new_response", (data) => {
      console.log("New response:", data);
      const newMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: data.message
      };
      setCurrentAssistantMessage(newMessage);
      setMessages(prevMessages => [...prevMessages, newMessage]);
    });

    // Event for appending to an existing response message
    socketInstance.on("append_to_response", (data) => {
      console.log("Append to response:", data);
      setCurrentAssistantMessage(prevMessage => {
        if (prevMessage) {
          const updatedMessage = {
            ...prevMessage,
            content: prevMessage.content + data.chunk
          };
          
          // Update the message in the messages array
          setMessages(prevMessages => 
            prevMessages.map(message => 
              message.id === prevMessage.id ? updatedMessage : message
            )
          );
          
          return updatedMessage;
        }
        return prevMessage;
      });
    });

    // Legacy event handler for backwards compatibility
    socketInstance.on("response_chunk", (data) => {
      console.log("Received legacy chunk:", data);
      // Only handle this if we don't have a current message or it's the first chunk
      if (currentAssistantMessage === null) {
        if (data.chunk === 'Processing your request...') {
          // Don't create a message for the processing notification
          return;
        }
        
        // Create a new assistant message
        const newMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: data.chunk
        };
        setCurrentAssistantMessage(newMessage);
        setMessages(prevMessages => [...prevMessages, newMessage]);
      } else if (!data.chunk.includes('Processing your request...')) {
        // Update existing message but only for non-processing chunks
        setCurrentAssistantMessage(prevMessage => {
          if (prevMessage) {
            const updatedMessage = {
              ...prevMessage,
              content: prevMessage.content + data.chunk
            };
            
            // Update the message in the messages array
            setMessages(prevMessages => 
              prevMessages.map(message => 
                message.id === prevMessage.id ? updatedMessage : message
              )
            );
            
            return updatedMessage;
          }
          return prevMessage;
        });
      }
    });

    // Handle tool results
    socketInstance.on("tool_result", (data) => {
      console.log("Received tool result:", data);
      setToolResults({
        title: data.tool || "Tool Result",
        content: data.result,
        timestamp: Date.now()
      });
    });

    socketInstance.on("response_complete", (data) => {
      console.log("Response complete:", data);
      setLoading(false);
      setCurrentAssistantMessage(null);
    });

    socketInstance.on("error", (data) => {
      console.error("Server error:", data.error);
      // Display error message to user
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: `Error: ${data.error}`
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      setLoading(false);
      setCurrentAssistantMessage(null);
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Scroll to bottom when terminal commands change
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalCommands]);

  // Function to send message to backend
  const handleSendMessage = async () => {
    if (!messageInput.trim() || loading || !socket || !connected) return;
    
    // Create user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: messageInput
    };
    
    // Add user message to chat
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setMessageInput("");
    setLoading(true);
    
    try {
      // Send message to server via Socket.IO
      socket.emit('chat_message', { message: messageInput });
    } catch (error) {
      console.error('Error sending message:', error);
      setLoading(false);
    }
  };

  // Format code blocks in the message
  const formatMessage = (content: string) => {
    // Detect if content has code blocks
    const hasCodeBlock = content.includes('```');
    
    if (hasCodeBlock) {
      return content;
    }
    
    // For regular text, detect and format URLs
    return content.replace(
      /(https?:\/\/[^\s]+)/g, 
      url => `[${url}](${url})`
    );
  };

  // Add a state for consolidated messages
  const [consolidatedMessages, setConsolidatedMessages] = useState<Message[]>([]);
  
  // Consolidate assistant messages into single messages
  useEffect(() => {
    if (messages.length === 0) {
      setConsolidatedMessages([]);
      return;
    }
    
    const newConsolidatedMessages: Message[] = [];
    let currentGroup: Message | null = null;
    
    messages.forEach(message => {
      if (message.type === 'user') {
        // User messages are always individual
        newConsolidatedMessages.push({ ...message });
        currentGroup = null;
      } else {
        // For assistant messages, try to consolidate
        if (!currentGroup) {
          // Start a new group
          currentGroup = { ...message, timestamp: Date.now() };
          newConsolidatedMessages.push(currentGroup);
        } else {
          // Append to the current group if it's from the assistant
          currentGroup.content += ' ' + message.content;
          // Update the reference in the consolidated messages array
          newConsolidatedMessages[newConsolidatedMessages.length - 1] = { ...currentGroup };
        }
      }
    });
    
    setConsolidatedMessages(newConsolidatedMessages);
  }, [messages]);

  // Function to handle terminal command execution
  const handleTerminalCommand = async () => {
    if (!terminalInput.trim() || terminalProcessing || !socket || !connected) return;

    // Create a new terminal command object
    const newCommand: TerminalCommand = {
      id: Date.now().toString(),
      command: terminalInput,
      output: '',
      timestamp: Date.now(),
      isComplete: false
    };

    // Add the command to the list
    setTerminalCommands(prev => [...prev, newCommand]);
    setTerminalInput('');
    setTerminalProcessing(true);

    try {
      // Send the terminal command directly via Socket.IO
      socket.emit('terminal_command', { command: terminalInput });
    } catch (error) {
      console.error('Error sending terminal command:', error);
      
      // Update the command with error information
      setTerminalCommands(prev => 
        prev.map(cmd => 
          cmd.id === newCommand.id 
            ? { ...cmd, output: 'Error executing command: Connection error', isComplete: true }
            : cmd
        )
      );
      setTerminalProcessing(false);
    }
  };

  // Socket event handlers for terminal commands
  useEffect(() => {
    if (!socket) return;

    // Listen for terminal output events
    socket.on('terminal_output', (data) => {
      console.log('Received terminal output:', data);
      
      // Find the most recent incomplete command and update it
      const commandId = data.commandId || 
        terminalCommands.find(cmd => !cmd.isComplete)?.id;
      
      if (commandId) {
        setTerminalCommands(prev => 
          prev.map(cmd => 
            cmd.id === commandId
              ? { 
                  ...cmd, 
                  output: cmd.output + (data.output || ''), 
                  isComplete: data.isComplete || false,
                  workingDir: data.workingDir || cmd.workingDir, // Update working directory if provided
                  returnCode: data.returnCode
                }
              : cmd
          )
        );
        
        if (data.isComplete) {
          setTerminalProcessing(false);
          
          // Store the session ID received from the server
          if (data.sessionId) {
            localStorage.setItem('terminalSessionId', data.sessionId);
          }
        }
      }
    });

    return () => {
      socket.off('terminal_output');
    };
  }, [socket, terminalCommands]);

  // Initialize terminal session ID on component mount
  useEffect(() => {
    // Create and store a unique session ID for this terminal instance if not already present
    if (!localStorage.getItem('terminalSessionId')) {
      const sessionId = `term_${Date.now()}`;
      localStorage.setItem('terminalSessionId', sessionId);
    }
  }, []);

  return (
    <>
      <Head>
        <title>Cybersecurity AI Agent</title>
        <meta name="description" content="Advanced Cybersecurity AI Agent Interface" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div
        className={`${styles.page} ${geistSans.variable} ${geistMono.variable}`}
      >
        <div className={styles.aiBackgroundOverlay}></div>
        <HexagonGrid />
        <NetworkGraph />
        <RadarAnimation loading={loading} />
        <main className={styles.main}>
          {/* Header Bar with Status */}
          <div className={styles.headerBar}>
            <div className={styles.logoContainer}>
              <span className={styles.logoIcon}>🛡️</span>
              <h1 className={styles.title}>CyberSec Command Center</h1>
            </div>
            <div className={styles.statusBar}>
              <div className={styles.statusItem}>
                <span>System:</span>
                <span>Active</span>
              </div>
              <div className={styles.connectionStatus}>
                Status: {connected ? 
                  <span className={styles.connected}>Connected</span> : 
                  <span className={styles.disconnected}>Disconnected</span>
                }
              </div>
              <HeaderDateTime />
            </div>
          </div>
          
          <div className={styles.splitContainer}>
            {/* Chat container - 60% width */}
            <div className={styles.chatContainer}>
              <div className={styles.messagesList}>
                {consolidatedMessages.map((message) => (
                  <div 
                    key={message.id} 
                    className={`${styles.message} ${
                      message.type === 'user' ? styles.userMessage : styles.assistantMessage
                    }`}
                  >
                    <div className={styles.messageName}>
                      {message.type === 'user' ? 'User' : 'CyberSec AI'}
                    </div>
                    <div className={styles.messageContent}>
                      {message.type === 'user' ? (
                        message.content
                      ) : (
                        <div className={styles.markdownContent}>
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight, rehypeRaw]}
                            components={{
                              p: ({node, ...props}) => <p className={styles.paragraph} {...props} />,
                              pre: ({node, ...props}) => <pre className={styles.codeBlock} {...props} />,
                              code: ({node, inline, ...props}) => 
                                inline 
                                  ? <code className={styles.inlineCode} {...props} />
                                  : <code className={styles.code} {...props} />,
                              h1: ({node, ...props}) => <h1 className={styles.heading} {...props} />,
                              h2: ({node, ...props}) => <h2 className={styles.heading} {...props} />,
                              h3: ({node, ...props}) => <h3 className={styles.heading} {...props} />,
                              ul: ({node, ...props}) => <ul className={styles.list} {...props} />,
                              ol: ({node, ...props}) => <ol className={styles.list} {...props} />,
                              li: ({node, ...props}) => <li className={styles.listItem} {...props} />
                            }}
                          >
                            {formatMessage(message.content)}
                          </ReactMarkdown>
                          {message.type === 'assistant' && loading && message.id === currentAssistantMessage?.id && (
                            <span className={styles.cursorBlink}></span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && !currentAssistantMessage && (
                  <div className={styles.loadingContainer}>
                    <div className={styles.loadingDots}>
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              <div className={styles.inputContainer}>
                <input
                  type="text"
                  className={styles.input}
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Enter command or ask cybersecurity question..."
                  disabled={loading || !connected}
                />
                <button 
                  className={styles.sendButton}
                  onClick={handleSendMessage}
                  disabled={loading || !connected}
                >
                  Execute
                </button>
              </div>
            </div>
            
            {/* Tool results container - 40% width */}
            <div className={styles.toolResultsContainer}>
              {/* Tab navigation */}
              <div className={styles.tabsContainer}>
                <button 
                  className={`${styles.tabButton} ${activeTab === 'analysis' ? styles.activeTab : ''}`}
                  onClick={() => setActiveTab('analysis')}
                >
                  Analysis
                </button>
                <button 
                  className={`${styles.tabButton} ${activeTab === 'terminal' ? styles.activeTab : ''}`}
                  onClick={() => setActiveTab('terminal')}
                >
                  Terminal
                </button>
              </div>

              {/* Analysis tab content */}
              {activeTab === 'analysis' && (
                <>
                  <div className={styles.toolResultsHeader}>
                    <h2>{toolResults ? toolResults.title : 'Security Analysis'}</h2>
                    <span>{toolResults ? new Date(toolResults.timestamp).toLocaleTimeString() : ''}</span>
                  </div>
                  <div className={styles.toolResultsContent}>
                    {toolResults ? (
                      <div className={styles.markdownContent}>
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeHighlight, rehypeRaw]}
                          components={{
                            pre: ({node, ...props}) => <pre className={styles.codeBlock} {...props} />,
                            code: ({node, inline, ...props}) => 
                              inline 
                                ? <code className={styles.inlineCode} {...props} />
                                : <code className={styles.code} {...props} />
                          }}
                        >
                          {toolResults.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <div className={styles.noToolResults}>
                        <p>Awaiting security tool execution...</p>
                        <p>Use the agent to run security tools like nmap, metasploit, or other available tools.</p>
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* Terminal tab content */}
              {activeTab === 'terminal' && (
                <div className={styles.reactTerminalContainer}>
                  <Terminal
                    name="CyberSec Terminal"
                    colorMode={ColorMode.Dark}
                    prompt={terminalCommands.length > 0 && terminalCommands[terminalCommands.length-1]?.workingDir 
                      ? `${terminalCommands[terminalCommands.length-1].workingDir}$` 
                      : `~$`}
                    onInput={(terminalInput) => {
                      if (!terminalProcessing && connected) {
                        // Create command object
                        const newCommand: TerminalCommand = {
                          id: Date.now().toString(),
                          command: terminalInput,
                          output: '',
                          timestamp: Date.now(),
                          isComplete: false,
                          workingDir: terminalCommands.length > 0 && terminalCommands[terminalCommands.length-1]?.workingDir 
                            ? terminalCommands[terminalCommands.length-1].workingDir 
                            : '~'
                        };
                        
                        // Add to commands list
                        setTerminalCommands(prev => [...prev, newCommand]);
                        setTerminalProcessing(true);
                        
                        // Send to server
                        if (socket) {
                          socket.emit('terminal_command', { 
                            command: terminalInput,
                            id: newCommand.id,
                            sessionId: localStorage.getItem('terminalSessionId') || undefined
                          });
                        }
                      }
                      return true; // Returns true to indicate the command was handled
                    }}
                  >
                    <TerminalOutput>Welcome to the CyberSec Terminal. Type commands to interact with the server.</TerminalOutput>
                    <TerminalOutput>Type 'help' for available commands or use any standard Unix/Linux command.</TerminalOutput>
                    <TerminalOutput>Connected: {connected ? 'Yes ✓' : 'No ✗'}</TerminalOutput>
                    <TerminalOutput>---</TerminalOutput>
                    
                    {terminalCommands.map((cmd) => (
                      <React.Fragment key={cmd.id}>
                        <TerminalInput>{cmd.command}</TerminalInput>
                        {cmd.output && (
                          <TerminalOutput>
                            {cmd.output}
                          </TerminalOutput>
                        )}
                        {!cmd.isComplete && (
                          <TerminalOutput>
                            <span className={styles.processingIndicator}>Processing...</span>
                          </TerminalOutput>
                        )}
                      </React.Fragment>
                    ))}
                    
                    {terminalProcessing && (
                      <TerminalOutput>
                        <div className={styles.loadingDots}>
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </TerminalOutput>
                    )}
                  </Terminal>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
