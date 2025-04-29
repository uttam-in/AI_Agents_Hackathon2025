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

// Anime-style Avatar components for the chat
const UserAvatar = () => (
  <div className={styles.avatar}>
    <div className={styles.userAvatarImage}>
      <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" width="50" height="50">
        <circle cx="50" cy="35" r="25" fill="#4a89dc" />
        <circle cx="40" cy="30" r="3" fill="white" />
        <circle cx="60" cy="30" r="3" fill="white" />
        <path d="M 40 45 Q 50 55 60 45" stroke="white" strokeWidth="2" fill="none" />
        <path d="M 25 30 Q 20 15 30 10" stroke="#4a89dc" strokeWidth="4" fill="none" />
        <path d="M 75 30 Q 80 15 70 10" stroke="#4a89dc" strokeWidth="4" fill="none" />
        <path d="M 30 85 Q 50 95 70 85 Q 80 70 70 60 L 30 60 Q 20 70 30 85" fill="#4a89dc" />
      </svg>
    </div>
    <div className={styles.avatarGlow}></div>
  </div>
);

const AIAvatar = () => (
  <div className={styles.avatar}>
    <div className={styles.aiAvatarImage}>
      <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" width="50" height="50">
        <circle cx="50" cy="35" r="25" fill="#00f2ff" />
        <circle cx="40" cy="30" r="3" fill="white" />
        <circle cx="60" cy="30" r="3" fill="white" />
        <path d="M 35 40 Q 50 45 65 40" stroke="white" strokeWidth="2" fill="none" />
        <path d="M 30 20 L 20 10" stroke="#00f2ff" strokeWidth="3" fill="none" />
        <path d="M 70 20 L 80 10" stroke="#00f2ff" strokeWidth="3" fill="none" />
        <path d="M 25 70 Q 50 85 75 70 Q 85 55 75 45 L 25 45 Q 15 55 25 70" fill="#00f2ff" />
        <circle cx="35" cy="30" r="8" fill="#00f2ff" stroke="white" strokeWidth="2" />
        <circle cx="65" cy="30" r="8" fill="#00f2ff" stroke="white" strokeWidth="2" />
        <circle cx="35" cy="30" r="2" fill="white" />
        <circle cx="65" cy="30" r="2" fill="white" />
      </svg>
    </div>
    <div className={styles.avatarGlow}></div>
  </div>
);

// Formatter for displaying different text options
const TextFormatOption = ({ text, active, onClick }: { text: string, active: boolean, onClick: () => void }) => (
  <button 
    className={`${styles.formatOption} ${active ? styles.activeFormatOption : ''}`} 
    onClick={onClick}
  >
    {text}
  </button>
);

// Radar animation that only shows when loading
const RadarAnimation = ({ loading }: { loading: boolean }) => (
  <div className={`${styles.radarContainer} ${loading ? styles.radarVisible : styles.radarHidden}`}>
    <div className={styles.radarCircle}></div>
    <div className={styles.radarSweep}></div>
  </div>
);

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

  // Text formatting options state
  const [textFormat, setTextFormat] = useState<'default' | 'code' | 'matrix'>('default');

  // Format options for the AI response
  const formatOptions = [
    { id: 'default', name: 'Default' },
    { id: 'code', name: 'Code Theme' },
    { id: 'matrix', name: 'Matrix' },
  ];

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

  // Setup resizable split container
  useEffect(() => {
    const chatContainer = document.getElementById('chat-container');
    const toolResultsContainer = document.querySelector(`.${styles.toolResultsContainer}`) as HTMLElement;
    const resizeHandle = document.getElementById('resize-handle');
    
    if (!chatContainer || !toolResultsContainer || !resizeHandle) return;
    
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;
    let containerWidth = 0;
    
    const startResize = (e: MouseEvent) => {
      isResizing = true;
      startX = e.clientX;
      startWidth = chatContainer.offsetWidth;
      containerWidth = chatContainer.parentElement?.offsetWidth || 0;
      resizeHandle.classList.add('active');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    };
    
    const resize = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const deltaX = e.clientX - startX;
      const newWidth = ((startWidth + deltaX) / containerWidth) * 100;
      
      // Limit minimum and maximum widths (20% - 80%)
      if (newWidth >= 20 && newWidth <= 80) {
        // Update widths and handle position
        chatContainer.style.width = `${newWidth}%`;
        toolResultsContainer.style.width = `${100 - newWidth}%`;
        resizeHandle.style.right = `${100 - newWidth}%`;
      }
    };
    
    const stopResize = () => {
      isResizing = false;
      resizeHandle.classList.remove('active');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    
    resizeHandle.addEventListener('mousedown', startResize);
    document.addEventListener('mousemove', resize);
    document.addEventListener('mouseup', stopResize);
    
    return () => {
      resizeHandle.removeEventListener('mousedown', startResize);
      document.removeEventListener('mousemove', resize);
      document.removeEventListener('mouseup', stopResize);
    };
  }, []);

  // Lightsaber logo component for the header
  const LightsaberLogo = () => (
    <div className={styles.lightsaberLogo}>
      <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" width="36" height="36">
        {/* Lightsaber handle */}
        <g className={styles.lightsaberHandle}>
          <rect x="40" y="60" width="20" height="30" rx="2" fill="#555" />
          <rect x="42" y="65" width="16" height="5" rx="1" fill="#333" />
          <rect x="42" y="75" width="16" height="5" rx="1" fill="#333" />
          <rect x="45" y="85" width="10" height="5" rx="1" fill="#222" />
          {/* Energy core */}
          <circle cx="50" cy="60" r="5" fill="#00dfff">
            <animate attributeName="opacity" values="0.7;1;0.7" dur="1.5s" repeatCount="indefinite" />
          </circle>
        </g>
        
        {/* Lightsaber blade with swinging motion */}
        <g className={styles.lightsaberBlade}>
          {/* Main blade */}
          <rect x="45" y="10" width="10" height="50" rx="5" fill="#00bfff">
            <animate attributeName="height" values="50;55;50" dur="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.8;1;0.8" dur="2s" repeatCount="indefinite" />
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="-5 50 60"
              to="5 50 60"
              dur="1.5s"
              repeatCount="indefinite"
              additive="sum"
              calcMode="spline"
              keySplines="0.5 0 0.5 1; 0.5 0 0.5 1"
              keyTimes="0; 0.5; 1"
            />
          </rect>
          
          {/* Inner glow */}
          <rect x="47" y="10" width="6" height="50" rx="3" fill="#80dfff" opacity="0.6">
            <animate attributeName="height" values="50;55;50" dur="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.6;0.8;0.6" dur="1.5s" repeatCount="indefinite" />
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="-5 50 60"
              to="5 50 60"
              dur="1.5s"
              repeatCount="indefinite"
              additive="sum"
              calcMode="spline"
              keySplines="0.5 0 0.5 1; 0.5 0 0.5 1"
              keyTimes="0; 0.5; 1"
            />
          </rect>
          
          {/* Outer glow */}
          <rect x="43" y="10" width="14" height="50" rx="7" fill="#00bfff" opacity="0.3">
            <animate attributeName="height" values="50;55;50" dur="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.3;0.5;0.3" dur="1.5s" repeatCount="indefinite" />
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="-5 50 60"
              to="5 50 60"
              dur="1.5s"
              repeatCount="indefinite"
              additive="sum"
              calcMode="spline"
              keySplines="0.5 0 0.5 1; 0.5 0 0.5 1"
              keyTimes="0; 0.5; 1"
            />
          </rect>
          
          {/* Motion blur effect */}
          <path d="M 45,10 Q 47,12 50,10 Q 53,12 55,10 L 55,58 Q 53,60 50,58 Q 47,60 45,58 Z" fill="#00bfff" opacity="0.2">
            <animate attributeName="opacity" values="0.1;0.2;0.1" dur="1s" repeatCount="indefinite" />
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="-8 50 60"
              to="8 50 60"
              dur="1.5s"
              repeatCount="indefinite"
              additive="sum"
              calcMode="spline"
              keySplines="0.5 0 0.5 1; 0.5 0 0.5 1"
              keyTimes="0; 0.5; 1"
            />
          </path>
          
          {/* Blade tip shine */}
          <circle cx="50" cy="10" r="5" fill="#ffffff" opacity="0.5">
            <animate attributeName="opacity" values="0.3;0.7;0.3" dur="2s" repeatCount="indefinite" />
            <animate attributeName="r" values="4;5;4" dur="2s" repeatCount="indefinite" />
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="-5 50 60"
              to="5 50 60"
              dur="1.5s"
              repeatCount="indefinite"
              additive="sum"
              calcMode="spline"
              keySplines="0.5 0 0.5 1; 0.5 0 0.5 1"
              keyTimes="0; 0.5; 1"
            />
          </circle>
        </g>
        
        {/* Strike effect (appears occasionally) */}
        <g className={styles.lightsaberStrike}>
          <path d="M 35,20 L 65,55" stroke="#ffffff" strokeWidth="2" opacity="0">
            <animate 
              attributeName="opacity" 
              values="0;0;0;0.8;0" 
              dur="5s" 
              repeatCount="indefinite"
              keyTimes="0;0.7;0.8;0.82;0.9" 
            />
          </path>
          <path d="M 35,55 L 65,25" stroke="#ffffff" strokeWidth="2" opacity="0">
            <animate 
              attributeName="opacity" 
              values="0;0;0;0;0.8;0" 
              dur="5s" 
              repeatCount="indefinite"
              keyTimes="0;0.75;0.85;0.86;0.88;0.95" 
            />
          </path>
        </g>
      </svg>
    </div>
  );

  return (
    <>
      <Head>
        <title>Jedi</title>
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
              <LightsaberLogo />
              <h1 className={styles.title}>Jedi</h1>
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
            </div>
          </div>
          
          <div className={styles.splitContainer}>
            {/* Resize handle */}
            <div className={styles.resizeHandle} id="resize-handle"></div>
            
            {/* Chat container - 60% width */}
            <div className={styles.chatContainer} id="chat-container">
              <div className={styles.messagesList}>
                {consolidatedMessages.map((message) => (
                  <div 
                    key={message.id} 
                    className={`${styles.message} ${
                      message.type === 'user' ? styles.userMessage : styles.assistantMessage
                    }`}
                  >
                    <div className={styles.messageName} data-name={message.type === 'user' ? 'User' : 'CyberSec AI'}>
                      {message.type === 'user' ? <UserAvatar /> : <AIAvatar />}
                    </div>
                    <div className={`${styles.messageContent} ${
                      message.type === 'assistant' && textFormat === 'code' ? styles.codeTheme : 
                      message.type === 'assistant' && textFormat === 'matrix' ? styles.matrixTheme : ''
                    }`}>
                      {message.type === 'user' ? (
                        message.content
                      ) : (
                        <>
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
                        </>
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
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
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
