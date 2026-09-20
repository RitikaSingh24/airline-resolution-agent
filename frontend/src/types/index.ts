export interface Customer {
  id: number;
  name: str;
  tier: "Silver" | "Gold" | "Platinum" | string;
  email: str;
  phone_masked: str;
  flights_12m: number;
  prior_complaints: number;
  complaint_note?: string | null;
}

export type str = string;

export interface Booking {
  id: number;
  pnr: string;
  segment_label: string;
  flight_no?: string | null;
  route: string;
  flight_date: string;
  sched_dep: string;
  status: string;
  delay_minutes?: number | null;
  new_dep?: string | null;
  cause?: string | null;
}

export interface Conversation {
  id: number;
  customer_id: number;
  created_at: string;
  updated_at: string;
}

export interface DecisionTraceItem {
  rule: string;
  inputs: Record<string, any>;
  outcome: any;
  reason_code?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export interface ChatResponse {
  reply: string;
  actions_taken: Array<Record<string, any>>;
  escalation: boolean;
  conversation_id: number | null;
  decision_trace: DecisionTraceItem[];
}

export interface Action {
  id: number;
  action_type: string;
  details_json: Record<string, any>;
  conversation_id?: number | null;
  customer_id?: number | null;
  booking_id?: number | null;
  created_at?: string;
}

export interface Escalation {
  id: number;
  reason_code: string;
  summary: string;
  status: string;
  conversation_id?: number | null;
  customer_id?: number | null;
  booking_id?: number | null;
  created_at?: string;
  updated_at?: string;
}
