// Manual Processing Components
export { ManualUpload } from './ManualUpload';
export { ProcessingStatus } from './ProcessingStatus';
export { ContentManagement } from './ContentManagement';
export { ManualProcessingDashboard } from './ManualProcessingDashboard';

// Types
export interface ManualContentItem {
  id: string;
  manufacturer: string;
  model_series: string;
  section_title: string;
  content: string;
  content_type: string;
  confidence_score: number;
  source_manual: string;
  page_reference: string;
  created_at: string;
  similarity_score?: number;
}

export interface ProcessingJob {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  filename: string;
  progress_percent: number;
  message: string;
  created_at: string;
  completed_at?: string;
  error_details?: string;
}

export interface UploadResponse {
  job_id: string;
  filename: string;
  file_size: number;
  status: string;
  message: string;
}