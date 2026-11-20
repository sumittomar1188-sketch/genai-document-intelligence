import { useRef, useState, type ChangeEvent, type DragEvent, type FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import { askQuestion, uploadDocument } from "./services/api";
import type { AskResponse, UploadResponse } from "./types/api";
import { formatAnswer } from "./utils/formatAnswer";

interface ConversationTurn extends AskResponse {
  id: number;
}

const UNSUPPORTED_FILE_MESSAGE =
  "Unsupported file format. Please upload a PDF or TXT file containing text.";

function hasSupportedFormat(file: File): boolean {
  const extension = file.name.split(".").pop()?.toLowerCase();
  const mimeType = file.type.trim().toLowerCase().split(";")[0];

  if (extension !== "pdf" && extension !== "txt") return false;

  const expectedMimeType = extension === "pdf" ? "application/pdf" : "text/plain";
  return !mimeType || mimeType === expectedMimeType || mimeType === "application/octet-stream";
}

export default function App() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedDocument, setUploadedDocument] = useState<UploadResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  function chooseFile(file: File | null) {
    if (!file) return;

    if (!hasSupportedFormat(file)) {
      setSelectedFile(null);
      setUploadedDocument(null);
      setUploadError(UNSUPPORTED_FILE_MESSAGE);
      return;
    }
    if (file.size === 0) {
      setUploadError("This file is empty. Choose a document with content.");
      return;
    }

    setSelectedFile(file);
    setUploadedDocument(null);
    setUploadError(null);
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    chooseFile(event.target.files?.[0] ?? null);
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    chooseFile(event.dataTransfer.files?.[0] ?? null);
  }

  async function handleUpload() {
    if (!selectedFile || isUploading) return;

    setIsUploading(true);
    setUploadError(null);
    try {
      const result = await uploadDocument(selectedFile);
      setUploadedDocument(result);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "The document could not be uploaded.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!uploadedDocument || !cleanQuestion || isAsking) return;

    setQuestion("");
    setAskError(null);
    setIsAsking(true);
    try {
      const response = await askQuestion(cleanQuestion);
      setTurns((previous) => [...previous, { ...response, id: Date.now() }]);
    } catch (error) {
      setQuestion(cleanQuestion);
      setAskError(error instanceof Error ? error.message : "The question could not be sent.");
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="page-content">
        <header className="page-heading">
          <h1>Document Q&amp;A Assistant</h1>
          <p>Upload your document and ask anything.</p>
        </header>

        <section className="section upload-section" aria-labelledby="upload-heading">
          <h2 id="upload-heading">Upload Document</h2>
          <div
            className={`drop-area${isDragging ? " is-dragging" : ""}`}
            onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              className="visually-hidden"
              type="file"
              accept=".pdf,.txt,application/pdf,text/plain"
              onChange={handleFileChange}
              aria-label="Choose a PDF or TXT document"
            />
            <p>Drop a PDF or TXT file here, or</p>
            <button className="button button-secondary" type="button" onClick={() => fileInputRef.current?.click()}>
              Choose file
            </button>
          </div>

          {selectedFile && (
            <div className="file-status" aria-live="polite">
              <span className="file-name" title={selectedFile.name}>{selectedFile.name}</span>
              <span className={uploadedDocument ? "status-success" : "status-muted"}>
                {uploadedDocument
                  ? "Document Uploaded"
                  : isUploading ? "Uploading…" : "Ready to upload"}
              </span>
            </div>
          )}

          <button
            className="button button-primary upload-button"
            type="button"
            onClick={() => void handleUpload()}
            disabled={!selectedFile || Boolean(uploadedDocument) || isUploading}
          >
            {isUploading ? "Uploading…" : uploadedDocument ? "Document Uploaded" : "Upload Document"}
          </button>
          {uploadError && <p className="error-message" role="alert">{uploadError}</p>}
        </section>

        <section className="section ask-section" aria-labelledby="ask-heading">
          <h2 id="ask-heading">Ask a Question</h2>
          <form className="question-form" onSubmit={(event) => void handleAsk(event)}>
            <label className="visually-hidden" htmlFor="question-input">Your question</label>
            <input
              id="question-input"
              type="text"
              value={question}
              onChange={(event) => { setQuestion(event.target.value); setAskError(null); }}
              placeholder={uploadedDocument ? "Type your question…" : "Upload a document to ask a question"}
              disabled={!uploadedDocument || isAsking}
            />
            <button className="button button-primary" type="submit" disabled={!uploadedDocument || !question.trim() || isAsking}>
              {isAsking ? "Thinking…" : "Ask AI"}
            </button>
          </form>
          {askError && <p className="error-message" role="alert">{askError}</p>}

          <div className="responses" aria-live="polite" aria-label="Questions and answers">
            {turns.map((turn) => {
              const formattedAnswer = formatAnswer(turn.answer, turn.sources);

              return (
                <article className="response" key={turn.id}>
                  <h3>{turn.question}</h3>
                  <div className="answer-text answer-markdown">
                    <ReactMarkdown components={{ img: () => null }}>
                      {formattedAnswer.text}
                    </ReactMarkdown>
                  </div>
                  {formattedAnswer.sources.length > 0 && (
                    <div className="sources">
                      {formattedAnswer.sources.map((source, index) => (
                        <p className="source" key={`${source.source}-${source.page ?? "none"}-${index}`}>
                          <span>{source.source}</span>
                          {typeof source.page === "number" && <span>Page {source.page}</span>}
                        </p>
                      ))}
                    </div>
                  )}
                </article>
              );
            })}
            {isAsking && <p className="loading-status" role="status">Waiting for an answer…</p>}
          </div>
        </section>
      </div>
    </main>
  );
}
