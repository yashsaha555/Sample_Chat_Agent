"use client";
import { useEffect, useRef, useState } from "react";
import { Paperclip, Send, Sparkles } from "lucide-react";
import Markdown from "../components/Markdown";
import { generateDataset, generateSampleLogs } from "./api-helpers";

type Message = { role: "user" | "assistant"; content: string };

export default function Page() {
  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scroller.current?.scrollTo({
      top: scroller.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages]);

  const handleFiles = (fList: FileList | null) => {
    if (!fList) return;
    const arr = Array.from(fList);
    setFiles((prev: File[]) => [...prev, ...arr]);
  };

  const uploadAndExtract = async (f: File[]) => {
    if (!f.length) return [] as string[];
    const fd = new FormData();
    f.forEach((x) => fd.append("files", x));
    const r = await fetch(`${API}/api/upload`, {
      method: "POST",
      body: fd
    });
    if (!r.ok) throw new Error("Upload failed");
    const js = await r.json();
    const ctx: string[] = (js.items || []).map(
      (it: any) => `# ${it.filename}\n${it.content}`
    );
    return ctx;
  };

  const send = async () => {
    const text = input.trim();
    if (!text && !files.length) return;
    setPending(true);
    setInput("");
    setMessages((m: Message[]) => [
      ...m,
      { role: "user", content: text || "[uploaded files]" }
    ]);
    try {
      const context = await uploadAndExtract(files);
      setFiles([]);
      const r = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, context })
      });
      if (!r.ok) throw new Error("Chat failed");
      const js = await r.json();
      setMessages((m: Message[]) => [
        ...m,
        { role: "assistant", content: js.reply }
      ]);
    } catch (e: any) {
      setMessages((m: Message[]) => [
        ...m,
        { role: "assistant", content: `Error: ${e.message}` }
      ]);
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="min-h-screen gradient">
      <div className="max-w-5xl mx-auto p-6">
        <header className="flex items-center gap-3 mb-6">
          <div className="h-10 w-10 rounded-xl2 bg-accent/20 flex items-center justify-center shadow-glow">
            <Sparkles className="text-accent" size={20} />
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-semibold tracking-tight">
              Premium Chatbot
            </h1>
            <p className="text-subt text-sm">
              Ultra-premium AI assistant with file + OCR + math
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="text-xs px-3 py-2 rounded-xl2 bg-card border border-white/10 hover:border-white/20"
              onClick={async () => {
                try {
                  await generateDataset();
                  setMessages((m) => [
                    ...m,
                    {
                      role: "assistant",
                      content:
                        "Synthetic dataset generated and ingested into vector DB."
                    }
                  ]);
                } catch (e: any) {
                  setMessages((m) => [
                    ...m,
                    { role: "assistant", content: `Error: ${e.message}` }
                  ]);
                }
              }}
            >
              Build Dataset
            </button>
            <button
              className="text-xs px-3 py-2 rounded-xl2 bg-card border border-white/10 hover:border-white/20"
              onClick={async () => {
                try {
                  const js = await generateSampleLogs(5);
                  const ctx: string[] = (js.items || []).map(
                    (it: any) => `# ${it.filename}\n${it.content}`
                  );
                  setFiles([]);
                  const r = await fetch(`${API}/api/chat`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      message:
                        "Analyze these sample IoT logs for anomalies and diagnostics.",
                      context: ctx
                    })
                  });
                  if (!r.ok) throw new Error("Chat failed");
                  const js2 = await r.json();
                  setMessages((m) => [
                    ...m,
                    { role: "assistant", content: js2.reply }
                  ]);
                } catch (e: any) {
                  setMessages((m) => [
                    ...m,
                    { role: "assistant", content: `Error: ${e.message}` }
                  ]);
                }
              }}
            >
              Try Sample Logs
            </button>
          </div>
        </header>

        <main className="glass rounded-2xl p-4 md:p-6 min-h-[70vh] flex flex-col">
          <div
            ref={scroller}
            className="flex-1 overflow-auto pr-2 scrollbar space-y-4"
          >
            {messages.length === 0 && (
              <div className="text-center text-subt mt-12">
                Enter / Upload your IoT Device Logs
              </div>
            )}
            {messages.map((m: Message, i: number) => (
              <div
                key={i}
                className={`flex ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 whitespace-pre-wrap leading-relaxed shadow/10 ${
                    m.role === "user"
                      ? "bg-accent text-white"
                      : "bg-card text-text"
                  }`}
                >
                  {m.role === "assistant" ? (
                    <Markdown content={m.content} />
                  ) : (
                    m.content
                  )}
                </div>
              </div>
            ))}
            {pending && (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-card text-subt animate-pulse">
                  Thinking…
                </div>
              </div>
            )}
          </div>

          <div
            className="mt-4 border border-white/10 rounded-2xl p-3 bg-[#0B1222]"
            onDragOver={(e) => {
              e.preventDefault();
            }}
            onDrop={(e) => {
              e.preventDefault();
              handleFiles(e.dataTransfer.files);
            }}
          >
            {files.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {files.map((f, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2 py-1 rounded-full bg-card text-subt border border-white/10"
                  >
                    {f.name}
                  </span>
                ))}
              </div>
            )}

            <div className="flex items-center gap-2">
              <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-2 rounded-xl2 bg-card border border-white/10 hover:border-white/20">
                <Paperclip size={16} className="text-subt" />
                <span className="text-sm text-subt">Attach</span>
                <input
                  type="file"
                  className="hidden"
                  multiple
                  onChange={(e) => handleFiles(e.target.files)}
                />
              </label>

              <input
                className="flex-1 bg-transparent outline-none px-3 py-2 text-sm placeholder:text-subt/60"
                placeholder="Type your message…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") send();
                }}
              />

              <button
                onClick={send}
                disabled={pending}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl2 bg-accent hover:bg-accent/90 text-white disabled:opacity-50"
              >
                <Send size={16} />
                Send
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
