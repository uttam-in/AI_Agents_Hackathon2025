import Head from "next/head";
import { Geist, Geist_Mono } from "next/font/google";
import styles from "@/styles/Home.module.css";
import { ChainlitContext } from "@chainlit/react-client";
import { useContext, useState, useEffect } from "react";

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

  // Function to send message to backend
  const handleSendMessage = async () => {
    if (!messageInput.trim() || loading) return;
    
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
      // Here you would normally call the API to get a response
      // For now, let's simulate a response after a delay
      setTimeout(() => {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `I received your message: "${userMessage.content}". This is a simulated response until the backend connection is properly set up.`
        };
        setMessages(prevMessages => [...prevMessages, assistantMessage]);
        setLoading(false);
      }, 1000);
      
      // When you have the API set up, you would do something like:
      // const response = await client.post('/chat', { message: messageInput });
      // Add the response to messages
    } catch (error) {
      console.error('Error sending message:', error);
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>AI Agents Hackathon 2025</title>
        <meta name="description" content="Cybersecurity AI Agent Interface" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div
        className={`${styles.page} ${geistSans.variable} ${geistMono.variable}`}
      >
        <main className={styles.main}>
          <h1 className={styles.title}>Cybersecurity AI Agent</h1>
          
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
                    {message.type === 'user' ? 'You' : 'Assistant'}
                  </div>
                  <div className={styles.messageContent}>
                    {message.content}
                  </div>
                </div>
              ))}
              {loading && <div className={styles.loading}>Thinking...</div>}
            </div>
            <div className={styles.inputContainer}>
              <input
                type="text"
                className={styles.input}
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Type your message..."
                disabled={loading}
              />
              <button 
                className={styles.sendButton}
                onClick={handleSendMessage}
                disabled={loading}
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
