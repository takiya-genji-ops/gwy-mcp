import { useState } from "react";
import MatchPage from "./pages/MatchPage";
import EssayPage from "./pages/EssayPage";
import ProfilePage from "./pages/ProfilePage";

type Page = "match" | "essay" | "profile";

function App() {
  const [page, setPage] = useState<Page>("match");

  const tabs: { key: Page; label: string }[] = [
    { key: "match", label: "选岗匹配" },
    { key: "essay", label: "申论批改" },
    { key: "profile", label: "个人画像" },
  ];

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", fontFamily: "system-ui, sans-serif" }}>
      <header style={{
        background: "#1a1a2e", color: "#fff", padding: "0 20px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        height: 48, flexShrink: 0,
      }}>
        <span style={{ fontWeight: 700, fontSize: 16 }}>gwy-mcp 公考助手</span>
        <nav style={{ display: "flex", gap: 4 }}>
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setPage(t.key)}
              style={{
                background: page === t.key ? "#e94560" : "transparent",
                color: "#fff", border: "none", padding: "8px 16px",
                borderRadius: 6, cursor: "pointer", fontSize: 13, fontWeight: 500,
              }}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main style={{ flex: 1, overflow: "auto", background: "#f5f5f5" }}>
        {page === "match" && <MatchPage />}
        {page === "essay" && <EssayPage />}
        {page === "profile" && <ProfilePage />}
      </main>
    </div>
  );
}

export default App;
