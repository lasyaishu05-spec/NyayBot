export const LANGUAGES = [
  { code: "en", label: "English", native: "English", flag: "EN" },
  { code: "hi", label: "Hindi", native: "Hindi", flag: "HI" },
  { code: "te", label: "Telugu", native: "Telugu", flag: "TE" },
  { code: "ta", label: "Tamil", native: "Tamil", flag: "TA" },
  { code: "kn", label: "Kannada", native: "Kannada", flag: "KN" },
  { code: "bn", label: "Bengali", native: "Bengali", flag: "BN" },
  { code: "mr", label: "Marathi", native: "Marathi", flag: "MR" },
  { code: "gu", label: "Gujarati", native: "Gujarati", flag: "GU" },
  { code: "ml", label: "Malayalam", native: "Malayalam", flag: "ML" },
  { code: "pa", label: "Punjabi", native: "Punjabi", flag: "PA" },
  { code: "ur", label: "Urdu", native: "Urdu", flag: "UR" },
  { code: "or", label: "Odia", native: "Odia", flag: "OR" },
];

export const PROCESSING_STEPS = [
  "Reading your legal document...",
  "Extracting text from all pages...",
  "Identifying key clauses and obligations...",
  "Simplifying complex legal language...",
  "Translating into selected language...",
  "Generating action checklist...",
];

export const MOCK_SUMMARY =
  "This is a Rental Agreement between Rajesh Kumar (Landlord) and Priya Sharma (Tenant) for a 2BHK apartment located at Flat No. 304, Green Valley Apartments, Koramangala, Bengaluru - 560034. The agreement is valid for 11 months starting from 1st April 2024, with a monthly rent of Rs. 22,000 and a security deposit of Rs. 66,000.";

export const MOCK_KEY_POINTS = [
  "Monthly rent of Rs. 22,000 must be paid by the 5th of every month.",
  "Security deposit of Rs. 66,000 is refundable within 30 days of vacating.",
  "2-month advance notice required before leaving the property.",
  "No subletting or alterations to the property without written consent.",
  "Tenant is responsible for minor repairs up to Rs. 500.",
  "Maintenance charges of Rs. 1,200/month are additional.",
];

export const MOCK_CLAUSES = [
  { text: "Agreement auto-renews unless terminated 60 days in advance.", type: "warning" },
  { text: "Landlord can inspect property with 24-hour prior notice.", type: "info" },
  { text: "Late payment penalty: 2% per week on overdue rent.", type: "danger" },
  { text: "Pets are strictly NOT allowed on the premises.", type: "danger" },
];

export const MOCK_ACTIONS = [
  { step: 1, text: "Sign and date the agreement on every page", done: false, deadline: null },
  {
    step: 2,
    text: "Pay security deposit via bank transfer (get receipt)",
    done: false,
    deadline: "Before 31 Mar 2024",
    isDeadline: true,
  },
  {
    step: 3,
    text: "Register the agreement at local Sub-Registrar Office",
    done: false,
    deadline: "Within 4 months",
    isDeadline: true,
  },
  { step: 4, text: "Keep a photocopy of the signed agreement", done: false, deadline: null },
  {
    step: 5,
    text: "Note auto-renewal clause - set a reminder for Feb 2025",
    done: false,
    deadline: "Set reminder: 1 Feb 2025",
    isDeadline: true,
  },
  { step: 6, text: "Confirm maintenance charge details in writing", done: false, deadline: null },
];

export const MOCK_CHAT = [
  { role: "ai", text: "Hi! I've analyzed your document. What would you like to know?" },
  { role: "user", text: "What happens if I pay rent late?" },
  {
    role: "ai",
    text: "According to Clause 7.2 of your agreement, a late payment penalty of 2% per week is charged on the overdue rent amount. For example, on Rs. 22,000 rent, that's Rs. 440 per week of delay.",
  },
];

export const CLAUSE_COLORS = {
  warning: { bg: "#FFFBEB", border: "#FDE68A", icon: "!", text: "#92400E" },
  info: { bg: "#EFF6FF", border: "#BFDBFE", icon: "i", text: "#1E40AF" },
  danger: { bg: "#FEF2F2", border: "#FECACA", icon: "!!", text: "#991B1B" },
};
