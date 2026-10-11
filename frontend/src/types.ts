export type Theme =
  | "economy"
  | "security"
  | "human_cost"
  | "diplomacy"
  | "accountability"
  | "innovation";
export const themes: Theme[] = [
  "economy",
  "security",
  "human_cost",
  "diplomacy",
  "accountability",
  "innovation",
];
export const themeNames: Record<Theme, string> = {
  economy: "Economy",
  security: "Security",
  human_cost: "Human cost",
  diplomacy: "Diplomacy",
  accountability: "Accountability",
  innovation: "Innovation",
};
export interface Article {
  id: string;
  country: string;
  outlet: string;
  url: string;
  headline: string;
  text: string;
  language: string;
  published: string;
  coverage: "headline" | "excerpt" | "full_text";
  retrieval: string;
}
export interface Framing {
  translated_headline: string;
  translated_text: string;
  key_claims: { text: string; quote: string }[];
  loaded_words: { word: string; explanation: string; neutral: string }[];
  blamed: string[];
  praised: string[];
  tone: string;
  themes: { theme: Theme; score: number; quote: string; rationale: string }[];
  omitted: string[];
  confidence: number;
}
export interface Outlet {
  article: Article;
  framing: Framing;
  method: string;
}
export interface CountryResult {
  country: string;
  outlets: Outlet[];
  status: string;
  message: string;
}
export interface Reference {
  text: string;
  source_ids: string[];
}
export interface Report {
  id: string;
  query: string;
  language: string;
  mode: string;
  created_at: string;
  countries: CountryResult[];
  synthesis: {
    summary: Reference[];
    simple_summary: Reference[];
    clusters: {
      claim: string;
      status: string;
      source_ids: string[];
      note: string;
    }[];
    missing_voices: {
      perspective: string;
      why_it_matters: string;
      source_ids: string[];
    }[];
    caveat: string;
  };
  notices: string[];
}
export interface Demo {
  id: string;
  query: string;
  title: string;
  date: string;
  tag: string;
  languages: string[];
}
export interface Config {
  countries: Record<string, { name: string; language: string; flag: string }>;
  languages: Record<string, string>;
  demos: Demo[];
  keys: { groq: boolean; news: boolean; audio: boolean };
}
export interface Progress {
  country?: string;
  stage: string;
  message: string;
  report?: Report;
}
