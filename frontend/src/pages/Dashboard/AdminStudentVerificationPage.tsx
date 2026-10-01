import { useCallback, useEffect, useState } from "react";
import { Download, RefreshCw, ShieldCheck } from "lucide-react";

import { getApiErrorMessage } from "@/lib/api";
import {
  approveStudentApplication,
  getStudentApplicationProof,
  listStudentApplications,
  rejectStudentApplication,
  type StudentApplication,
  type StudentApplicationList,
} from "@/services/studentVerification";

const FILTERS = ["pending", "approved", "rejected", "withdrawn", "all"];

function formatBytes(bytes?: number): string {
  if (!bytes) return "Unavailable";
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function AdminStudentVerificationPage() {
  const [filter, setFilter] = useState("pending");
  const [offset, setOffset] = useState(0);
  const [result, setResult] = useState<StudentApplicationList | null>(null);
  const [selected, setSelected] = useState<StudentApplication | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadApplications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await listStudentApplications(filter, offset);
      setResult(next);
      setSelected((current) =>
        next.applications.find((application) => application.id === current?.id) ??
        next.applications[0] ??
        null
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "Unable to load student verification applications."
        )
      );
    } finally {
      setLoading(false);
    }
  }, [filter, offset]);

  useEffect(() => {
    void loadApplications();
  }, [loadApplications]);

  async function handleApprove() {
    if (!selected || !window.confirm("Approve this application and grant one year of Student Pro?")) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const approved = await approveStudentApplication(selected.id);
      setSelected(approved);
      setMessage("Application approved. Student Pro access is active for 365 days.");
      await loadApplications();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Unable to approve this application."));
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    if (!selected || !rejectionReason.trim()) {
      setError("Enter a rejection reason before rejecting the application.");
      return;
    }
    if (!window.confirm("Reject this student verification application?")) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const rejected = await rejectStudentApplication(
        selected.id,
        rejectionReason.trim()
      );
      setSelected(rejected);
      setRejectionReason("");
      setMessage("Application rejected and the student was notified.");
      await loadApplications();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Unable to reject this application."));
    } finally {
      setBusy(false);
    }
  }

  async function handleProofDownload() {
    if (!selected) return;
    setError(null);
    try {
      const proof = await getStudentApplicationProof(selected.id);
      const objectUrl = URL.createObjectURL(proof);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = "student-proof";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Unable to retrieve this proof document."));
    }
  }

  function updateFilter(nextFilter: string) {
    setOffset(0);
    setFilter(nextFilter);
  }

  const canMoveBack = offset > 0;
  const canMoveForward = result !== null && offset + result.limit < result.total;

  return (
    <div className="mx-auto min-w-0 max-w-7xl space-y-6 text-foreground transition-colors duration-200">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <ShieldCheck className="mt-1 size-7 shrink-0 text-primary" />
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
              Student Verification Review
            </h1>
            <p className="mt-2 text-muted-foreground">
              Review enrollment evidence before granting Student Pro access.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void loadApplications()}
          disabled={loading}
          className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground transition-colors duration-200 hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw className="size-4" />
          Refresh
        </button>
      </header>

      {error && <p role="alert" className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-destructive transition-colors duration-200">{error}</p>}
      {message && <p role="status" className="rounded-xl border border-border bg-card p-4 text-foreground transition-colors duration-200">{message}</p>}

      <div className="flex flex-wrap gap-2" aria-label="Filter student applications">
        {FILTERS.map((item) => (
          <button
            key={item}
            type="button"
            aria-pressed={filter === item}
            onClick={() => updateFilter(item)}
            className={`rounded-full px-4 py-2 text-sm font-medium capitalize transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ${
              filter === item
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-accent hover:text-accent-foreground"
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="grid min-w-0 gap-5 lg:grid-cols-[minmax(16rem,0.8fr)_minmax(0,1.5fr)]">
        <section className="min-w-0 overflow-hidden rounded-2xl border border-border bg-card">
          <div className="border-b border-border px-4 py-3 text-sm text-muted-foreground">
            {result?.total ?? 0} application{result?.total === 1 ? "" : "s"}
          </div>
          {loading ? (
            <p role="status" className="p-5 text-sm text-muted-foreground">Loading applications...</p>
          ) : result?.applications.length ? (
            <ul className="divide-y divide-border">
              {result.applications.map((application) => (
                <li key={application.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setSelected(application);
                      setRejectionReason("");
                    }}
                    className={`w-full min-w-0 p-4 text-left transition-colors duration-200 hover:bg-secondary/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary ${
                      selected?.id === application.id ? "bg-secondary/60" : ""
                    }`}
                  >
                    <span className="block truncate font-semibold text-foreground">{application.applicant_name}</span>
                    <span className="mt-1 block truncate text-sm text-muted-foreground">{application.user_email}</span>
                    <span className="mt-2 block text-xs capitalize text-muted-foreground">
                      {application.status} · {new Date(application.created_at).toLocaleDateString()}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="p-5 text-sm text-muted-foreground">No applications in this view.</p>
          )}
          <div className="flex items-center justify-between border-t border-border p-3">
            <button
              type="button"
              disabled={!canMoveBack || loading}
              onClick={() => setOffset((current) => Math.max(0, current - 25))}
              className="rounded-md px-3 py-2 text-sm text-foreground transition-colors duration-200 hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={!canMoveForward || loading}
              onClick={() => setOffset((current) => current + 25)}
              className="rounded-md px-3 py-2 text-sm text-foreground transition-colors duration-200 hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </section>

        <section className="min-w-0 space-y-5 rounded-2xl border border-border bg-card p-4 sm:p-6">
          {selected ? (
            <>
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border pb-4">
                <div className="min-w-0">
                  <h2 className="break-words text-xl font-semibold text-foreground">{selected.applicant_name}</h2>
                  <p className="mt-1 break-all text-sm text-muted-foreground">{selected.user_email}</p>
                </div>
                <span className="rounded-full bg-secondary px-3 py-1 text-sm capitalize text-secondary-foreground">{selected.status}</span>
              </div>

              <dl className="grid min-w-0 grid-cols-1 gap-4 text-sm sm:grid-cols-2">
                <div className="min-w-0"><dt className="text-muted-foreground">Institution</dt><dd className="mt-1 break-words font-medium text-foreground">{selected.institution_name}</dd></div>
                <div className="min-w-0"><dt className="text-muted-foreground">Enrollment number</dt><dd className="mt-1 break-words font-medium text-foreground">{selected.enrollment_number}</dd></div>
                <div className="min-w-0"><dt className="text-muted-foreground">Program</dt><dd className="mt-1 break-words font-medium text-foreground">{selected.course_or_program}</dd></div>
                <div className="min-w-0"><dt className="text-muted-foreground">Academic year / graduation</dt><dd className="mt-1 break-words font-medium text-foreground">{selected.academic_year} / {selected.graduation_year}</dd></div>
                <div className="min-w-0"><dt className="text-muted-foreground">Institution email</dt><dd className="mt-1 break-all font-medium text-foreground">{selected.institution_email || "Not provided"}</dd></div>
                <div className="min-w-0"><dt className="text-muted-foreground">Submitted</dt><dd className="mt-1 font-medium text-foreground">{new Date(selected.created_at).toLocaleString()}</dd></div>
                <div className="min-w-0 sm:col-span-2"><dt className="text-muted-foreground">Additional information</dt><dd className="mt-1 whitespace-pre-wrap break-words font-medium text-foreground">{selected.additional_information || "None"}</dd></div>
              </dl>

              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-secondary/60 p-4">
                <div className="min-w-0">
                  <p className="break-words text-sm font-medium text-foreground">
                    {selected.proof_original_filename || "Proof document"}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {selected.proof_content_type || "Unknown type"} · {formatBytes(selected.proof_size)}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={!selected.proof_available}
                  onClick={() => void handleProofDownload()}
                  className="inline-flex min-h-10 shrink-0 items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground transition-colors duration-200 hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Download className="size-4" />
                  {selected.proof_available ? "Download proof" : "Proof expired"}
                </button>
              </div>

              {selected.status === "pending" ? (
                <div className="space-y-4 border-t border-border pt-4">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void handleApprove()}
                    className="w-full rounded-lg bg-primary px-4 py-3 font-semibold text-primary-foreground transition-colors duration-200 hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
                  >
                    {busy ? "Saving..." : "Approve · grant 365 days Pro"}
                  </button>
                  <label className="block space-y-2 text-sm font-medium text-foreground">
                    Rejection reason
                    <textarea
                      required
                      maxLength={2000}
                      rows={3}
                      value={rejectionReason}
                      onChange={(event) => setRejectionReason(event.target.value)}
                      className="w-full resize-y rounded-lg border border-input bg-background px-3 py-2.5 text-foreground placeholder:text-muted-foreground transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                      placeholder="Explain what is missing or why the proof is not sufficient."
                    />
                  </label>
                  <button
                    type="button"
                    disabled={busy || !rejectionReason.trim()}
                    onClick={() => void handleReject()}
                    className="rounded-lg border border-destructive/50 px-4 py-3 font-semibold text-destructive transition-colors duration-200 hover:bg-destructive/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Reject application
                  </button>
                </div>
              ) : selected.rejection_reason ? (
                <div className="border-t border-border pt-4">
                  <p className="text-sm font-medium text-muted-foreground">Rejection reason</p>
                  <p className="mt-1 whitespace-pre-wrap break-words text-sm text-foreground">{selected.rejection_reason}</p>
                </div>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Select an application to review.</p>
          )}
        </section>
      </div>
    </div>
  );
}
