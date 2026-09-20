import { useCallback, useEffect, useState } from "react";
import {
  createConversation,
  getActions,
  getCustomerBookings,
  getCustomers,
  getEscalations,
  sendMessage as apiSendMessage,
} from "@/services/api";
import {
  Action,
  Booking,
  ChatMessage,
  Customer,
  DecisionTraceItem,
  Escalation,
} from "@/types";

export function useChat() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [actions, setActions] = useState<Action[]>([]);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [latestDecisionTrace, setLatestDecisionTrace] = useState<DecisionTraceItem[]>([]);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /** Selects a customer, resets chat state, fetches bookings & creates a new conversation */
  const selectCustomer = useCallback(
    async (customer: Customer) => {
      setSelectedCustomer(customer);
      setBookings([]);
      setConversationId(null);
      setMessages([]);
      setActions([]);
      setEscalations([]);
      setLatestDecisionTrace([]);
      setError(null);
      setIsLoading(true);

      try {
        // 1. Fetch customer bookings
        const customerBookings = await getCustomerBookings(customer.id);
        setBookings(customerBookings);

        // 2. Create one dedicated conversation per selected customer
        const conv = await createConversation(customer.id);
        setConversationId(conv.id);

        // 3. Load initial customer escalations
        const initialEscalations = await getEscalations(customer.id);
        setEscalations(initialEscalations);
      } catch (err: any) {
        setError(err.message || "Failed to initialize session for customer.");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  /** Initial load: fetch all seeded customers and select the first one */
  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getCustomers();
      setCustomers(data);
      if (data && data.length > 0) {
        await selectCustomer(data[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load customers from backend.");
      setIsLoading(false);
    }
  }, [selectCustomer]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  /** Sends a chat message to the resolution agent */
  const sendChatMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;
      if (!conversationId || !selectedCustomer) {
        setError("No active conversation found. Please select a customer.");
        return;
      }

      setIsSending(true);
      setError(null);

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content,
      };

      setMessages((prev) => [...prev, userMsg]);

      try {
        // 1. Send message to backend
        const response = await apiSendMessage(conversationId, content);

        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.reply,
        };

        setMessages((prev) => [...prev, assistantMsg]);

        // 2. Update decision trace
        setLatestDecisionTrace(response.decision_trace || []);

        // 3. Refresh live actions & escalations
        const updatedActions = await getActions(conversationId);
        setActions(updatedActions);

        const updatedEscalations = await getEscalations(selectedCustomer.id);
        setEscalations(updatedEscalations);
      } catch (err: any) {
        setError(err.message || "Failed to process chat message.");
      } finally {
        setIsSending(false);
      }
    },
    [conversationId, selectedCustomer]
  );

  /** Handles quick-start scenario selection by switching customer if needed, then sending prompt */
  const triggerScenario = useCallback(
    async (scenarioText: string, targetCustomerId: number) => {
      let activeConvId = conversationId;
      let activeCust = selectedCustomer;

      if (!activeCust || activeCust.id !== targetCustomerId) {
        const targetCust = customers.find((c) => c.id === targetCustomerId);
        if (targetCust) {
          setIsLoading(true);
          setSelectedCustomer(targetCust);
          setBookings([]);
          setConversationId(null);
          setMessages([]);
          setActions([]);
          setEscalations([]);
          setLatestDecisionTrace([]);
          setError(null);

          try {
            const customerBookings = await getCustomerBookings(targetCust.id);
            setBookings(customerBookings);

            const conv = await createConversation(targetCust.id);
            activeConvId = conv.id;
            activeCust = targetCust;
            setConversationId(conv.id);

            const initialEsc = await getEscalations(targetCust.id);
            setEscalations(initialEsc);
          } catch (err: any) {
            setError(err.message || "Failed to switch customer for scenario.");
            setIsLoading(false);
            return;
          } finally {
            setIsLoading(false);
          }
        }
      }

      if (!activeConvId || !activeCust) return;

      setIsSending(true);
      setError(null);

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: scenarioText,
      };

      setMessages((prev) => [...prev, userMsg]);

      try {
        const response = await apiSendMessage(activeConvId, scenarioText);

        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.reply,
        };

        setMessages((prev) => [...prev, assistantMsg]);
        setLatestDecisionTrace(response.decision_trace || []);

        const updatedActions = await getActions(activeConvId);
        setActions(updatedActions);

        const updatedEscalations = await getEscalations(activeCust.id);
        setEscalations(updatedEscalations);
      } catch (err: any) {
        setError(err.message || "Failed to process scenario intent.");
      } finally {
        setIsSending(false);
      }
    },
    [conversationId, selectedCustomer, customers]
  );

  return {
    customers,
    selectedCustomer,
    bookings,
    conversationId,
    messages,
    actions,
    escalations,
    latestDecisionTrace,
    isLoading,
    isSending,
    error,
    selectCustomer,
    sendChatMessage,
    triggerScenario,
    retryInitialLoad: loadInitialData,
  };
}
