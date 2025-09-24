import React, { useState, useEffect } from 'react';
import { Search, Filter, Trash2, RefreshCw, Eye, Download, AlertCircle } from 'lucide-react';

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
  similarity_score?: number;
}

interface ContentFilters {
  manufacturer?: string;
  content_type?: string;
  search_query?: string;
  min_confidence?: number;
}

interface ContentManagementProps {
  onContentSelected?: (content: ManualContentItem) => void;
}

export const ContentManagement: React.FC<ContentManagementProps> = ({
  onContentSelected
}) => {
  const [content, setContent] = useState<ManualContentItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ContentFilters>({});
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [isSearchMode, setIsSearchMode] = useState(false);

  // Load content list
  const loadContent = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (filters.manufacturer) params.append('manufacturer', filters.manufacturer);
      if (filters.content_type) params.append('content_type', filters.content_type);
      params.append('limit', '50');

      const response = await fetch(`/api/v1/content?${params}`, {
        headers: {
          'x-correlation-id': crypto.randomUUID(),
        },
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error?.message || 'Failed to load content');
      }

      setContent(result.data.content);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      console.error('Content loading error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Search content
  const searchContent = async () => {
    if (!filters.search_query?.trim()) {
      loadContent();
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const searchRequest = {
        query: filters.search_query,
        manufacturer: filters.manufacturer,
        content_type: filters.content_type,
        min_confidence: filters.min_confidence || 0,
        max_results: 50
      };

      const response = await fetch('/api/v1/content/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-correlation-id': crypto.randomUUID(),
        },
        body: JSON.stringify(searchRequest),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error?.message || 'Search failed');
      }

      setContent(result.data.results);
      setIsSearchMode(true);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search error occurred');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete content items
  const deleteContent = async (contentId: string) => {
    if (!confirm('Are you sure you want to delete this content item?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/content/${contentId}`, {
        method: 'DELETE',
        headers: {
          'x-correlation-id': crypto.randomUUID(),
        },
      });

      if (response.ok) {
        setContent(prev => prev.filter(item => item.id !== contentId));
        setSelectedItems(prev => {
          const updated = new Set(prev);
          updated.delete(contentId);
          return updated;
        });
      } else {
        const result = await response.json();
        throw new Error(result.error?.message || 'Delete failed');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete error occurred');
      console.error('Delete error:', err);
    }
  };

  // Reprocess content item
  const reprocessContent = async (contentId: string) => {
    try {
      const response = await fetch(`/api/v1/content/${contentId}/reprocess`, {
        method: 'POST',
        headers: {
          'x-correlation-id': crypto.randomUUID(),
        },
      });

      if (response.ok) {
        // Refresh content list
        loadContent();
      } else {
        const result = await response.json();
        throw new Error(result.error?.message || 'Reprocess failed');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reprocess error occurred');
      console.error('Reprocess error:', err);
    }
  };

  // Load content on component mount and filter changes
  useEffect(() => {
    if (!isSearchMode) {
      loadContent();
    }
  }, [filters.manufacturer, filters.content_type]);

  const handleSearch = () => {
    if (filters.search_query?.trim()) {
      searchContent();
    } else {
      setIsSearchMode(false);
      loadContent();
    }
  };

  const handleItemSelection = (contentId: string) => {
    setSelectedItems(prev => {
      const updated = new Set(prev);
      if (updated.has(contentId)) {
        updated.delete(contentId);
      } else {
        updated.add(contentId);
      }
      return updated;
    });
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Filters and Search */}
      <div className="bg-white p-6 rounded-lg border">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Content
            </label>
            <div className="relative">
              <input
                type="text"
                value={filters.search_query || ''}
                onChange={(e) => setFilters(prev => ({ ...prev, search_query: e.target.value }))}
                placeholder="Search manual content..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Manufacturer
            </label>
            <select
              value={filters.manufacturer || ''}
              onChange={(e) => setFilters(prev => ({ ...prev, manufacturer: e.target.value || undefined }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Manufacturers</option>
              <option value="Whirlpool">Whirlpool</option>
              <option value="LG">LG</option>
              <option value="Samsung">Samsung</option>
              <option value="GE">GE</option>
              <option value="Maytag">Maytag</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content Type
            </label>
            <select
              value={filters.content_type || ''}
              onChange={(e) => setFilters(prev => ({ ...prev, content_type: e.target.value || undefined }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="troubleshooting">Troubleshooting</option>
              <option value="maintenance">Maintenance</option>
              <option value="safety">Safety</option>
              <option value="warranty">Warranty</option>
            </select>
          </div>

          <div className="flex items-end space-x-2">
            <button
              onClick={handleSearch}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center space-x-2"
            >
              <Search className="w-4 h-4" />
              <span>Search</span>
            </button>
            <button
              onClick={() => {
                setFilters({});
                setIsSearchMode(false);
                loadContent();
              }}
              className="px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}

      {/* Content List */}
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">
              Manual Content ({content.length} items)
              {isSearchMode && filters.search_query && (
                <span className="text-sm text-gray-500 ml-2">
                  - Search results for "{filters.search_query}"
                </span>
              )}
            </h2>
            <div className="flex space-x-2">
              {selectedItems.size > 0 && (
                <button
                  onClick={() => {
                    // Bulk delete functionality
                    selectedItems.forEach(id => deleteContent(id));
                  }}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors flex items-center space-x-1"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Delete Selected ({selectedItems.size})</span>
                </button>
              )}
              <button
                onClick={() => isSearchMode ? handleSearch() : loadContent()}
                disabled={isLoading}
                className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 disabled:opacity-50 transition-colors flex items-center space-x-1"
              >
                <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
            <p className="text-gray-600">{isSearchMode ? 'Searching...' : 'Loading content...'}</p>
          </div>
        ) : content.length === 0 ? (
          <div className="text-center py-12">
            <Filter className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">
              {isSearchMode ? 'No content found matching your search' : 'No content available'}
            </p>
          </div>
        ) : (
          <div className="divide-y">
            {content.map((item) => (
              <div
                key={item.id}
                className={`p-4 hover:bg-gray-50 ${selectedItems.has(item.id) ? 'bg-blue-50' : ''}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <input
                      type="checkbox"
                      checked={selectedItems.has(item.id)}
                      onChange={() => handleItemSelection(item.id)}
                      className="mt-1 h-4 w-4 text-blue-600 rounded border-gray-300"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-sm font-medium text-gray-900">
                          {item.section_title}
                        </h3>
                        <span className="text-xs text-gray-500">
                          {item.manufacturer} - {item.model_series}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceColor(item.confidence_score)}`}>
                          {(item.confidence_score * 100).toFixed(0)}%
                        </span>
                        {item.similarity_score && (
                          <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                            {(item.similarity_score * 100).toFixed(0)}% match
                          </span>
                        )}
                      </div>

                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {item.content.substring(0, 200)}...
                      </p>

                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>Type: {item.content_type}</span>
                        <span>Source: {item.source_manual}</span>
                        <span>Page: {item.page_reference}</span>
                        <span>Created: {formatDate(item.created_at)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => onContentSelected && onContentSelected(item)}
                      className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => reprocessContent(item.id)}
                      className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                      title="Reprocess"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteContent(item.id)}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};