export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const SCENARIO_INTENTS = [
  {
    id: "S1",
    label: "S1 — Priya",
    customerId: 1,
    text: "My flight SK-204 was cancelled and I am furious! I want a full refund and a free business class upgrade on my return flight.",
    description: "Cancelled flight • Refund + business class upgrade request",
  },
  {
    id: "S2",
    label: "S2 — Arvind",
    customerId: 2,
    text: "My flight SK-118 is delayed by 4 hours. Can you arrange a hotel for me?",
    description: "4h delay • Hotel request",
  },
  {
    id: "S3",
    label: "S3 — Meher",
    customerId: 3,
    text: "My flight SK-305 is delayed by 6 hours. I want a full night hotel and I want a higher-fare flight without paying the Rs 2,000 extra amount.",
    description: "6h delay • Full-night hotel + Rs2,000 fare waiver request",
  },
];
