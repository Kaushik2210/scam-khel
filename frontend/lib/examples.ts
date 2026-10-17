// Synthetic example texts for the "Try an example" buttons. All names and numbers are fictional.
import type { Lang } from "./types";

export interface Example {
  id: "scam" | "legit" | "otp";
  text: Record<Lang, string>;
}

export const EXAMPLES: Example[] = [
  {
    id: "scam",
    text: {
      en:
        "This is Inspector Rao from the Cyber Crime Branch (SIMULATION). Your Aadhaar is linked to a money laundering case and a warrant is ready.\n" +
        "You are under digital arrest. Stay on the video call and do not tell anyone, not even your family.\n" +
        "Transfer Rs 90,000 to the RBI safe account simverify@examplebank right now to prove your innocence.",
      hi:
        "मैं साइबर क्राइम ब्रांच से इंस्पेक्टर राव बोल रहा हूँ (SIMULATION)। आपका आधार मनी लॉन्ड्रिंग केस से जुड़ा है और वारंट तैयार है।\n" +
        "आप डिजिटल अरेस्ट में हैं। वीडियो कॉल पर रहिए और किसी को मत बताइए।\n" +
        "तुरंत 90,000 रुपये सुरक्षित खाते में ट्रांसफर करें।",
    },
  },
  {
    id: "legit",
    text: {
      en: "Example Bank: Rs 1,250 debited from your account at a grocery store. If this was not you, call the number on the back of your card. Never share your OTP or PIN with anyone.",
      hi: "उदाहरण बैंक: आपके खाते से किराना दुकान पर 1,250 रुपये कटे हैं। यह आप नहीं थे तो कार्ड के पीछे दिए नंबर पर कॉल करें। अपना OTP या पिन किसी को न बताएँ।",
    },
  },
  {
    id: "otp",
    text: {
      en: "Hello, I am the delivery executive. Your parcel will reach you today between 4 and 6 pm. Please share the delivery OTP with me at the door.",
      hi: "नमस्ते, मैं डिलीवरी बॉय बोल रहा हूँ। आपका पार्सल आज शाम 4 से 6 बजे के बीच पहुँचेगा। दरवाज़े पर डिलीवरी OTP मुझे बता दीजिएगा।",
    },
  },
];
