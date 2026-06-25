// QualScope demo data. In a real app, fetched from FastAPI; here used as seed
// state and as the shape the API contracts target.

export const PROJECT = {
  name: 'QSTAT Frontend',
  current: 'Test Interview',
  files: [
    { id: 'f1',  name: 'Interview 01 — Default.mp3',     type: 'mp3', status: 'ok',    meta: '42:18 · transcribed' },
    { id: 'f2',  name: 'Interview 02 — Default2.mp3',        type: 'mp3', status: 'proc',  meta: 'transcribing… 64%', progress: 64 },
    { id: 'f3',  name: 'Interview 03 — Default3.mp3',     type: 'mp3', status: 'queue', meta: 'in queue' },
    { id: 'f4', name: 'Doc1.pdf',     type: 'pdf', status: 'ok',    meta: '4 pp · 12 chunks' },
    { id: 'f5', name: 'Doc1.docx',     type: 'doc', status: 'ok',    meta: '12 pp · 38 chunks' },
    { id: 'f6', name: 'Spreadsheet.xlsx',              type: 'xls', status: 'ok',    meta: '3 sheets · 9 chunks' },
    { id: 'f7', name: 'Doc3.pdf',     type: 'pdf', status: 'ok',    meta: '28 pp · 94 chunks' },
  ]
};

export const CODEBOOK = [
  {
    id: 'g1', name: 'Category1', color: '1', count: 47, open: true,
    desc: 'Description 1',
    children: [
      { id: 'c11', name: 'Code 1',     color: '1', count: 14, desc: 'Code Description 1' },
      { id: 'c12', name: 'Code 2',          color: '1', count: 11, desc: 'Code Description 2' },
      { id: 'c13', name: 'Code 3',     color: '1', count: 12, desc: 'Code Description 3' },
      { id: 'c14', name: 'Code 4',   color: '1', count: 10, desc: 'Code Description 4' }
    ]
  },
  {
    id: 'g2', name: 'Category 2', color: '3', count: 38, open: true,
    desc: 'Description 2',
    children: [
      { id: 'c21', name: 'Code 1',         color: '3', count: 13, desc: 'Code Description 1' },
      { id: 'c22', name: 'Code 2',  color: '3', count: 9,  desc: 'Code Description 2' },
      { id: 'c23', name: 'Code 3',    color: '3', count: 8,  desc: 'Code Description 3' },
    ]
  }
];


// Citation registry — both transcript-anchored and document-chunk citations.
// In production these come back from the LLM call (with chunks supplied by
// the RAG pipeline) and from the coding pipeline.
export const CITES = {
  1: { kind: 't', codeId: 'c14', turnTs: '00:00:24' },
  2: { kind: 't', codeId: 'c11', turnTs: '00:00:54' },
  3: { kind: 't', codeId: 'c31', turnTs: '00:00:54' },
  4: { kind: 't', codeId: 'c23', turnTs: '00:01:46' },
  5: { kind: 't', codeId: 'c12', turnTs: '00:01:46' },
  6: { kind: 'd', file: 'Prior coding — phase 1.pdf', fileId: 'f13', page: 12, score: 0.847,
       preview: 'Phase 1 coders converged on a pattern they called "autonomy-by-relocation": the locus of judgment moves from drafting to curation, but is not described as a loss.' },
  7: { kind: 'd', file: 'Interview protocol v3.docx', fileId: 'f11', page: 4, score: 0.812,
       preview: 'Probe sequence 3.b — when participants mention verification habits, follow up with: "Has the kind of thing you check changed over time?"' },
  8: { kind: 't', codeId: 'c32', turnTs: '00:03:30' },
  9: { kind: 't', codeId: 'c33', turnTs: '00:03:30' }
};

export const MODELS = [
  { id: 'qwen',   name: 'qwen3-14b-AWQ',     kind: 'local', desc: 'local · vLLM' },
  { id: 'sonnet', name: 'claude-sonnet-4.5', kind: 'cloud', desc: 'external · Anthropic' }

];
