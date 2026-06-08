import { useState } from "react";
import { api } from '../api';
import type { MatchResultItem } from '../api';

export default function MatchPage() {
  const [announcement, setAnnouncement] = useState("");
  const [education, setEducation] = useState("本科");
  const [major, setMajor] = useState("");
  const [isFresh, setIsFresh] = useState(false);
  const [political, setPolitical] = useState("");
  const [household, setHousehold] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<MatchResultItem[] | null>(null);
  const [error, setError] = useState("");

  const handleMatch = async () => {
    if (!announcement.trim() || !major.trim()) return;
    setLoading(true); setError(""); setResults(null);
    try {
      const res = await api.matchPositions({
        education, major, is_fresh_graduate: isFresh,
        political_status: political || undefined,
        household_registration: household || undefined,
        announcement_text: announcement,
      });
      setResults(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>选岗匹配</h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
        <div>
          <label style={{ fontSize: 12, color: "#666" }}>学历</label>
          <select value={education} onChange={(e) => setEducation(e.target.value)}
            style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd", marginTop: 4 }}>
            {["专科", "本科", "硕士研究生", "博士研究生"].map((e) => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
        </div>
        <div>
          <label style={{ fontSize: 12, color: "#666" }}>专业</label>
          <input value={major} onChange={(e) => setMajor(e.target.value)} placeholder="如 计算机科学与技术"
            style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd", marginTop: 4 }} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input type="checkbox" checked={isFresh} onChange={(e) => setIsFresh(e.target.checked)} />
          <label style={{ fontSize: 13 }}>应届毕业生</label>
        </div>
        <div>
          <label style={{ fontSize: 12, color: "#666" }}>政治面貌</label>
          <select value={political} onChange={(e) => setPolitical(e.target.value)}
            style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd", marginTop: 4 }}>
            <option value="">不限</option>
            <option value="中共党员">中共党员</option>
            <option value="共青团员">共青团员</option>
            <option value="群众">群众</option>
          </select>
        </div>
        <div style={{ gridColumn: "1 / -1" }}>
          <label style={{ fontSize: 12, color: "#666" }}>户籍所在地</label>
          <input value={household} onChange={(e) => setHousehold(e.target.value)} placeholder="如 江苏省南京市"
            style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #ddd", marginTop: 4 }} />
        </div>
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 12, color: "#666" }}>公告文本（粘贴PDF/网页提取的文本，或直接粘贴岗位表）</label>
        <textarea value={announcement} onChange={(e) => setAnnouncement(e.target.value)}
          placeholder="粘贴招考公告全文或岗位表..."
          style={{ width: "100%", height: 160, padding: 10, borderRadius: 6, border: "1px solid #ddd", marginTop: 4, resize: "vertical" }} />
      </div>
      <button onClick={handleMatch} disabled={loading}
        style={{ padding: "10px 32px", background: "#e94560", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 600 }}>
        {loading ? "匹配中..." : "开始匹配"}
      </button>
      {error && <p style={{ color: "red", marginTop: 12 }}>{error}</p>}

      {results && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
            匹配结果（{results.filter((r) => r.is_match).length}/{results.length} 可报）
          </h3>
          {results.map((r, i) => (
            <div key={i} style={{
              background: "#fff", borderRadius: 8, padding: 14, marginBottom: 10,
              borderLeft: `4px solid ${r.is_match ? "#22c55e" : "#ef4444"}`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{r.position.unit_name} — {r.position.position_name || "岗位"}</strong>
                <span style={{
                  padding: "2px 10px", borderRadius: 12, fontSize: 12, fontWeight: 600,
                  background: r.is_match ? "#dcfce7" : "#fee2e2",
                  color: r.is_match ? "#166534" : "#991b1b",
                }}>
                  {r.is_match ? "可报" : "不可报"}
                </span>
              </div>
              <div style={{ fontSize: 12, color: "#666", marginTop: 6 }}>
                学历: {r.position.requirements.education} | 专业: {r.position.requirements.majors.join("、") || "不限"} | 招{r.position.recruitment_count}人
              </div>
              {r.blocked_conditions.length > 0 && (
                <div style={{ marginTop: 8, fontSize: 12 }}>
                  {r.blocked_conditions.map((c, j) => (
                    <span key={j} style={{ display: "inline-block", background: "#fee2e2", color: "#991b1b", padding: "1px 8px", borderRadius: 4, marginRight: 6, marginBottom: 4 }}>{c}</span>
                  ))}
                </div>
              )}
              {r.suggestion && <p style={{ fontSize: 12, color: "#666", marginTop: 6 }}>{r.suggestion}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
