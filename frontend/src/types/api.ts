export interface UploadResponse {
  status: string;
  message: string;
  original_filename: string;
  saved_filename: string;
  chunks_processed: number;
  chunks_stored: number;
}

export interface DocumentSource {
  source: string;
  page: number | null;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: DocumentSource[];
}
