import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { RecoilRoot } from "recoil";
import { ChainlitAPI, ChainlitContext } from "@chainlit/react-client";

// Define server URL
const CHAINLIT_SERVER_URL = "http://localhost:8000";

// Initialize the Chainlit API client with the correct parameters
// Constructor requires: httpEndpoint, type, and optional callback handlers
const apiClient = new ChainlitAPI(
  CHAINLIT_SERVER_URL, 
  'webapp', 
  // Optional 401 unauthorized handler
  () => {
    console.log("Unauthorized access, please login");
  },
  // Optional error handler
  (error) => {
    console.error("Chainlit API error:", error.toString());
  }
);

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ChainlitContext.Provider value={apiClient}>
      <RecoilRoot>
        <Component {...pageProps} />
      </RecoilRoot>
    </ChainlitContext.Provider>
  );
}
