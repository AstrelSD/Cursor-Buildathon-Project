import { CROP_OPTIONS, type CropOption } from "@/constants/crops";

export type VoiceIntakePreview = {
  crop_type?: CropOption;
  declared_acreage?: number;
  requested_amount?: number;
};

/** Match order: longer / more specific patterns first. */
const CROP_SIGNALS: { label: CropOption; patterns: RegExp[] }[] = [
  {
    label: "Vegetables",
    patterns: [
      /vegetables?/i,
      /பச்சை(?:க்)?காய்|காய்கறி|காய்\s*கறி|எலுமிச்சை/i,
      /එළවළු|කොළඅලු/i,
      /\bveg\b/i,
    ],
  },
  {
    label: "Fruits",
    patterns: [
      /fruits?/i,
      /பழம்|பழங்கள்/i,
      /පළතුරු|පලතුරු/i,
    ],
  },
  {
    label: "Coconut",
    patterns: [
      /coconuts?/i,
      /தேங்காய்|தேங்கா/i,
      /පොල්|පොල/i,
      /pol\s*(?:gaha|tree)?/i,
    ],
  },
  {
    label: "Maize",
    patterns: [
      /maize/i,
      /மக்காச்சோளம்|மக்கா/i,
      /මයිස්|ඉරිඟු/i,
      /\bmakka\s*cholam\b/i,
    ],
  },
  {
    label: "Corn",
    patterns: [
      /\bcorn\b/i,
      /சோளம்/i,
      /\bcholam\b/i,
    ],
  },
  {
    label: "Tea",
    patterns: [
      /\btea\b/i,
      /தேயிலை|தேநீர்/i,
      /තේ/i,
      /\bthee\b/i,
      /\bteyilai\b/i,
    ],
  },
  {
    label: "Paddy",
    patterns: [
      /\bpaddy\b/i,
      /\brice\b/i,
      /நெல்|அரிசி|விதைப்பயிர்/i,
      /වී|කුඹුරු|හාල්/i,
      /\bnel\b/i,
      /\barisi\b/i,
    ],
  },
];

function parseAcreage(text: string): number | undefined {
  const lower = text.toLowerCase();
  const patterns = [
    /(\d+(?:\.\d+)?)\s*(?:acres?|acreage|\bac\b)/i,
    /(?:acre|acres|acreage)\s*(?:of\s*)?(\d+(?:\.\d+)?)/i,
    /(\d+(?:\.\d+)?)\s*(?:අක්කර|ஏக்கர்|ஏகரம்)/,
  ];
  for (const pattern of patterns) {
    const match = text.match(pattern) ?? lower.match(pattern);
    if (match?.[1]) {
      const value = Number.parseFloat(match[1]);
      if (Number.isFinite(value) && value > 0) return value;
    }
  }
  return undefined;
}

function parseAmount(text: string, acreage?: number): number | undefined {
  const lower = text.toLowerCase();
  const keywordPatterns = [
    /(?:lkr|rs\.?|rupees?|rupee|loan|amount|need|want|borrow)\s*(?:of\s*)?(\d[\d,]*(?:\.\d+)?)\s*(?:k|thousand)?/i,
    /(\d[\d,]*(?:\.\d+)?)\s*(?:k|thousand)\s*(?:lkr|rs\.?|rupees?)?/i,
    /(\d[\d,]*(?:\.\d+)?)\s*(?:lkr|rs\.?|rupees?)/i,
  ];

  for (const pattern of keywordPatterns) {
    const match = lower.match(pattern);
    if (!match?.[1]) continue;
    const value = parseMoneyToken(match[1], match[0]);
    if (value != null && value >= 5000) return value;
  }

  const candidates: number[] = [];
  const numberRe = /(\d[\d,]*(?:\.\d+)?)\s*(k|thousand)?/gi;
  let m: RegExpExecArray | null;
  while ((m = numberRe.exec(lower)) !== null) {
    const after = lower.slice(m.index + m[0].length, m.index + m[0].length + 12);
    if (/^\s*(?:acre|acres|acreage|\bac\b)/i.test(after)) continue;
    const value = parseMoneyToken(m[1], m[0]);
    if (value != null && value >= 5000) candidates.push(value);
  }

  if (candidates.length === 0) return undefined;
  const best = Math.max(...candidates);
  if (acreage != null && best === acreage) {
    const alt = candidates.filter((n) => n !== acreage);
    return alt.length ? Math.max(...alt) : undefined;
  }
  return best;
}

function parseMoneyToken(raw: string, context: string): number | null {
  const val = Number.parseFloat(raw.replace(/,/g, ""));
  if (!Number.isFinite(val)) return null;
  const ctx = context.toLowerCase();
  if (ctx.includes("k") || ctx.includes("thousand")) return val * 1000;
  return val;
}

export function parseCropFromText(text: string): CropOption | undefined {
  for (const { label, patterns } of CROP_SIGNALS) {
    if (patterns.some((pattern) => pattern.test(text))) {
      return label;
    }
  }
  for (const opt of CROP_OPTIONS) {
    const re = new RegExp(`\\b${opt.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i");
    if (re.test(text)) return opt;
  }
  return undefined;
}

export function normalizeCropType(raw: string): CropOption {
  const trimmed = raw.trim();
  if (!trimmed) return CROP_OPTIONS[0];

  const exact = CROP_OPTIONS.find((opt) => opt.toLowerCase() === trimmed.toLowerCase());
  if (exact) return exact;

  const fromText = parseCropFromText(trimmed);
  if (fromText) return fromText;

  return CROP_OPTIONS[0];
}

/** Lightweight client-side parse while the user is speaking (and for crop normalization). */
export function parseVoiceTranscriptPreview(transcript: string): VoiceIntakePreview {
  const text = transcript.trim();
  if (text.length < 3) return {};

  const declared_acreage = parseAcreage(text);
  const requested_amount = parseAmount(text, declared_acreage);
  const crop_type = parseCropFromText(text);

  return {
    ...(crop_type ? { crop_type } : {}),
    ...(declared_acreage != null ? { declared_acreage } : {}),
    ...(requested_amount != null ? { requested_amount } : {}),
  };
}

/** Merge live transcript parsing with API extraction (transcript wins for crop when API defaulted). */
export function mergeVoiceIntakeFields(
  api: {
    crop_type: string;
    declared_acreage: number;
    requested_amount: number;
  },
  transcript: string,
): Required<Pick<VoiceIntakePreview, "crop_type">> & VoiceIntakePreview {
  const preview = parseVoiceTranscriptPreview(transcript);
  const apiCrop = normalizeCropType(api.crop_type);

  let crop_type: CropOption = preview.crop_type ?? apiCrop;
  if (
    preview.crop_type &&
    apiCrop === CROP_OPTIONS[0] &&
    preview.crop_type !== CROP_OPTIONS[0]
  ) {
    crop_type = preview.crop_type;
  }

  return {
    crop_type,
    declared_acreage: api.declared_acreage ?? preview.declared_acreage,
    requested_amount: api.requested_amount ?? preview.requested_amount,
  };
}

/** Keep the latest non-empty preview values across partial transcript updates. */
export function accumulateVoicePreview(
  current: VoiceIntakePreview,
  next: VoiceIntakePreview,
): VoiceIntakePreview {
  return {
    crop_type: next.crop_type ?? current.crop_type,
    declared_acreage: next.declared_acreage ?? current.declared_acreage,
    requested_amount: next.requested_amount ?? current.requested_amount,
  };
}
