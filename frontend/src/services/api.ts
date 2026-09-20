import { API_BASE_URL } from "@/lib/constants";
import {
  Action,
  Booking,
  ChatResponse,
  Conversation,
  Customer,
  Escalation,
} from "@/types";

const DEFAULT_TIMEOUT_MS = 30000;

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
    return response;
  } catch (error: any) {
    if (error.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs / 1000}s`);
    }
    throw new Error(error.message || "Failed to connect to backend service.");
  } finally {
    clearTimeout(id);
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.message) {
        errorMsg = errorData.message;
      } else if (errorData.detail) {
        errorMsg =
          typeof errorData.detail === "string"
            ? errorData.detail
            : JSON.stringify(errorData.detail);
      } else if (errorData.error) {
        errorMsg = errorData.error;
      }
    } catch (_) {
      // Ignore JSON parse failures
    }
    throw new Error(errorMsg);
  }
  return response.json();
}

/** Fetches all seeded customer records from GET /api/v1/customers */
export async function getCustomers(): Promise<Customer[]> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/api/v1/customers`);
  return handleResponse<Customer[]>(res);
}

/** Fetches bookings for a specific customer from GET /api/v1/customers/{id}/bookings */
export async function getCustomerBookings(customerId: number): Promise<Booking[]> {
  const res = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/customers/${customerId}/bookings`
  );
  return handleResponse<Booking[]>(res);
}

/** Creates a new conversation for a customer from POST /api/v1/conversations */
export async function createConversation(customerId: number): Promise<Conversation> {
  const res = await fetchWithTimeout(`${API_BASE_URL}/api/v1/conversations`, {
    method: "POST",
    body: JSON.stringify({ customer_id: customerId }),
  });
  return handleResponse<Conversation>(res);
}

/** Sends a chat message to POST /api/v1/conversations/{conversation_id}/messages */
export async function sendMessage(
  conversationId: number,
  content: string
): Promise<ChatResponse> {
  let res = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({ content }),
    }
  );
  if (!res.ok && res.status === 404) {
    // Alternate route endpoint support
    res = await fetchWithTimeout(
      `${API_BASE_URL}/api/v1/chat/${conversationId}/messages`,
      {
        method: "POST",
        body: JSON.stringify({ content }),
      }
    );
  }
  return handleResponse<ChatResponse>(res);
}

/** Fetches audited resolution actions from GET /api/v1/conversations/{id}/actions */
export async function getActions(conversationId?: number): Promise<Action[]> {
  if (!conversationId) return [];
  let res = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/conversations/${conversationId}/actions`
  );
  if (!res.ok && res.status === 404) {
    res = await fetchWithTimeout(
      `${API_BASE_URL}/api/v1/actions?conversation_id=${conversationId}`
    );
  }
  return handleResponse<Action[]>(res);
}

/** Fetches support escalation records from GET /api/v1/escalations */
export async function getEscalations(customerId?: number): Promise<Escalation[]> {
  const url = customerId
    ? `${API_BASE_URL}/api/v1/escalations?customer_id=${customerId}`
    : `${API_BASE_URL}/api/v1/escalations`;
  const res = await fetchWithTimeout(url);
  const data = await handleResponse<Escalation[]>(res);
  if (customerId) {
    return data.filter((e) => !e.customer_id || e.customer_id === customerId);
  }
  return data;
}
