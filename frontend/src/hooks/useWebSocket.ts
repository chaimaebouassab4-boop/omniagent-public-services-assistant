import { useEffect } from "react";
import { io, type Socket } from "socket.io-client";
import { getChatSocketUrl } from "../services/chat";
import { useChatStore } from "../store/chatStore";
import type { ChatMessage } from "../types/api";

interface UseWebSocketOptions {
  caseId: string;
}

/** Socket-ready hook that manages connection and typing simulation. */
export function useWebSocket({ caseId }: UseWebSocketOptions): void {
  const addMessage = useChatStore((state) => state.addMessage);
  const setTyping = useChatStore((state) => state.setTyping);
  const setConnected = useChatStore((state) => state.setConnected);
  const markMessageRead = useChatStore((state) => state.markMessageRead);

  useEffect(() => {
    const socketUrl = getChatSocketUrl(caseId);

    // Placeholder wiring using socket.io for later backend handshake.
    let socket: Socket | null = null;
    try {
      socket = io(socketUrl, {
        transports: ["websocket"],
        autoConnect: true,
        reconnectionAttempts: 2,
        timeout: 4000
      });

      socket.on("connect", () => setConnected(true));
      socket.on("disconnect", () => setConnected(false));
      socket.on("typing", (typing: boolean) => setTyping(typing));
      socket.on("message", (message: ChatMessage) => addMessage(message));
      socket.on("read", (messageId: string) => markMessageRead(messageId));
    } catch {
      setConnected(false);
    }

    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, [addMessage, caseId, markMessageRead, setConnected, setTyping]);
}
