import Head from "next/head";
import { Geist, Geist_Mono } from "next/font/google";
import styles from "@/styles/Home.module.css";
import { ChainlitContext } from "@chainlit/react-client";
import { useContext, useState, useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Simple message interface
interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp?: number;  // Adding timestamp to sort messages
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
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
