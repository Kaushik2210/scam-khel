import type { Lang } from "./types";

type L = Record<Lang, string>;

export const TACTICS: Record<string, L> = {
  authority_impersonation: { en: "Pretends to be an official", hi: "अधिकारी होने का दिखावा" },
  fear_arrest_threat: { en: "Threatens arrest or a case", hi: "गिरफ्तारी या केस की धमकी" },
  isolation_secrecy: { en: "Says “tell no one”", hi: "“किसी को मत बताओ” कहता है" },
  stay_on_camera_digital_arrest: { en: "“Digital arrest”: stay on camera", hi: "“डिजिटल अरेस्ट”: कैमरे पर रहो" },
  urgency_deadline: { en: "Artificial deadline", hi: "बनावटी समय-सीमा" },
  fake_case_or_badge_id: { en: "Quotes a case or badge number", hi: "केस या बैज नंबर बताता है" },
  document_demand: { en: "Asks for Aadhaar / PAN / bank details", hi: "आधार / पैन / बैंक जानकारी माँगता है" },
  safe_account_transfer: { en: "Asks to move money to a “safe account”", hi: "“सुरक्षित खाते” में पैसे माँगता है" },
  verification_fee_or_deposit: { en: "Demands a fee, fine or deposit", hi: "फीस, जुर्माना या जमा माँगता है" },
  remote_access_app_request: { en: "Asks to install a remote-access app", hi: "रिमोट-एक्सेस ऐप इंस्टॉल करवाता है" },
  otp_request: { en: "Asks for an OTP or PIN", hi: "OTP या पिन माँगता है" },
  link_or_apk_push: { en: "Pushes a link or APK", hi: "लिंक या APK भेजता है" },
  family_member_implicated: { en: "Says a family member is involved", hi: "परिवार के सदस्य को फँसा बताता है" },
};

export const STAGES: Record<string, L> = {
  contact: { en: "Contact", hi: "संपर्क" },
  accusation: { en: "Accusation", hi: "आरोप" },
  isolation: { en: "Isolation", hi: "अकेला करना" },
  verification: { en: "“Verification”", hi: "“सत्यापन”" },
  payment: { en: "Payment demand", hi: "पैसों की माँग" },
};

export const EVIDENCE_TYPES: Record<string, L> = {
  phone: { en: "Phone", hi: "फोन" },
  upi: { en: "UPI ID", hi: "UPI आईडी" },
  account: { en: "Account", hi: "खाता" },
  ifsc: { en: "IFSC", hi: "IFSC" },
  url: { en: "Link", hi: "लिंक" },
  apk: { en: "APK file", hi: "APK फ़ाइल" },
  agency: { en: "Claimed agency", hi: "बताई गई एजेंसी" },
  officer_name: { en: "Officer name", hi: "अधिकारी का नाम" },
  badge_id: { en: "Badge ID", hi: "बैज आईडी" },
  case_id: { en: "Case ID", hi: "केस आईडी" },
  amount: { en: "Amount", hi: "राशि" },
  deadline: { en: "Deadline", hi: "समय-सीमा" },
};

export const lab = (m: Record<string, L>, k: string, lang: Lang) => m[k]?.[lang] ?? k;

export function fmtDuration(s: number): string {
  const m = Math.floor(s / 60);
  return m ? `${m}m ${s % 60}s` : `${s}s`;
}
