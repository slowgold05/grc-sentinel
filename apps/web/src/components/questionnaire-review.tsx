"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useEffect, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Answer = { id: string; question: string; answer: string; statement_ids: string[]; review_status: string };

export function QuestionnaireReview() {
  const { getToken, userId } = useAuth();
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    const response = await fetch(`${apiUrl}/api/questionnaire-answers`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Could not load questionnaire answers");
    setAnswers(await response.json());
  }, [getToken]);

  useEffect(() => { if (userId) load().catch((reason: Error) => setError(reason.message)); }, [load, userId]);

  async function review(id: string, status: "approved" | "rejected", edited_answer?: string) {
    const token = await getToken();
    if (!token) return;
    const response = await fetch(`${apiUrl}/api/questionnaire-answers/${id}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ status, edited_answer: edited_answer || null }),
    });
    if (!response.ok) return setError("Answer was already reviewed or unavailable");
    await load();
  }

  return <div className="mt-8 space-y-4">{error && <p role="alert" className="text-rose-300">{error}</p>}{answers.map((item) => <article key={item.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><p className="text-sm font-semibold text-cyan-300">{item.question}</p><textarea id={`answer-${item.id}`} defaultValue={item.answer} disabled={item.review_status !== "pending"} maxLength={10000} className="mt-4 min-h-28 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm" /><p className="mt-2 text-xs text-slate-500">Grounded in {item.statement_ids.length} approved statement(s) · {item.review_status}</p>{item.review_status === "pending" && <div className="mt-4 flex gap-3"><button onClick={() => review(item.id, "approved", (document.getElementById(`answer-${item.id}`) as HTMLTextAreaElement).value)} className="rounded-lg bg-emerald-300 px-4 py-2 font-semibold text-slate-950">Approve</button><button onClick={() => review(item.id, "rejected")} className="px-4 py-2 text-rose-300">Reject</button></div>}</article>)}{!answers.length && !error && <p className="text-slate-400">No answers are waiting for review.</p>}</div>;
}
