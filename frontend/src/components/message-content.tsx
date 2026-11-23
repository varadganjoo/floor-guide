"use client";
import { Citation } from "@astryxdesign/core/Citation";
import { Button } from "@astryxdesign/core/Button";
import { type Message, type Reference } from "@/lib/api";
export function MessageContent({ message, onSource }: { message: Message; onSource: (reference: Reference) => void }) {
  const sources = message.references ?? [];
  return <>
    <p className="message-copy">{message.content.split(/(\[\d+\])/g).map((part, index) => {
      const match = /^\[(\d+)\]$/.exec(part);
      const reference = match ? sources.find(item => item.number === Number(match[1])) : undefined;
      return reference ? <button type="button" className="citation-button" key={index} onClick={() => onSource(reference)} aria-label={`Open source ${reference.number}: ${reference.title}`}><Citation number={reference.number} variant="number" source={{ title: reference.title }} /></button> : part;
    })}</p>
    {sources.length > 0 && <section className="source-links" aria-label="Supporting sources">{sources.map(reference => <Button key={reference.number} variant="ghost" size="sm" label={`[${reference.number}] ${reference.title}`} onClick={() => onSource(reference)} />)}</section>}
  </>;
}
