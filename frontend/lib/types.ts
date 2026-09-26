export type Mode = "collaborate" | "compete";
export type Status = "lobby" | "playing" | "ended";
export type Grade = "A+" | "A" | "B" | "C" | "D" | "F";
export type ReefBand = "thriving" | "stressed" | "bleaching" | "dead";
export type ReefEventType = "turtle" | "bloom" | "fish" | "murk" | "sludge";

export type Beat = {
  ask: string;
  fixtureTitle: string;
  fixture: string;
  targetTokens: number;
};

export type Challenge = {
  id: string;
  title: string;
  brief: string;
  hint: string;
  turnCount: number;
  targetTokens: number;
  beats: Beat[];
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type Thread = {
  ownerId: string;
  step: number;
  done: boolean;
  turnLimit: number;
  messages: ChatMessage[];
};

export type Piece = {
  role: string;
  title: string;
  body: string;
};

export type Player = {
  id: string;
  name: string;
  language: string;
  builds: string;
  cares: string;
  piece: Piece | null;
  squadId: string | null;
  score: number;
  lastGrade: Grade | null;
  connected: boolean;
  joinedAt: number;
};

export type Squad = {
  id: string;
  name: string;
  playerIds: string[];
  memberNames: string[];
  shared: string;
  distinct: string;
  creature: string;
  closing: string;
  icebreaker: string;
  prompt: string;
  promptAuthorId: string | null;
  promptUpdatedAt: number;
  score: number;
  lastGrade: Grade | null;
};

export type Submission = {
  id: string;
  playerId: string;
  squadId: string | null;
  actor: string;
  prompt: string;
  tokenCount: number;
  targetTokens: number;
  lookupTokens: number;
  carbonGrams: number;
  excessKgAtScale: number;
  grade: Grade;
  score: number;
  reefDelta: number;
  reefHealth: number;
  aiResponse: string;
  simulated: boolean;
  summary: string;
  eventType: ReefEventType;
  createdAt: number;
  turnIndex: number;
  turnCount: number;
  followUp: boolean;
  reasonable: boolean;
  verdictReason: string;
  judgedByModel: boolean;
  serverSideTools: number;
};

export type ReefEvent = {
  id: string;
  type: ReefEventType;
  title: string;
  subtitle: string;
  grade: Grade;
  actor: string;
  imageUrl: string | null;
  createdAt: number;
};

export type GameSession = {
  code: string;
  mode: Mode;
  status: Status;
  playerMin: number;
  playerMax: number;
  challenge: Challenge | null;
  reefHealth: number;
  reefBand: ReefBand;
  players: Player[];
  squads: Squad[];
  submissions: Submission[];
  events: ReefEvent[];
  threads: Thread[];
  turnsAllowed: number;
  createdAt: number;
  revision: number;
};

export type Health = {
  ok: boolean;
  grokConfigured: boolean;
  chatModel: string;
  imageModel: string;
  imagesEnabled: boolean;
  grokRoles: string[];
  lanIp: string;
  formula: {
    energyKwhPer1kTokens: number;
    carbonGramsPerKwh: number;
    scaleQueries: number;
    webLookupTokens: number;
    tokenizer: string;
    note: string;
  };
};

export type Identity = {
  playerId: string;
  playerToken: string;
  name: string;
};
