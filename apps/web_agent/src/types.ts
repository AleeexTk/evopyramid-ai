export type AgentRole = 'user' | 'assistant' | 'system';

export interface AgentMessage {
  id: string;
  role: AgentRole;
  content: string;
  timestamp: string;
  status?: 'streaming' | 'complete' | 'error';
}

export interface WebAgentTabState {
  id: string;
  title: string;
  url: string;
  isMonitoring: boolean;
  messages: AgentMessage[];
  pageContent?: string;
  error?: string;
}
