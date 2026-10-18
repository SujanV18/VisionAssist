export type User = {
  id: string;
  name: string;
  email: string;
  role: "manager" | "salesperson";
  referral_code: string | null;
};
export type Product = {
  id: string;
  model: string;
  title: string;
  specs: {
    resolution: string;
    lens_options: string[];
    ir_range: string;
    protection: string;
    wdr: string;
  };
  evidence: {
    filename: string;
    sha256: string;
    pages: Record<string, number>;
    review_note: string;
  };
  verified: boolean;
  price_paise: number;
  price_kind: string;
};
export type Line = { product_id: string; quantity: number; lens: string };
export type Quote = {
  id: string;
  version: number;
  status: string;
  items: (Line & {
    model: string;
    unit_price_paise: number;
    line_total_paise: number;
  })[];
  total_paise: number;
  notes: string;
  created_at: string;
  price_kind: string;
};
export type Enquiry = {
  id: string;
  name: string;
  contact: string;
  property_type: string;
  location: string;
  requirements: string;
  status: string;
  assignee_id: string | null;
  assignee_name: string | null;
  original_referrer_name: string | null;
  revision: number;
  created_at: string;
  history?: {
    id: string;
    action: string;
    actor: string;
    created_at: string;
    details: Record<string, string | number | boolean | null>;
  }[];
  quotations?: Quote[];
};
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  extraHeaders: Record<string, string> = {},
): Promise<T> {
  const response = await fetch("/api" + path, {
    method,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-VisionAssist": "1",
      ...extraHeaders,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = data.detail;
    throw new Error(
      Array.isArray(detail)
        ? detail.map((d: { msg: string }) => d.msg).join("; ")
        : detail || "Request failed. Please try again.",
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export const money = (paise: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(paise / 100);
export const date = (value: string) =>
  new Date(value).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
export const statusName = (value: string) =>
  ({
    new: "Unassigned",
    assigned: "Assigned",
    drafting: "Draft in progress",
    in_review: "Under review",
  })[value] || value;
