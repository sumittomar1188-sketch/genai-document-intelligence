import type { DocumentSource } from "../types/api";

export interface FormattedAnswer {
  text: string;
  sources: DocumentSource[];
}

const markdownEscapes = new Set([
  "\\", "`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!", "|", ">",
]);

function unescapeMarkdown(text: string): string {
  return text.replace(/\\([^\n])/g, (match, character: string) =>
    markdownEscapes.has(character) ? character : match,
  );
}

function normalizeFilename(filename: string): string {
  return filename.trim().replace(/^[`'"“”]|[`'"“”]$/g, "").normalize("NFC").toLowerCase();
}

export function formatAnswer(answer: string, availableSources: DocumentSource[]): FormattedAnswer {
  const sourceByFilename = new Map<string, DocumentSource[]>();
  for (const source of availableSources) {
    const key = normalizeFilename(source.source);
    sourceByFilename.set(key, [...(sourceByFilename.get(key) ?? []), source]);
  }

  const displayedSources = new Map<string, DocumentSource>();
  const citationPattern = /【([^】]+)】|\[([^\]]+)\]/g;
  const citationText = unescapeMarkdown(answer);

  const text = citationText
    .replace(citationPattern, (wholeMatch, bracketCitation: string | undefined, squareCitation: string | undefined) => {
      const citation = (bracketCitation ?? squareCitation ?? "").trim();
      const pageMatch = citation.match(/^(.*?)\s*,?\s*page\s+(\d+)\s*$/i);
      const filename = (pageMatch?.[1] ?? citation).trim();

      // Strip source-style PDF/TXT citations from the answer, even if the API
      // did not return a matching source. Unrecognized Markdown brackets stay intact.
      if (!/\.(pdf|txt)$/i.test(filename)) return wholeMatch;

      const citedPage = pageMatch ? Number(pageMatch[2]) : null;
      const matches = sourceByFilename.get(normalizeFilename(filename)) ?? [];
      const availablePages = new Set(
        matches
          .map((source) => source.page)
          .filter((page): page is number => typeof page === "number"),
      );
      const onlyAvailablePage = availablePages.values().next().value as number | undefined;
      const matchingSources = citedPage !== null
        ? matches.filter((source) => source.page === citedPage)
        : availablePages.size === 1
          ? matches.filter((source) => source.page === onlyAvailablePage)
          : matches;

      for (const source of matchingSources) {
        const displayedPage = citedPage ?? (availablePages.size === 1 ? source.page : null);
        const key = `${normalizeFilename(source.source)}:${displayedPage ?? "none"}`;
        if (!displayedSources.has(key)) {
          displayedSources.set(key, { source: source.source, page: displayedPage });
        }
      }

      return " ";
    })
    .replace(/[ \t]+([,.;!?])/g, "$1")
    .trim();

  return { text, sources: [...displayedSources.values()] };
}
