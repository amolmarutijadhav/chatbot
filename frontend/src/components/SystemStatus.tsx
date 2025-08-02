import React from 'react';
import { Activity, Server, Users, MessageSquare, Clock } from 'lucide-react';
import { HealthResponse, StatsResponse } from '../types/api.ts';

interface SystemStatusProps {
  health: HealthResponse | null;
  stats: StatsResponse | null;
  loading: boolean;
}

const SystemStatus: React.FC<SystemStatusProps> = ({ health, stats, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
        <div className={`flex items-center space-x-2 px-2 py-1 rounded-full text-xs font-medium ${
          health?.status === 'healthy' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          <Activity className="w-3 h-3" />
          <span>{health?.status || 'Unknown'}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Server className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">
              {health?.components?.api_server?.endpoints || 0}
            </p>
            <p className="text-xs text-gray-500">Endpoints</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Users className="w-4 h-4 text-green-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">
              {stats?.active_sessions || 0}
            </p>
            <p className="text-xs text-gray-500">Active Sessions</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <MessageSquare className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">
              {stats?.total_messages || 0}
            </p>
            <p className="text-xs text-gray-500">Total Messages</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="p-2 bg-orange-100 rounded-lg">
            <Clock className="w-4 h-4 text-orange-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">
              {health?.uptime_seconds ? Math.round(health.uptime_seconds / 60) : 0}
            </p>
            <p className="text-xs text-gray-500">Uptime (min)</p>
          </div>
        </div>
      </div>

      {health?.memory_usage_mb && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Memory Usage</span>
            <span>{health.memory_usage_mb.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(health.memory_usage_mb, 100)}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemStatus; 