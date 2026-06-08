import { useState, useEffect } from "react";
import { api } from "../api";
import type { GradingResult } from '../api';

export default function EssayPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [essayType, setEssayType] = useState("");
  const [questionTypes, setQuestionTypes] = useState<{ type: string; total_score: number; dimensions: string[] }[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GradingResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.questionTypes().then(setQuestionTypes).catch(() => {});
  }, []);

  const handleGrade = async () => {
    if (!question.trim() || !answer.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await api.gradeEssay(question, answer, essayType || undefined);
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "批改请求失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>申论批改</h2>
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: "#666" }}>题型（可选，不选则自动判断）</label>
        <div style={{ display: "flex", gap: 8, marginTop: 4, flexWrap: "wrap" }}>
          {questionTypes.map((qt) => (
            <button
              key={qt.type}
              onClick={() => setEssayType(essayType === qt.type ? "" : qt.type)}
              style={{
                padding: "4px 12px", borderRadius: 16, border: "1px solid #ddd",
                background: essayType === qt.type ? "#e94560" : "#fff",
                color: essayType === qt.type ? "#fff" : "#333",
                cursor: "pointer", fontSize: 12,
              }}
            >
              {qt.type}（{qt.total_score}分）
            </button>
          ))}
        </div>
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: "#666" }}>申论题目</label>
        <textarea value={question} onChange={(e) => setQuestion(e.target.value)}
          placeholder="粘贴申论题目..."
          style={{ width: "100%", height: 80, padding: 10, borderRadius: 6, border: "1px solid #ddd", marginTop: 4, resize: "vertical" }} />
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: "#666" }}>你的作答</label>
        <textarea value={answer} onChange={(e) => setAnswer(e.target.value)}
          placeholder="粘贴你的作答内容..."
          style={{ width: "100%", height: 200, padding: 10, borderRadius: 6, border: "1px solid #ddd", marginTop: 4, resize: "vertical" }} />
      </div>
      <button onClick={handleGrade} disabled={loading}
        style={{ padding: "10px 32px", background: "#e94560", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 600 }}>
        {loading ? "批改中..." : "提交批改"}
      </button>
      {error && <p style={{ color: "red", marginTop: 12 }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 24 }}>
          <div style={{ background: "#1a1a2e", color: "#fff", borderRadius: 10, padding: 20, textAlign: "center", marginBottom: 20 }}>
            <div style={{ fontSize: 40, fontWeight: 800 }}>{result.total_score}<span style={{ fontSize: 18, fontWeight: 400, opacity: 0.7 }}>/{result.max_score}</span></div>
            <div style={{ fontSize: 14, marginTop: 4, opacity: 0.8 }}>等级：{result.grade_level}</div>
          </div>

          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>各维度评分</h3>
          {result.dimensions.map((d, i) => (
            <div key={i} style={{ background: "#fff", borderRadius: 8, padding: 12, marginBottom: 8, display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ width: 60, textAlign: "center", flexShrink: 0 }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: "#e94560" }}>{d.score}</div>
                <div style={{ fontSize: 10, color: "#999" }}>/ {d.max_score}</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{d.name}</div>
                <div style={{ fontSize: 12, color: "#666", marginTop: 2 }}>{d.comment}</div>
              </div>
            </div>
          ))}

          <h3 style={{ fontSize: 16, fontWeight: 600, margin: "20px 0 12px" }}>逐段批注</h3>
          {result.paragraph_feedback.map((pf, i) => (
            <div key={i} style={{ background: "#fff", borderRadius: 8, padding: 12, marginBottom: 8 }}>
              <div style={{ fontSize: 12, color: "#999", marginBottom: 4 }}>第{pf.paragraph_index + 1}段：{pf.paragraph_text}</div>
              <div style={{ fontSize: 13, color: "#e94560", marginBottom: 4 }}>问题：{pf.feedback}</div>
              <div style={{ fontSize: 13, color: "#166534" }}>建议：{pf.suggestion}</div>
            </div>
          ))}

          <h3 style={{ fontSize: 16, fontWeight: 600, margin: "20px 0 12px" }}>综合评语</h3>
          <div style={{ background: "#fff", borderRadius: 8, padding: 14, fontSize: 14, lineHeight: 1.6 }}>{result.overall_comment}</div>

          {result.reference_comparison && (
            <>
              <h3 style={{ fontSize: 16, fontWeight: 600, margin: "20px 0 12px" }}>范文对比</h3>
              <div style={{ background: "#fff", borderRadius: 8, padding: 14, fontSize: 14, lineHeight: 1.6 }}>{result.reference_comparison}</div>
            </>
          )}

          <h3 style={{ fontSize: 16, fontWeight: 600, margin: "20px 0 12px" }}>优先改进</h3>
          <ul style={{ background: "#fff", borderRadius: 8, padding: "14px 14px 14px 32px", fontSize: 14, lineHeight: 1.8 }}>
            {result.improvement_priority.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
