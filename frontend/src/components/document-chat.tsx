"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@astryxdesign/core/Button";
import { ChatLayout, ChatComposer, ChatMessage, ChatMessageBubble, ChatMessageList } from "@astryxdesign/core/Chat";
import { api, ApiError, duration, reportPaint, timestamp, type Config, type Conversation, type Message, type Reference, type Run, type Topic, type TurnResult } from "@/lib/api";
import { MessageContent } from "./message-content";
import { SourcePreview } from "./source-preview";
import { isSendKey, operationSettled, type Pending } from "@/lib/chat-state";

const pendingKey = "floor-guide.pending";
function readPending(id?: string): Pending | null {
  try {
    const stored = JSON.parse(localStorage.getItem(pendingKey) ?? "{}") as Record<string, Pending>;
    const value = id ? stored[id] : Object.values(stored)[0];
    return value && typeof value.conversationId === "string" && typeof value.path === "string" && value.path.startsWith(`/conversations/${value.conversationId}/`) && typeof value.body?.operation_id === "string" ? value : null;
  } catch { return null; }
}
function rememberPending(id: string, value: Pending | null) {
  try {
    const stored = JSON.parse(localStorage.getItem(pendingKey) ?? "{}") as Record<string, Pending>;
    if (value) stored[id] = value; else delete stored[id];
    localStorage.setItem(pendingKey, JSON.stringify(stored));
  } catch { /* The in-memory key still protects retries without browser storage. */ }
}

export function DocumentChat() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [config, setConfig] = useState<Config | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const activeRef = useRef<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const submittingRef = useRef(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const [source, setSource] = useState<Reference | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [moreConversations, setMoreConversations] = useState(false);
  const waiting = run?.status === "awaiting_clarification";

  const refreshConversations = useCallback(async () => {
    const { data } = await api<{ items: Conversation[] }>("/conversations?limit=50&offset=0");
    setConversations(data.items); setMoreConversations(data.items.length === 50);
  }, []);
  const loadConversation = useCallback(async (id: string, preserve = false) => {
    activeRef.current = id;
    setActiveId(id); setError(null); setSidebarOpen(false);
    if (!preserve) { setMessages([]); setRun(null); setLoading(true); setDraft(""); }
    try { localStorage.setItem("floor-guide.conversation", id); } catch { /* Optional convenience. */ }
    const stored = readPending(id);
    setPending(stored?.conversationId === id ? stored : null);
    try {
      const all: Message[] = [];
      let current: Run | null = null;
      for (let offset = 0; ; offset += 200) {
        const { data } = await api<{ items: Message[]; run: Run | null }>(`/conversations/${id}/messages?limit=200&offset=${offset}`);
        if (activeRef.current !== id) return;
        all.push(...data.items); current = data.run;
        if (data.items.length < 200) break;
      }
      setMessages(all); setRun(current);
      if (stored && operationSettled(stored, current)) { rememberPending(id, null); setPending(null); }
    } catch (cause) {
      if (activeRef.current === id) setError(cause instanceof Error ? cause.message : "Could not load this conversation.");
    } finally { if (activeRef.current === id) setLoading(false); }
  }, []);
  useEffect(() => {
    let alive = true;
    async function initialize() {
      try {
        const [settings, catalog, history] = await Promise.all([api<Config>("/config"), api<{ items: Topic[] }>("/topics"), api<{ items: Conversation[] }>("/conversations?limit=50&offset=0")]);
        if (!alive) return;
        setConfig(settings.data); setTopics(catalog.data.items); setConversations(history.data.items); setMoreConversations(history.data.items.length === 50);
        let saved: string | null = null;
        try { saved = localStorage.getItem("floor-guide.conversation"); } catch { /* Storage is optional. */ }
        const stored = readPending();
        const selected = stored?.conversationId ?? saved;
        if (selected) await loadConversation(selected); else setLoading(false);
      } catch (cause) { if (alive) { setError(cause instanceof Error ? cause.message : "Could not connect to the API."); setLoading(false); } }
    }
    void initialize();
    return () => { alive = false; };
  }, [loadConversation]);
  // Recover a request that outlived a tab refresh without invoking the model again.
  useEffect(() => {
    if (!activeId || run?.status !== "running" || busy) return;
    let cancelled = false;
    const timer = setInterval(() => {
      void api<Run | null>(`/conversations/${activeId}/run`).then(({ data }) => {
        if (!cancelled && activeRef.current === activeId && data?.status !== "running") void loadConversation(activeId, true);
      }).catch(() => { if (!cancelled) setError("Could not refresh this run. Reopen the conversation to try again."); });
    }, 2000);
    return () => { cancelled = true; clearInterval(timer); };
  }, [activeId, run?.status, busy, loadConversation]);

  async function createConversation() {
    const { data } = await api<Conversation>("/conversations", { method: "POST", body: "{}" });
    activeRef.current = data.id; setActiveId(data.id); setMessages([]); setRun(null); setPending(null); setDraft(""); setError(null); setLoading(false); setSidebarOpen(false);
    try { localStorage.setItem("floor-guide.conversation", data.id); } catch { /* Optional convenience. */ }
    await refreshConversations();
    return data.id;
  }
  async function execute(operation: Pending) {
    if (busyRef.current) return;
    busyRef.current = true; setBusy(true); setError(null); setPending(operation); rememberPending(operation.conversationId, operation);
    const started = performance.now();
    try {
      const { data, requestId } = await api<TurnResult>(operation.path, { method: "POST", body: JSON.stringify(operation.body) });
      const failed = data.run.status === "failed";
      if (activeRef.current === operation.conversationId) {
        await loadConversation(operation.conversationId, true);
        setRun(data.run); setPending(failed ? operation : null);
        if (failed) setError(data.run.error ?? "The answer could not be completed. Retry this operation.");
      }
      rememberPending(operation.conversationId, failed ? operation : null);
      reportPaint(requestId, started, data.run.status);
      await refreshConversations();
    } catch (cause) {
      if (cause instanceof ApiError) reportPaint(cause.requestId, started, "failed");
      if (activeRef.current === operation.conversationId) {
        if (cause instanceof ApiError && [400, 404, 422].includes(cause.status)) {
          rememberPending(operation.conversationId, null); setPending(null);
          if (typeof operation.body.content === "string") setDraft(operation.body.content);
        }
        if (cause instanceof ApiError && cause.status === 409) await loadConversation(operation.conversationId, true);
        setError(cause instanceof Error ? cause.message : "Could not send. Retry with the same operation key.");
      }
    } finally { busyRef.current = false; setBusy(false); }
  }
  async function submit(content: string) {
    const text = content.trim();
    if (!text || busyRef.current || submittingRef.current || loading || run?.status === "running" || pending) return;
    if (text.length > 12_000) { setError("Keep your message under 12,000 characters."); return; }
    submittingRef.current = true;
    try {
      const id = activeId ?? await createConversation();
      const operation: Pending = waiting && run ? { conversationId: id, path: `/conversations/${id}/resume`, body: { turn_id: run.id, interrupt_id: run.interrupt_id, version: run.version, content: text, operation_id: crypto.randomUUID() } } : { conversationId: id, path: `/conversations/${id}/messages`, previousRunId: run?.id ?? null, body: { content: text, operation_id: crypto.randomUUID() } };
      setDraft(""); await execute(operation);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not create a conversation."); }
    finally { submittingRef.current = false; }
  }
  async function cancel() {
    if (!activeId || !run || busyRef.current) return;
    await execute({ conversationId: activeId, path: `/conversations/${activeId}/runs/${run.id}/cancel`, body: { operation_id: crypto.randomUUID() } });
  }
  async function loadMoreConversations() {
    try {
      const { data } = await api<{ items: Conversation[] }>(`/conversations?limit=50&offset=${conversations.length}`);
      setConversations(previous => [...previous, ...data.items.filter(item => !previous.some(old => old.id === item.id))]); setMoreConversations(data.items.length === 50);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load more conversations."); }
  }
  const currentTitle = conversations.find(item => item.id === activeId)?.title;
  const composerDisabled = busy || loading || run?.status === "running" || !!pending || config?.configured === false;
  return <main className="workspace">
    <aside className={`sidebar ${sidebarOpen ? "is-open" : ""}`} aria-label="Conversations and library">
      <header className="brand"><strong className="brand-mark" aria-hidden="true">F/</strong><section><strong>Floor Guide</strong><p>YOUR DOCUMENT WORKSPACE</p></section><Button className="mobile-only" variant="ghost" label="Close navigation" onClick={() => setSidebarOpen(false)} /></header>
      <Button label="＋ New conversation" variant="primary" isDisabled={busy || loading} onClick={() => { void createConversation().catch(cause => setError(cause.message)); }} />
      <section className="history-section"><p className="section-label">CONVERSATIONS</p><nav className="conversation-list" aria-label="Saved conversations">
        {conversations.length === 0 && <p className="muted">Your conversations will be saved here.</p>}
        {conversations.map(conversation => <button key={conversation.id} type="button" className={`conversation-row ${conversation.id === activeId ? "is-active" : ""}`} aria-current={conversation.id === activeId ? "page" : undefined} onClick={() => { void loadConversation(conversation.id); }}><strong>{conversation.title || "New conversation"}</strong><small>{timestamp(conversation.updated_at)}</small></button>)}
        {moreConversations && <Button label="Load older conversations" variant="ghost" size="sm" onClick={() => { void loadMoreConversations(); }} />}
      </nav></section>
      <details className="library" open><summary>Document library <small>{config?.documents_count ?? "—"} sources</small></summary>{topics.map(topic => <section key={topic.id} className="topic"><strong title={topic.description}>{topic.name}</strong>{topic.documents.map(document => <p key={document.id} title={document.title}><i className={document.available ? "available-dot" : "unavailable-dot"} aria-hidden="true" />{document.title}<small>{document.available ? document.revision ? `Rev ${document.revision}` : "Available" : "Unavailable"}</small></p>)}</section>)}</details>
      <footer className="sidebar-footer"><Link href="/observability">Run inspector ↗</Link><p>Local prototype · No authentication</p></footer>
    </aside>
    <section className="chat-column" aria-label="Document chat">
      <header className="chat-header"><section><Button className="mobile-only" variant="ghost" label="Open navigation" onClick={() => setSidebarOpen(true)} /><p className="section-label">FLOOR SUPERVISOR ASSISTANT</p><h1>{currentTitle || "A little clarity for your shift."}</h1></section><p className="model-status">{config ? `${config.model} · effort ${config.reasoning_effort}` : "Connecting…"}</p></header>
      <p className="demo-notice">EXAMPLE ONLY — NOT RELEASED FOR OPERATION. Verify against your approved plant procedures.</p>
      {config?.configured === false && <section className="inline-warning" role="status"><strong>Model connection needs configuration.</strong><p>Add the OpenAI API key to the root .env and restart the backend. Saved conversations and sources remain available.</p></section>}
      <ChatLayout key={activeId ?? "new"} className="chat-layout" composer={<section className="composer-region">
        {waiting && <section className="clarification" role="status"><strong>A detail is needed before continuing</strong><p>{run.clarification_question}</p><small>Reply below to continue this same question.</small><Button label="Cancel this question" variant="ghost" size="sm" isDisabled={busy} onClick={() => { void cancel(); }} /></section>}
        {(error || (pending && !busy)) && <section className="inline-error" role="alert"><p>{error || "A previous send may still be processing. Retry to retrieve its result without duplicating the question."}</p>{pending ? <Button label="Retry same operation" size="sm" isDisabled={busy || run?.status === "running"} onClick={() => { void execute(pending); }} /> : <Button label="Refresh conversation" size="sm" onClick={() => { if (activeId) void loadConversation(activeId); else window.location.reload(); }} />}</section>}
        <ChatComposer value={draft} onChange={setDraft} onSubmit={value => { void submit(value); }} isDisabled={composerDisabled}
          input={<textarea aria-label={waiting ? "Clarification reply" : "Ask about your plant documents"} rows={3} value={draft} maxLength={12_000} disabled={composerDisabled} placeholder={waiting ? "Add the missing details…" : "Ask about a procedure, asset, or quality check…"} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (isSendKey({ key: event.key, shiftKey: event.shiftKey, isComposing: event.nativeEvent.isComposing, keyCode: event.nativeEvent.keyCode })) { event.preventDefault(); void submit(draft); } }} />}
          sendButton={<Button label={waiting ? "Send reply ↑" : "Send question ↑"} variant="primary" isDisabled={composerDisabled || !draft.trim()} onClick={() => { void submit(draft); }} />}
          footerActions={<small className="composer-hint">Enter to send · Shift + Enter for a new line</small>} />
        <p className="composer-disclaimer">Answers use available documents. Open the numbered sources to check the evidence.</p>
      </section>}>
        {loading ? <section className="empty-state" role="status"><p className="section-label">LOADING YOUR WORKSPACE</p><h2>Retrieving saved conversations…</h2></section> : messages.length === 0 ? <section className="empty-state"><p className="empty-symbol" aria-hidden="true">✳</p><p className="section-label">KNOW WHERE TO LOOK. KNOW WHAT TO ASK.</p><h2>Your documents.<br />A clearer next step.</h2><p>Ask a question in your own words. Get a document-grounded answer and the exact evidence behind it.</p><section className="starter-grid" aria-label="Question suggestions">{["What checks should I make before starting maintenance?", "How should I handle a nonconforming product?", "Which documents cover safe-work procedures?"].map(question => <button key={question} className="starter" onClick={() => setDraft(question)} type="button">{question}<b aria-hidden="true">↗</b></button>)}</section><p className="muted">Demonstration documents. Your approved procedures always take priority.</p></section> : <ChatMessageList align="top">{messages.map(message => <ChatMessage key={message.id} sender={message.role} metadata={<section className="message-meta"><small>{message.kind === "clarification" ? "Clarification requested" : message.kind === "reply" ? "Clarification reply" : message.role === "assistant" ? "Document-grounded answer" : "You"} · {timestamp(message.created_at)}</small>{message.run_id && <Link href={`/observability?run=${encodeURIComponent(message.run_id)}`}>Inspect run ↗</Link>}</section>}><ChatMessageBubble variant={message.role === "user" ? "filled" : "ghost"} name={message.role === "user" ? "You" : "Floor Guide"}><MessageContent message={message} onSource={setSource} /></ChatMessageBubble></ChatMessage>)}</ChatMessageList>}
        {busy && pending?.conversationId === activeId && typeof pending.body.content === "string" && <ChatMessage sender="user"><ChatMessageBubble name="You">{pending.body.content}</ChatMessageBubble></ChatMessage>}
        {(busy || run?.status === "running") && <p className="working-status" role="status">Checking your question against the document library…</p>}
        {run && !busy && run.status !== "running" && <p className="turn-status" role="status">{run.status === "awaiting_clarification" ? "Waiting for your reply" : run.status === "failed" ? "Question needs a retry" : run.status === "cancelled" ? "Question cancelled" : "Answer complete"} · Active {duration(run.active_ms)}{run.wait_ms > 0 ? ` · Human wait ${duration(run.wait_ms)}` : ""}</p>}
      </ChatLayout>
    </section>
    <SourcePreview source={source} onClose={() => setSource(null)} />
  </main>;
}
