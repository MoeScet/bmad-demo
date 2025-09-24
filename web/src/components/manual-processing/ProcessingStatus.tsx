import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, Loader2, FileText, AlertTriangle } from 'lucide-react';

interface ProcessingJob {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  filename: string;
  progress_percent: number;
  message: string;
  created_at: string;
  completed_at?: string;
  error_details?: string;
}

interface ProcessingStatusProps {
  jobId?: string;
  refreshInterval?: number; // in milliseconds
  onJobComplete?: (job: ProcessingJob) => void;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  jobId,
  refreshInterval = 5000,
  onJobComplete
}) => {
  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJobStatus = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/status/${id}`, {
        headers: {
          'x-correlation-id': crypto.randomUUID(),
        },
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error?.message || 'Failed to fetch job status');
      }

      const jobData = result.data as ProcessingJob;
      setJob(jobData);

      // Call completion callback if job is done and wasn't done before
      if (jobData.status === 'completed' && onJobComplete) {
        onJobComplete(jobData);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      console.error('Status fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!jobId) return;

    // Initial fetch
    fetchJobStatus(jobId);

    // Set up polling for active jobs
    const pollInterval = setInterval(() => {
      if (job && (job.status === 'queued' || job.status === 'processing')) {
        fetchJobStatus(jobId);
      }
    }, refreshInterval);

    return () => clearInterval(pollInterval);
  }, [jobId, refreshInterval, job?.status]);

  const getStatusIcon = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'queued':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'processing':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'queued':
        return 'bg-yellow-100 border-yellow-200';
      case 'processing':
        return 'bg-blue-100 border-blue-200';
      case 'completed':
        return 'bg-green-100 border-green-200';
      case 'failed':
        return 'bg-red-100 border-red-200';
      default:
        return 'bg-gray-100 border-gray-200';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getProgressBarColor = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'processing':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  if (!jobId) {
    return (
      <div className="text-center text-gray-500 py-8">
        <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p>No job selected</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-200 bg-red-50 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-medium text-red-900">Error Loading Status</h3>
            <p className="text-red-700 mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={() => jobId && fetchJobStatus(jobId)}
          className="mt-4 px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!job && isLoading) {
    return (
      <div className="text-center py-8">
        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
        <p className="text-gray-600">Loading job status...</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center text-gray-500 py-8">
        <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p>Job not found</p>
      </div>
    );
  }

  return (
    <div className={`border rounded-lg p-6 ${getStatusColor(job.status)}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {getStatusIcon(job.status)}
          <div>
            <h3 className="text-lg font-medium text-gray-900 capitalize">
              {job.status.replace('_', ' ')} Processing
            </h3>
            <p className="text-sm text-gray-600">{job.filename}</p>
          </div>
        </div>
        <div className="text-right text-xs text-gray-500">
          <p>Job ID: {job.job_id.slice(-8)}</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{job.progress_percent.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(job.status)}`}
            style={{ width: `${job.progress_percent}%` }}
          />
        </div>
      </div>

      {/* Status Message */}
      <div className="mb-4">
        <p className="text-sm text-gray-700">{job.message}</p>
      </div>

      {/* Error Details */}
      {job.status === 'failed' && job.error_details && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <h4 className="text-sm font-medium text-red-900 mb-2">Error Details:</h4>
          <p className="text-sm text-red-700 font-mono">{job.error_details}</p>
        </div>
      )}

      {/* Timestamps */}
      <div className="grid grid-cols-2 gap-4 text-xs text-gray-500 border-t pt-4">
        <div>
          <p className="font-medium">Started:</p>
          <p>{formatDate(job.created_at)}</p>
        </div>
        {job.completed_at && (
          <div>
            <p className="font-medium">Completed:</p>
            <p>{formatDate(job.completed_at)}</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-2 mt-4">
        {(job.status === 'queued' || job.status === 'processing') && (
          <button
            onClick={() => fetchJobStatus(job.job_id)}
            disabled={isLoading}
            className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        )}

        {job.status === 'completed' && (
          <button
            onClick={() => {
              // TODO: Navigate to content view or results
              console.log('View results for job:', job.job_id);
            }}
            className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
          >
            View Results
          </button>
        )}

        {job.status === 'failed' && (
          <button
            onClick={() => {
              // TODO: Implement retry functionality
              console.log('Retry job:', job.job_id);
            }}
            className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
};