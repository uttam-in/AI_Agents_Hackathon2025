import Head from "next/head";
import { Geist, Geist_Mono } from "next/font/google";
import styles from "@/styles/Home.module.css";
import { ChainlitContext } from "@chainlit/react-client";
import { useContext, useState, useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";

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

    socketInstance.on("response_chunk", (data) => {
      console.log("Received chunk:", data);
      if (currentAssistantMessage === null) {
        // Create a new assistant message if it doesn't exist yet
        const newMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: data.chunk
        };
        setCurrentAssistantMessage(newMessage);
        setMessages(prevMessages => [...prevMessages, newMessage]);
      } else {
        // Update the existing message with the new chunk
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
          <h1 className={styles.title}>Cybersecurity AI Agent</h1>
          
          <div className={styles.connectionStatus}>
            Status: {connected ? 
              <span className={styles.connected}>Connected</span> : 
              <span className={styles.disconnected}>Disconnected</span>
            }
          </div>
          
          <div className={styles.chatContainer}>
            <div className={styles.messagesList}>
              {messages.map((message) => (
                <div 
                  key={message.id} 
                  className={`${styles.message} ${
                    message.type === 'user' ? styles.userMessage : styles.assistantMessage
                  }`}
                >
                  <div className={styles.messageName}>
                    {message.type === 'user' ? 'You' : 'CyberSec Agent'}
                  </div>
                  <div className={styles.messageContent}>
                    {message.content}
                  </div>
                </div>
              ))}
              {loading && !currentAssistantMessage && <div className={styles.loading}>Agent is thinking...</div>}
              <div ref={messagesEndRef} />
            </div>
            <div className={styles.inputContainer}>
              <input
                type="text"
                className={styles.input}
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask the cybersecurity agent..."
                disabled={loading || !connected}
              />
              <button 
                className={styles.sendButton}
                onClick={handleSendMessage}
                disabled={loading || !connected}
              >
                Send
              </button>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
