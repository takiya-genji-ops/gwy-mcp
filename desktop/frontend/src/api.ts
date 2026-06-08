const BASE = "http://127.0.0.1:8711";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

export interface Position {
  unit_name: string; position_name: string; position_code?: string;
  recruitment_count: number;
  requirements: {
    education: string; majors: string[];
    is_fresh_required: boolean; grassroots_years: number;
    political_status?: string; household_restriction?: string;
  };
  work_location?: string; source_url?: string;
}

export interface MatchResultItem {
  position: Position; is_match: boolean;
  matched_conditions: string[]; blocked_conditions: string[];
  suggestion?: string;
}

export interface GradeDimension {
  name: string; score: number; max_score: number; comment: string;
}

export interface ParagraphFeedback {
  paragraph_index: number; paragraph_text: string;
  feedback: string; suggestion: string;
}

export interface GradingResult {
  total_score: number; max_score: number; grade_level: string;
  dimensions: GradeDimension[]; paragraph_feedback: ParagraphFeedback[];
  overall_comment: string; reference_comparison: string;
  improvement_priority: string[];
}

export const api = {
  health: () => get<{ status: string }>("/api/health"),

  parseAnnouncement: (source: string, sourceType: string) =>
    post<Record<string, unknown>>("/api/parse-announcement", { source, source_type: sourceType }),

  matchPositions: (params: {
    education: string; major: string; is_fresh_graduate: boolean;
    political_status?: string; household_registration?: string;
    announcement_text: string;
  }) => post<MatchResultItem[]>("/api/match-positions", params),

  gradeEssay: (question: string, userAnswer: string, essayType?: string) =>
    post<GradingResult>("/api/grade-essay", {
      question, user_answer: userAnswer, essay_type: essayType,
    }),

  referenceEssays: () => get<{ id: string; topic: string; type: string }[]>("/api/reference-essays"),

  questionTypes: () => get<{ type: string; total_score: number; dimensions: string[] }[]>("/api/question-types"),

  saveProfile: (p: { education: string; major: string; is_fresh_graduate: boolean }) =>
    post("/api/save-profile", p),

  loadProfile: () => get<Record<string, unknown> | null>("/api/load-profile"),
};
