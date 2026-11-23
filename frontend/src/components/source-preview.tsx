"use client";
import { Dialog, DialogHeader } from "@astryxdesign/core/Dialog";
import { type Reference } from "@/lib/api";
export function SourcePreview({ source, onClose }: { source: Reference | null; onClose: () => void }) {
  return <Dialog isOpen={source !== null} onOpenChange={open => { if (!open) onClose(); }} purpose="info" width={620} aria-label="Source evidence">
    {source && <>
      <DialogHeader title={`Source ${source.number}`} subtitle={source.title} onOpenChange={open => { if (!open) onClose(); }} />
      <section className="source-detail">
        <p className="demo-notice">EXAMPLE ONLY — NOT RELEASED FOR OPERATION</p>
        <h2>{source.heading || "Document excerpt"}</h2>
        <blockquote>{source.quote}</blockquote>
        <p className="muted">Evidence snapshot saved with this answer. Application-validated reference.</p>
        <dl className="source-meta"><dt>Document</dt><dd>{source.document_id}</dd><dt>Section</dt><dd>{source.source_id}</dd><dt>Version hash</dt><dd>{source.document_hash}</dd></dl>
      </section>
    </>}
  </Dialog>;
}
