export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  streaming?: boolean;
  toolStatus?: string | null;
}

export interface AgentAlert {
  id: string;
  alert_type: string;
  severity: "info" | "warning" | "critical";
  message: string;
  cycle_id: string;
  farm_id: string;
  created_at: string | null;
}

export interface AgentTask {
  id: string;
  task_type: "reminder" | "follow_up" | "check" | "action";
  title: string;
  description: string;
  farm_id: string;
  pond_id: string;
  cycle_id: string;
  due_at: string | null;
  is_completed: boolean;
  created_at: string | null;
}

export interface AgentMemory {
  id: string;
  memory_type: "fact" | "preference" | "event" | "advice" | "note";
  content: string;
  tags: string[];
  farm_id: string;
  pond_id: string;
  cycle_id: string;
  source: string;
  confidence: number;
  is_verified: boolean;
  created_at: string | null;
}

export interface AgentMemoryEntity {
  id: string;
  entity_type: string;
  canonical_name: string;
  farm_id: string;
  metadata: Record<string, unknown>;
}

export interface AgentMemoryRelation {
  id: string;
  source_entity_id: string;
  relation_type: string;
  target_entity_id: string;
  confidence: number;
  source_type: string;
}

export interface AgentMemoryObservation {
  id: string;
  entity_id: string;
  observation_type: string;
  content: string;
  farm_id: string;
  pond_id: string;
  cycle_id: string;
  confidence: number;
  source_type: string;
  is_verified: boolean;
  created_at: string | null;
}

export interface AgentMemoryGraph {
  entities: AgentMemoryEntity[];
  relations: AgentMemoryRelation[];
  observations: AgentMemoryObservation[];
}

export interface AgentPageContext {
  route: string;
  page_type: string;
  farm_id: string;
  pond_id: string;
  cycle_id: string;
  filters: Record<string, string>;
}

export interface ChatPayload {
  session_id: string;
  response: string;
  farm_id: string;
  pond_id: string;
  cycle_id: string;
  page_context?: AgentPageContext;
}

export interface StreamEvent {
  type: "text" | "tool_start" | "tool_done" | "done" | "error";
  delta?: string;
  name?: string;
  session_id?: string;
  farm_id?: string;
  pond_id?: string;
  cycle_id?: string;
  message?: string;
}
