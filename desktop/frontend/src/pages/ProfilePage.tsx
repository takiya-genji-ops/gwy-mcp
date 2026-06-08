import { useState, useEffect } from "react";
import { api } from "../api";

export default function ProfilePage() {
  const [education, setEducation] = useState("本科");
  const [major, setMajor] = useState("");
  const [isFresh, setIsFresh] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.loadProfile().then((p) => {
      if (p) {
        setEducation(String(p.education || "本科"));
        setMajor(String(p.major || ""));
        setIsFresh(Boolean(p.is_fresh_graduate));
      }
    }).catch(() => {});
  }, []);

  const handleSave = async () => {
    try {
      await api.saveProfile({ education, major, is_fresh_graduate: isFresh });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // ignore
    }
  };

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: 20 }}>
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>个人画像</h2>
      <p style={{ fontSize: 13, color: "#666", marginBottom: 20 }}>
        保存你的基本信息后，选岗匹配时会自动使用。信息仅存储在本地。
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div>
          <label style={{ fontSize: 12, color: "#666" }}>学历</label>
          <select value={education} onChange={(e) => setEducation(e.target.value)}
            style={{ width: "100%", padding: 10, borderRadius: 6, border: "1px solid #ddd", marginTop: 4 }}>
            {["专科", "本科", "硕士研究生", "博士研究生"].map((e) => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
        <div>
          <label style={{ fontSize: 12, color: "#666" }}>专业</label>
          <input value={major} onChange={(e) => setMajor(e.target.value)} placeholder="如 计算机科学与技术"
            style={{ width: "100%", padding: 10, borderRadius: 6, border: "1px solid #ddd", marginTop: 4 }} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input type="checkbox" checked={isFresh} onChange={(e) => setIsFresh(e.target.checked)} />
          <label style={{ fontSize: 14 }}>应届毕业生</label>
        </div>
        <button onClick={handleSave}
          style={{ padding: "12px", background: saved ? "#22c55e" : "#e94560", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: 14 }}>
          {saved ? "已保存 ✓" : "保存画像"}
        </button>
      </div>
    </div>
  );
}
