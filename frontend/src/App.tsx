import React, { useState } from 'react';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'inbox' | 'metrics' | 'agents'>('inbox');

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-blue-400">📧 AI Email Agent</h1>
          <p className="text-sm text-gray-400 mt-1">Pharmaceutical Distribution System</p>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-4">
            <button
              onClick={() => setActiveTab('inbox')}
              className={`px-4 py-3 text-sm font-medium ${
                activeTab === 'inbox'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              📨 Inbox
            </button>
            <button
              onClick={() => setActiveTab('metrics')}
              className={`px-4 py-3 text-sm font-medium ${
                activeTab === 'metrics'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              📊 Metrics
            </button>
            <button
              onClick={() => setActiveTab('agents')}
              className={`px-4 py-3 text-sm font-medium ${
                activeTab === 'agents'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              🤖 Agents
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'inbox' && <InboxTab />}
        {activeTab === 'metrics' && <MetricsTab />}
        {activeTab === 'agents' && <AgentsTab />}
      </main>
    </div>
  );
};

// Inbox Tab Component
const InboxTab: React.FC = () => {
  const emails = [
    { id: '1', from: 'customer@brazil.com', subject: 'Re: Bulk Order - Paracetamol 500mg', priority: 'high', status: 'pending', time: '10:32 AM' },
    { id: '2', from: 'pharma@china.cn', subject: '询价：阿莫西林胶囊 250mg', priority: 'medium', status: 'processing', time: '09:15 AM' },
    { id: '3', from: 'info@medical.com', subject: 'Question about shipping terms', priority: 'low', status: 'completed', time: 'Yesterday' },
  ];

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      <div className="px-4 py-3 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Inbox</h2>
      </div>
      <div>
        {emails.map((email) => (
          <div key={email.id} className="px-4 py-3 border-b border-gray-700 hover:bg-gray-750 flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${
              email.status === 'pending' ? 'bg-green-500' :
              email.status === 'processing' ? 'bg-yellow-500' : 'bg-gray-500'
            }`} />
            <div className="flex-1">
              <h3 className="font-medium">{email.subject}</h3>
              <p className="text-sm text-gray-400">{email.from}</p>
            </div>
            <span className={`text-xs px-2 py-1 rounded ${
              email.priority === 'high' ? 'bg-red-500/20 text-red-400' :
              email.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>
              {email.priority.toUpperCase()}
            </span>
            <span className="text-sm text-gray-500">{email.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Metrics Tab Component
const MetricsTab: React.FC = () => {
  const metrics = [
    { name: 'Emails Today', value: '247', trend: '+12%', trendUp: true },
    { name: 'Avg Processing Time', value: '1.2s', trend: '-8%', trendUp: true },
    { name: 'Avg Cost per Email', value: '$0.018', trend: '-5%', trendUp: true },
    { name: 'Classification Accuracy', value: '98.3%', trend: '+0.3%', trendUp: true },
    { name: 'Sonnet Routing Rate', value: '82%', trend: 'On Target', trendUp: true },
    { name: 'Prompt Versions', value: '43', trend: '+3 this week', trendUp: true },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {metrics.map((metric) => (
        <div key={metric.name} className="bg-gray-800 rounded-lg border border-gray-700 p-4">
          <div className="text-3xl font-bold text-blue-400">{metric.value}</div>
          <div className="text-sm text-gray-400 mt-1">{metric.name}</div>
          <div className={`text-xs mt-2 ${metric.trendUp ? 'text-green-400' : 'text-red-400'}`}>
            {metric.trend}
          </div>
        </div>
      ))}
    </div>
  );
};

// Agents Tab Component
const AgentsTab: React.FC = () => {
  const agents = [
    { name: 'CEO Agent', status: 'Running', budget: 0.45, budgetMax: 2.00 },
    { name: 'Price Agent', status: 'Completed', budget: 0.10, budgetMax: 0.10 },
    { name: 'Compliance Agent', status: 'Completed', budget: 0.15, budgetMax: 0.15 },
    { name: 'Logistics Agent', status: 'Running', budget: 0.07, budgetMax: 0.12 },
    { name: 'Reply Agent', status: 'Pending', budget: 0, budgetMax: 0.08 },
  ];

  return (
    <div className="space-y-4">
      {agents.map((agent) => (
        <div key={agent.name} className="bg-gray-800 rounded-lg border border-orange-500/30 p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="font-medium text-orange-400">{agent.name}</span>
            <span className={`text-xs px-2 py-1 rounded ${
              agent.status === 'Running' ? 'bg-yellow-500/20 text-yellow-400' :
              agent.status === 'Completed' ? 'bg-green-500/20 text-green-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>
              {agent.status}
            </span>
          </div>
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Budget</span>
            <span>${agent.budget.toFixed(2)} / ${agent.budgetMax.toFixed(2)}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-orange-500 to-orange-400 h-2 rounded-full"
              style={{ width: `${(agent.budget / agent.budgetMax) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

export default App;
