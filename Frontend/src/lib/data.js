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
    id: 'g1', name: 'Trust & Autonomy', color: '1', count: 47, open: true,
    desc: 'How teachers negotiate epistemic authority with AI outputs.',
    children: [
      { id: 'c11', name: 'Verification habits',     color: '1', count: 14, desc: 'Cross-checking AI outputs against curriculum, peers, or first principles.' },
      { id: 'c12', name: 'Loss of agency',          color: '1', count: 11, desc: 'Feeling that decisions are nudged or pre-made by the tool.' },
      { id: 'c13', name: 'Selective deference',     color: '1', count: 12, desc: 'Trusting AI for low-stakes tasks; reserving judgment elsewhere.' },
      { id: 'c14', name: 'Calibration over time',   color: '1', count: 10, desc: 'Trust shifting as familiarity with the tool grows.' }
    ]
  },
  {
    id: 'g2', name: 'Pedagogical Impact', color: '3', count: 38, open: true,
    desc: 'Effects on teaching practice and student learning experience.',
    children: [
      { id: 'c21', name: 'Personalization',         color: '3', count: 13, desc: 'Tailoring materials to individual learner needs.' },
      { id: 'c22', name: 'Skill atrophy concerns',  color: '3', count: 9,  desc: 'Worry that students offload core skills before mastery.' },
      { id: 'c23', name: 'Scaffolding rewrites',    color: '3', count: 8,  desc: 'Restructuring lesson scaffolds because of AI-aided drafts.' },
      { id: 'c24', name: 'Feedback richness',       color: '3', count: 8,  desc: 'Faster, more granular formative feedback loops.' }
    ]
  },
  {
    id: 'g3', name: 'Adoption Barriers', color: '2', count: 29, open: true,
    desc: 'Friction preventing routine classroom use.',
    children: [
      { id: 'c31', name: 'Time costs',              color: '2', count: 12, desc: 'Setup, prompt-crafting, and review consume planning time.' },
      { id: 'c32', name: 'Institutional policy',    color: '2', count: 10, desc: 'Unclear or restrictive district/school guidance.' },
      { id: 'c33', name: 'Tool fragmentation',      color: '2', count: 7,  desc: 'Juggling multiple overlapping products and logins.' }
    ]
  },
  {
    id: 'g4', name: 'Student Reactions', color: '4', count: 24, open: false,
    desc: 'How students respond, behaviorally and affectively.',
    children: [
      { id: 'c41', name: 'Curiosity surge',         color: '4', count: 9 },
      { id: 'c42', name: 'Anxiety / dependence',    color: '4', count: 8 },
      { id: 'c43', name: 'Peer disclosure norms',   color: '4', count: 7 }
    ]
  },
  {
    id: 'g5', name: 'Identity & Craft', color: '5', count: 18, open: false,
    desc: 'Teaching as a vocation; what the tool changes about that self-image.',
    children: [
      { id: 'c51', name: 'Pride in handcraft',      color: '5', count: 7 },
      { id: 'c52', name: 'Role drift',              color: '5', count: 6 },
      { id: 'c53', name: 'Generational framing',    color: '5', count: 5 }
    ]
  },
  {
    id: 'g6', name: 'Equity Concerns', color: '6', count: 13, open: false,
    desc: 'Unevenness in access, benefit, and harm across student populations.',
    children: [
      { id: 'c61', name: 'Access gaps',             color: '6', count: 5 },
      { id: 'c62', name: 'Linguistic bias',         color: '6', count: 4 },
      { id: 'c63', name: 'Hidden curriculum',       color: '6', count: 4 }
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
