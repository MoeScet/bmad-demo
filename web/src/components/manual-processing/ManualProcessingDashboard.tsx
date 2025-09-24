import React, { useState } from 'react';
import { FileText, Upload, Search, BarChart3 } from 'lucide-react';
import { ManualUpload } from './ManualUpload';
import { ProcessingStatus } from './ProcessingStatus';
import { ContentManagement } from './ContentManagement';

interface ManualContentItem {
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
}

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

type TabType = 'upload' | 'status' | 'content' | 'analytics';

export const ManualProcessingDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('upload');
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [selectedContent, setSelectedContent] = useState<ManualContentItem | null>(null);

  const tabs = [
    { id: 'upload' as TabType, name: 'Upload Manual', icon: Upload },
    { id: 'status' as TabType, name: 'Processing Status', icon: FileText },
    { id: 'content' as TabType, name: 'Content Management', icon: Search },
    { id: 'analytics' as TabType, name: 'Quality Analytics', icon: BarChart3 },
  ];

  const handleUploadComplete = (response: any) => {
    setCurrentJobId(response.job_id);
    setActiveTab('status');
  };

  const handleJobComplete = (job: ProcessingJob) => {
    if (job.status === 'completed') {
      // Optionally switch to content tab to view results
      setTimeout(() => {
        setActiveTab('content');
      }, 2000);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'upload':
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Upload Manual for Processing
              </h2>
              <p className="text-gray-600">
                Upload PDF manuals to extract content and generate vector embeddings for semantic search.
              </p>
            </div>
            <ManualUpload
              onUploadComplete={handleUploadComplete}
              maxFileSize={50}
            />
          </div>
        );

      case 'status':
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Processing Status
              </h2>
              <p className="text-gray-600">
                Monitor the progress of manual processing jobs and view completion status.
              </p>
            </div>
            <ProcessingStatus
              jobId={currentJobId || undefined}
              onJobComplete={handleJobComplete}
            />
            {!currentJobId && (
              <div className="text-center text-gray-500 py-8">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>No active processing job</p>
                <p className="text-sm">Upload a manual to start processing</p>
              </div>
            )}
          </div>
        );

      case 'content':
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Content Management
              </h2>
              <p className="text-gray-600">
                Browse, search, and manage processed manual content with quality metrics.
              </p>
            </div>
            <ContentManagement onContentSelected={setSelectedContent} />
          </div>
        );

      case 'analytics':
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Quality Analytics
              </h2>
              <p className="text-gray-600">
                View quality metrics, processing statistics, and content analysis reports.
              </p>
            </div>
            <QualityAnalytics />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Manual Processing Dashboard
                </h1>
                <p className="mt-2 text-gray-600">
                  Process PDF manuals and manage content for semantic search
                </p>
              </div>
              <div className="flex items-center space-x-4">
                {currentJobId && (
                  <div className="text-sm">
                    <span className="text-gray-500">Active Job:</span>
                    <span className="ml-1 font-mono text-blue-600">
                      {currentJobId.slice(-8)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${isActive
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderTabContent()}
      </div>

      {/* Content Detail Modal */}
      {selectedContent && (
        <ContentDetailModal
          content={selectedContent}
          onClose={() => setSelectedContent(null)}
        />
      )}
    </div>
  );
};

// Placeholder Quality Analytics Component
const QualityAnalytics: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null);

  React.useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/v1/quality/report');
        const result = await response.json();
        if (response.ok) {
          setAnalytics(result.data);
        }
      } catch (error) {
        console.error('Failed to load analytics:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-8 h-8 animate-pulse mx-auto mb-4 text-blue-500" />
        <p className="text-gray-600">Loading quality analytics...</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-medium mb-4">Content Overview</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Total Items:</span>
            <span className="font-medium">{analytics?.total_content_items || 0}</span>
          </div>
          <div className="flex justify-between">
            <span>Average Quality:</span>
            <span className="font-medium">
              {(analytics?.quality_metrics?.average_quality_score * 100 || 0).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-medium mb-4">Content Types</h3>
        <div className="space-y-2">
          {analytics?.content_type_distribution && Object.entries(analytics.content_type_distribution).map(([type, count]: [string, any]) => (
            <div key={type} className="flex justify-between">
              <span className="capitalize">{type}:</span>
              <span className="font-medium">{count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-medium mb-4">Manufacturers</h3>
        <div className="space-y-2">
          {analytics?.manufacturer_distribution && Object.entries(analytics.manufacturer_distribution).slice(0, 5).map(([mfg, count]: [string, any]) => (
            <div key={mfg} className="flex justify-between">
              <span>{mfg}:</span>
              <span className="font-medium">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Content Detail Modal
interface ContentDetailModalProps {
  content: ManualContentItem;
  onClose: () => void;
}

const ContentDetailModal: React.FC<ContentDetailModalProps> = ({ content, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-bold text-gray-900">{content.section_title}</h2>
              <p className="text-gray-600">{content.manufacturer} - {content.model_series}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl font-semibold"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 120px)' }}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Content Type:</span>
                <span className="ml-2 capitalize">{content.content_type}</span>
              </div>
              <div>
                <span className="font-medium">Confidence Score:</span>
                <span className="ml-2">{(content.confidence_score * 100).toFixed(1)}%</span>
              </div>
              <div>
                <span className="font-medium">Source Manual:</span>
                <span className="ml-2">{content.source_manual}</span>
              </div>
              <div>
                <span className="font-medium">Page Reference:</span>
                <span className="ml-2">{content.page_reference}</span>
              </div>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Content:</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <pre className="whitespace-pre-wrap text-sm text-gray-700">
                  {content.content}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};