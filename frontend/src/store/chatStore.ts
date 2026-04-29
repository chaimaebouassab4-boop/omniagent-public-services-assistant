import { create } from "zustand";
import type { ChatMessage } from "../types/api";

interface ChatStoreState {
  messages: ChatMessage[];
  isTyping: boolean;
  isConnected: boolean;
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  hydrateMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  markMessageRead: (messageId: string) => void;
  setTyping: (typing: boolean) => void;
  setConnected: (connected: boolean) => void;
}

export const useChatStore = create<ChatStoreState>((set) => ({
  messages: [],
  isTyping: false,
  isConnected: false,
  isLoading: true,
  setLoading: (loading) => set({ isLoading: loading }),
  hydrateMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message]
    })),
  markMessageRead: (messageId) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === messageId ? { ...message, status: "read", pending: false } : message
      )
    })),
  setTyping: (typing) => set({ isTyping: typing }),
  setConnected: (connected) => set({ isConnected: connected })
}));
